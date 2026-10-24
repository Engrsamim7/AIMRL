"""Atomic radio reservations and isolated pre-transmission interventions.

The reservation is made in the original inline event order, at zero elapsed
airtime. It is inspected only after the enclosing physical event completes.
Accepting it leaves the original heap/counters untouched. An alternative rolls
back that unsent reservation before changing queue service. No actor is trained.
"""
import copy
import heapq
import numpy as np
from delivery_learning import DeliveryNetwork

RADIO_FEATURES=['blocked','confidence','observation_age','queue_wait','score',
    'public_demand','public_detour','sender_is_scout','queue_size','ready_alternatives',
    'max_alternative_score','mean_alternative_age','service_time','elapsed_phase']


class PreTransmissionNetwork(DeliveryNetwork):
    def __init__(self,*args,batch_priority=False,**kwargs):
        super().__init__(*args,**kwargs)
        self.reservation=None;self.radio_capture=None;self.radio_paused=False
        self.reservation_count=0;self.radio_actions=[]
        self.batch_priority=batch_priority

    def priority(self,p):
        if self.method=='WARN_PRIORITY':return (-int(p['blocked']),-self.public_demand[p['edge']],p['number'])
        if self.method=='VALUE':return (-p['score'],p['number'])
        return (p['number'],)

    def start_radio(self,forced=None):
        if self.radio_busy:return
        ready=[p for p in self.radio if p.get('ready_at',-np.inf)<=self.t]
        if not ready:return
        packet=forced if forced is not None else min(ready,key=self.priority)
        assert any(p is packet for p in ready)
        self.radio.remove(packet);self.radio_busy=True;self.active_packet=packet
        packet['tx_start']=self.t;self.stats['tx_started']+=1
        before=self.sequence
        self.push(self.t+self.case.packet_time*self.scale,'TX_END',packet)
        self.reservation=dict(packet=packet,event_sequence=self.sequence if self.sequence>before else None)
        self.reservation_count+=1

    def radio_features(self):
        assert self.reservation is not None
        p=self.reservation['packet'];others=self.radio
        ready=[q for q in others if q.get('ready_at',-np.inf)<=self.t]
        return np.asarray([float(p['blocked']),p['confidence'],(self.t-p['t_obs'])/self.scale,
            (self.t-p['offered'])/self.scale,p['score'],self.public_demand[p['edge']],
            self.public_detour[p['edge']]/self.reference,float(p['sender']==0),len(others),len(ready),
            max([q['score'] for q in ready],default=0.),
            np.mean([(self.t-q['t_obs'])/self.scale for q in others]) if others else 0.,
            self.case.packet_time,self.t/self.reference],np.float64)

    def accept_reservation(self):
        assert self.reservation is not None
        self.reservation=None;self.radio_paused=False

    def _undo_reservation(self):
        assert self.reservation is not None
        p=self.reservation['packet'];sequence=self.reservation['event_sequence']
        assert p is self.active_packet and p['tx_start']==self.t
        if sequence is not None:
            found=[i for i,e in enumerate(self.events) if e[1]==sequence]
            assert len(found)==1
            event=self.events.pop(found[0]);assert event[2]=='TX_END' and event[3] is p
            heapq.heapify(self.events)
        self.stats['tx_started']-=1;self.radio_busy=False;self.active_packet=None
        self.reservation=None;self.radio_paused=False;p.pop('tx_start')
        return p

    def _requeue(self,p):
        if self.method in ['LATEST','WARN_PRIORITY','VALUE']:
            same=[q for q in self.radio if q['sender']==p['sender'] and q['edge']==p['edge']]
            if any(q['number']>p['number'] for q in same):
                self.stats['coalesced']+=1;return
            self.radio=[q for q in self.radio if q not in same]
            self.stats['coalesced']+=len(same)
        self.radio.append(p)

    def intervene(self,action):
        assert self.reservation is not None
        if action=='send':self.accept_reservation();return
        assert action in ['drop','defer','swap']
        alternatives=[p for p in self.radio if p.get('ready_at',-np.inf)<=self.t]
        if action=='swap':assert alternatives
        if action=='defer':assert self.case.packet_time>0
        selected=self._undo_reservation()
        if action=='defer':
            selected['ready_at']=self.t+self.case.packet_time*self.scale
            self._requeue(selected);self.push(selected['ready_at'],'RADIO_WAKE',None)
        elif action=='swap':self._requeue(selected)
        # Drop omits only this unsent packet. Defer affects this packet only:
        # existing/future ready packets can use the channel immediately.
        forced=min(alternatives,key=self.priority) if action=='swap' else None
        self.start_radio(forced=forced)
        self.radio_actions.append(dict(t=self.t,action=action,packet=selected['id']))
        # This is one intervention; the immediate replacement reservation is
        # factual. Its later successors follow the unchanged reference rule.
        if self.reservation is not None:self.accept_reservation()

    def boundary(self):
        if self.reservation is None:return False
        if self.batch_priority:
            assert self.radio_capture is None,'Batch reference and intervention capture are separate arms'
            selected=self.reservation['packet']
            ready=[p for p in self.radio if p.get('ready_at',-np.inf)<=self.t]
            best=min([selected]+ready,key=self.priority)
            if best is not selected:
                self._requeue(self._undo_reservation());self.start_radio(forced=best)
            self.accept_reservation();return False
        if self.radio_capture is not None and self.radio_capture(self):
            self.radio_paused=True;return True
        self.accept_reservation();return False

    def advance(self,initialize=True):
        assert not self.radio_paused,'Resolve the pending reservation before resuming'
        if initialize and not self.initialized:
            for u in self.units:self.push(u.depart,'START',u.cid)
            self.initialized=True
        previous_time=None;same_time=0
        while self.events:
            self.t,_,kind,payload=heapq.heappop(self.events)
            same_time=same_time+1 if self.t==previous_time else 1;previous_time=self.t
            if same_time>10000:raise RuntimeError(f'Nonprogressing radio/physical event cycle seed={self.seed}')
            if kind=='RADIO_WAKE':self.start_radio()
            elif kind=='TX_END':self.finish_radio(payload)
            elif kind=='MESSAGE':self.receive(*payload)
            else:
                u=self.units[payload]
                if kind=='START':self.request_service(u)
                elif kind=='SERVICE_END':u.service+=self.t-u.segment_start;self.release(u.node);self.decide(u)
                elif kind=='ARRIVE':
                    e=u.current_edge;self.flow[e]-=1;u.travel+=self.t-u.entered;u.nominal+=self.g.c[e];u.path.append(int(e));u.node=int(self.g.dst[e]);u.current_edge=-1
                    if u.node==u.target:u.finish=self.t;u.status='done'
                    else:self.request_service(u)
                elif kind=='INSPECT_END':u.inspection+=self.t-u.segment_start;self.decide(u)
                elif kind=='HOLD_END':u.hold+=self.t-u.segment_start;self.decide(u)
                else:raise ValueError(kind)
            # Finish the atomic physical event before exposing a zero-airtime
            # reservation. The send branch preserves original event ordering.
            if self.boundary():return None
            if kind not in ['RADIO_WAKE','TX_END','MESSAGE'] and all(u.status=='done' for u in self.units):break
        return self.finalize()


def paired_radio(snapshot,actions):
    assert snapshot.radio_paused and snapshot.reservation is not None
    outcomes={}
    for action in actions:
        branch=copy.deepcopy(snapshot);branch.radio_capture=None
        branch.intervene(action);result,rows=branch.advance(initialize=False)
        assert branch.schedule.digest==snapshot.schedule.digest and branch.schedule.intervals==snapshot.schedule.intervals
        assert branch.stats['radio_airtime']>=-1e-9 and branch.stats['transmitted']<=branch.stats['tx_started']
        outcomes[action]=(result,rows)
    return outcomes
