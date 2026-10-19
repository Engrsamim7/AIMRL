"""On-time cooperative PS-IQL/Double-DQN and packet-boundary continuations.

New research layer; the timed-network physics and previous source fingerprints
are unchanged. Actors use public topology and own/delivered belief summaries.
Shared finite-horizon team reward is fleet on-time delivery; bandwidth has no
reward term. Report rejection authority is bounded separately from routing.
"""
import copy
from dataclasses import replace
import hashlib
import heapq
import math
import numpy as np
import torch
from torch import nn
from timed_network import TimedNetwork,path,uniform

FEATURES=['wait','cost','nominal_tail','expected_tail','closure_probability','own_known','own_blocked','own_age','own_confidence','peer_known','peer_blocked','peer_age','peer_confidence','own_peer_conflict','remaining_deadline','elapsed_fraction','local_flow','encounters','reverse_edge','planner_action','remaining_time_ratio','peer_previous_blocked','peer_changes','state_nominal_remaining','state_expected_remaining','state_closure_summary']
GATE_FEATURES=['blocked','confidence','age','own_known','own_blocked','own_age','peer_known','peer_blocked','peer_age','own_conflict','peer_conflict','actor_action_change','before_margin','after_margin','edge_at_node','edge_reachable','distance_to_edge','public_demand','public_detour','remaining_deadline','travelling','pending','old_peer_confidence','posterior_change']


class EdgeQ(nn.Module):
    def __init__(self):
        super().__init__();self.body=nn.Sequential(nn.Linear(len(FEATURES),64),nn.Tanh(),nn.Linear(64,32),nn.Tanh(),nn.Linear(32,1))
        self.state_value=nn.Sequential(nn.Linear(6,32),nn.Tanh(),nn.Linear(32,1))
        for head in [self.body,self.state_value]:nn.init.zeros_(head[-1].weight);nn.init.zeros_(head[-1].bias)
    def forward(self,x):
        # Transparent planning prior, refined by learned return residuals.
        state=x[...,[14,15,17,23,24,25]]
        return self.state_value(state).squeeze(-1)+x[...,23]-.1*x[...,3]+.05*torch.tanh(self.body(x).squeeze(-1))


class Actor:
    def __init__(self,seed,training=False):
        torch.manual_seed(seed);self.net=EdgeQ();self.target=EdgeQ();self.target.load_state_dict(self.net.state_dict());self.training=training;self.epsilon=0.;self.replay=[];self.updates=0
        self.rng=np.random.default_rng(seed);self.opt=torch.optim.Adam(self.net.parameters(),lr=.0005) if training else None
    def __deepcopy__(self,memo):
        if self.training:raise RuntimeError('Counterfactual branches require a frozen actor')
        return self
    def values(self,x):
        with torch.no_grad():return self.net(torch.as_tensor(np.asarray(x),dtype=torch.float32)).numpy()
    def choose(self,x,seed,cid,index,explore=True):
        if explore and uniform(seed,891,cid,index)<self.epsilon:return min(int(uniform(seed,892,cid,index)*len(x)),len(x)-1)
        return int(np.argmax(self.values(x)))
    def learn(self,transitions,steps=12):
        self.replay.extend(transitions)
        if len(self.replay)>100000:self.replay=self.replay[-100000:]
        if len(self.replay)<128:return []
        losses=[]
        for _ in range(steps):
            batch=[self.replay[i] for i in self.rng.integers(len(self.replay),size=128)]
            x=torch.tensor(np.array([b[0] for b in batch]),dtype=torch.float32);r=torch.tensor([b[1] for b in batch],dtype=torch.float32)
            lengths=[len(b[2]) for b in batch];width=max(max(lengths),1);nxt=np.zeros((128,width,len(FEATURES)),np.float32);mask=np.zeros((128,width),bool)
            for i,b in enumerate(batch):
                if lengths[i]:nxt[i,:lengths[i]]=b[2];mask[i,:lengths[i]]=True
            z=torch.tensor(nxt);valid=torch.tensor(mask)
            with torch.no_grad():
                online=self.net(z).masked_fill(~valid,-1e9);selected=online.argmax(1);future=self.target(z).gather(1,selected[:,None]).squeeze(1);lower=torch.tensor([b[4] if len(b)>4 else 0. for b in batch],dtype=torch.float32);future=torch.maximum(lower,torch.minimum(lower+1.,future));future[~valid.any(1)]=0.;target=r+future
            prediction=self.net(x);mc=torch.tensor([b[3] if len(b)>3 else b[1] for b in batch],dtype=torch.float32)
            loss=nn.functional.smooth_l1_loss(prediction,target)+.5*nn.functional.smooth_l1_loss(prediction,mc);self.opt.zero_grad();loss.backward();nn.utils.clip_grad_norm_(self.net.parameters(),5.);self.opt.step();losses.append(float(loss.detach()))
            self.updates+=1
            if self.updates%100==0:self.target.load_state_dict(self.net.state_dict())
        return losses
    def state(self):return dict(features=FEATURES,network={k:v.detach().numpy().tolist() for k,v in self.net.state_dict().items()},updates=self.updates)
    @classmethod
    def load(cls,state):
        assert state['features']==FEATURES;a=cls(0);a.net.load_state_dict({k:torch.tensor(v,dtype=torch.float32) for k,v in state['network'].items()});a.target.load_state_dict(a.net.state_dict());return a


class DeliveryNetwork(TimedNetwork):
    def __init__(self,*args,actor=None,receiver='ALL',gate=None,dropout=0.,**kwargs):
        super().__init__(*args,**kwargs);self.actor=actor;self.receiver=receiver;self.gate=gate;self.dropout=dropout
        self.history={u.cid:[] for u in self.units};self.peer_history={u.cid:{} for u in self.units};self.decision_index={u.cid:0 for u in self.units}
        self.rejections=0;self.gate_log=[];self.intervention=None;self.capture=None;self.branch_stop=False;self.initialized=False;self.finalized=False
    def offer(self,u,e,blocked,t_obs,confidence):
        # The base number is only a queue tie-break. Loss identity is semantic,
        # so unrelated earlier offers cannot change this observation's loss draw.
        before=self.packet_sequence;super().offer(u,e,blocked,t_obs,confidence)
        # Base start_radio may already have committed the packet. Mutate that
        # dict in place as well as pending packets before delivery can occur.
        opaque=hashlib.sha256(repr((self.seed,u.cid,int(e),float(t_obs).hex(),bool(blocked))).encode()).hexdigest()[:24]
        for p in self.radio+([self.active_packet] if self.active_packet is not None else []):
            if p['number']==before+1:p['id']=opaque
    def beliefs(self,u,own_only=False):
        merged=dict(u.own)
        if own_only or self.receiver=='NONE':return merged
        for e,r in u.peer.items():
            if e in merged and merged[e][1]>=r[1]:continue
            if self.receiver=='FIXED' and (not 0<=self.t-r[1]<=3.2 or r[2]<.6):continue
            merged[e]=r
        return merged
    def candidate_features(self,u,own_only=False,live=True):
        g=self.g;merged=self.beliefs(u,own_only);prior=self.model.prior(self.t/self.reference);at=self.distance(u.node)
        w=g.c.copy()+self.case.hub_service+prior*self.case.inspection*g.c
        probs=np.full(g.m,prior);banned=[]
        visible=set(self.observation_edges(u)) if live else set()
        for e in visible:w[e]+=g.c[e]*.2*self.flow[e]/max(g.q[e],1)
        for e,(blocked,ts,conf) in merged.items():
            if ts>self.t or not math.isfinite(at[int(g.src[e])]):continue
            future=float(at[int(g.src[e])]);p=self.model.probability(blocked,(self.t+future-ts)/self.scale,(self.t+future)/self.reference,conf)
            if e in u.own and ts==u.own[e][1] and conf>=1. and self.t==ts and future==0.:p=float(blocked)
            probs[e]=p;w[e]+=(p-prior)*self.case.inspection*g.c[e]
            if e in g.out[u.node] and e in u.own and u.own[e][0] and u.own[e][2]>=1 and self.t-u.own[e][1]<.5*self.scale:banned.append(e)
        reference=path(g,u.node,u.target,w,banned);planner=reference[0] if reference else None
        actions=[];features=[];remaining=(u.deadline-self.t)/self.reference
        for e in g.out[u.node]:
            if e in banned or (int(g.dst[e]) in g.targets and int(g.dst[e])!=u.target):continue
            tail=path(g,int(g.dst[e]),u.target,g.c)
            if tail is None:continue
            expected=path(g,int(g.dst[e]),u.target,w)
            own=u.own.get(e);peer=None if own_only else u.peer.get(e)
            if peer is not None and self.receiver=='FIXED' and (not 0<=self.t-peer[1]<=3.2 or peer[2]<.6):peer=None
            past={} if own_only or peer is None else self.peer_history[u.cid].get(e,{})
            f=[0.,g.c[e]/self.reference,sum(g.c[a] for a in tail)/self.reference,(w[e]+sum(w[a] for a in expected or []))/self.reference,probs[e],float(own is not None),float(own[0]) if own else 0.,min(8.,(self.t-own[1])/self.scale) if own else 8.,own[2] if own else 0.,float(peer is not None),float(peer[0]) if peer else 0.,min(8.,(self.t-peer[1])/self.scale) if peer else 8.,peer[2] if peer else 0.,float(own is not None and peer is not None and own[0]!=peer[0]),np.clip(remaining,-4,4),(self.t-u.depart)/self.reference,.2*self.flow[e]/max(g.q[e],1) if e in visible else 0.,min(u.encounters/10.,5.),float(bool(u.path) and int(g.dst[e])==int(g.src[u.path[-1]])),float(e==planner),(g.c[e]+sum(g.c[a] for a in tail))/max(u.deadline-self.t,self.scale*.1),float(past.get('previous_blocked',False)),min(past.get('changes',0)/5.,2.)]
            actions.append(int(e));features.append(np.clip(f,-10,10))
        # WAIT is a declared action and consumes actual half-edge-scale time.
        nominal=path(g,u.node,u.target,g.c);distance=sum(g.c[e] for e in nominal or [])
        wait=np.zeros(23);wait[0]=1.;wait[2]=distance/self.reference;wait[3]=(min(f[3] for f in features)+.5*self.scale/self.reference) if features else (distance+.5*self.scale)/self.reference;wait[4]=float(np.mean(probs[g.out[u.node]])) if g.out[u.node] else 0.;wait[14]=np.clip(remaining,-4,4);wait[15]=(self.t-u.depart)/self.reference;wait[17]=min(u.encounters/10.,5.);wait[19]=float(planner is None);wait[20]=distance/max(u.deadline-self.t,self.scale*.1)
        actions.append(None);features.append(np.clip(wait,-10,10))
        x=np.asarray(features,np.float32);shared=np.array([distance/self.reference,float(x[:,3].min()),float(np.mean(probs[g.out[u.node]])) if g.out[u.node] else 0.],np.float32)
        x=np.concatenate([x,np.tile(shared,(len(x),1))],axis=1)
        return actions,x,-distance/self.reference
    def choose(self,u,own_only=False):
        if self.actor is None:return super().choose(u,own_only)
        actions,x,phi=self.candidate_features(u,own_only)
        index=self.decision_index[u.cid];chosen=self.actor.choose(x,self.seed,u.cid,index,explore=not own_only)
        if not own_only:
            self.history[u.cid].append(dict(x=x,chosen=chosen,phi=phi,t=self.t));self.decision_index[u.cid]+=1
        # Shared diagnostics use current admitted peer beliefs, never truth.
        reports=[]
        for e,r in self.beliefs(u,own_only).items():
            if not own_only and e in u.peer and r[1]==u.peer[e][1] and math.isfinite(self.distance(u.node)[int(self.g.src[e])]):
                future=float(self.distance(u.node)[int(self.g.src[e])]);p=self.model.probability(r[0],(self.t+future-r[1])/self.scale,(self.t+future)/self.reference,r[2]);reports.append((e,p))
        return actions[chosen],reports,self.model.prior(self.t/self.reference)
    def probe(self,u):
        # Gate sees the receiver's own current state. In transit, use its known
        # destination as the next decision location; no future event lookup.
        probe=copy.copy(u)
        if probe.status=='travel':probe.node=int(self.g.dst[probe.current_edge])
        actions,x,_=self.candidate_features(probe,live=False)
        values=self.actor.values(x) if self.actor is not None else -.1*x[:,3]
        ordered=np.sort(values)
        return actions[int(values.argmax())],float(ordered[-1]-ordered[-2]) if len(ordered)>1 else 0.
    def packet_features(self,cid,p):
        u=self.units[cid];e=p['edge'];old=u.peer.get(e);own=u.own.get(e);before,margin0=self.probe(u)
        u.peer[e]=(p['blocked'],p['t_obs'],p['confidence'])
        try:after,margin1=self.probe(u)
        finally:
            if old is None:u.peer.pop(e)
            else:u.peer[e]=old
        loc=int(self.g.dst[u.current_edge]) if u.status=='travel' else u.node;distance=float(self.distance(loc)[int(self.g.src[e])]);reachable=math.isfinite(distance)
        phase=self.t/self.reference;newp=self.model.probability(p['blocked'],max(0.,self.t-p['t_obs'])/self.scale,phase,p['confidence']);oldp=self.model.probability(old[0],max(0.,self.t-old[1])/self.scale,phase,old[2]) if old else self.model.prior(phase)
        x=[float(p['blocked']),p['confidence'],min(8.,(self.t-p['t_obs'])/self.scale),float(own is not None),float(own[0]) if own else 0.,min(8.,(self.t-own[1])/self.scale) if own else 8.,float(old is not None),float(old[0]) if old else 0.,min(8.,(self.t-old[1])/self.scale) if old else 8.,float(own is not None and own[0]!=p['blocked']),float(old is not None and old[0]!=p['blocked']),float(before!=after),margin0,margin1,float(int(self.g.src[e])==loc),float(reachable),min(distance/self.reference,4.) if reachable else 4.,self.public_demand[e],self.public_detour[e]/self.reference,np.clip((u.deadline-self.t)/self.reference,-4,4),float(u.status=='travel'),float(u.status=='pending'),old[2] if old else 0.,newp-oldp]
        return np.asarray(x,np.float32)
    def eligible(self,cid,p):
        u=self.units[cid];old=u.peer.get(p['edge']);own=u.own.get(p['edge'])
        return u.status!='done' and 0<=self.t-p['t_obs'] and (old is None or p['t_obs']>old[1]) and (own is None or p['t_obs']>own[1])
    def admit(self,cid,p):
        u=self.units[cid];old=u.peer.get(p['edge'])
        if old is not None:
            h=self.peer_history[cid].setdefault(p['edge'],dict(changes=0,previous_blocked=old[0]));h['previous_blocked']=old[0];h['changes']+=int(old[0]!=p['blocked'])
        u.peer[p['edge']]=(p['blocked'],p['t_obs'],p['confidence'])
    def receive(self,cid,p):
        self.stats['delivered_packets']+=1
        if not self.eligible(cid,p):return
        key=(cid,p['id']);x=None
        if self.intervention is not None and key==self.intervention[0]:
            decision=self.intervention[1];self.intervention=None
        elif self.capture is not None:
            x=self.packet_features(cid,p)
            if self.capture(self,cid,p,x):self.branch_stop=True;return
            decision=True
        elif self.receiver=='NONE':decision=False
        elif self.dropout>0 and uniform(self.seed,893,cid,p['id'])<self.dropout:decision=False
        elif self.receiver=='FIXED':decision=self.t-p['t_obs']<=3.2 and p['confidence']>=.6
        elif self.receiver in ['KEEP','KEEP_ONE']:
            old=self.units[cid].peer.get(p['edge']);decision=not(old is not None and old[0] and not p['blocked'] and (self.receiver=='KEEP' or self.rejections<1))
        elif self.receiver=='LEARN' and self.rejections<1:
            x=self.packet_features(cid,p);decision=self.gate.admit(x) if x[11]>.5 else True
        else:decision=True
        if decision:self.admit(cid,p)
        else:self.rejections+=1
        if x is not None:self.gate_log.append(dict(t=self.t,cid=cid,id=p['id'],accepted=bool(decision),features=x.tolist()))
    def advance(self,initialize=True):
        if initialize and not self.initialized:
            for u in self.units:self.push(u.depart,'START',u.cid)
            self.initialized=True
        while self.events:
            self.t,_,kind,payload=heapq.heappop(self.events)
            if kind=='TX_END':self.finish_radio(payload);continue
            if kind=='MESSAGE':
                cid,p=payload;self.receive(cid,p)
                if self.branch_stop:return None
                continue
            u=self.units[payload]
            if kind=='START':self.request_service(u)
            elif kind=='SERVICE_END':u.service+=self.t-u.segment_start;self.release(u.node);self.decide(u)
            elif kind=='ARRIVE':
                e=u.current_edge;self.flow[e]-=1;u.travel+=self.t-u.entered;u.nominal+=self.g.c[e];u.path.append(int(e));u.node=int(self.g.dst[e]);u.current_edge=-1
                if u.node==u.target:u.finish=self.t;u.status='done'
                else:self.request_service(u)
            elif kind=='INSPECT_END':u.inspection+=self.t-u.segment_start;self.decide(u)
            elif kind=='HOLD_END':u.hold+=self.t-u.segment_start;self.decide(u)
            if all(x.status=='done' for x in self.units):break
        return self.finalize()
    def finalize(self):
        assert not self.finalized;self.finalized=True
        end=self.t if all(u.status=='done' for u in self.units) else self.horizon
        if self.active_packet is not None:self.stats['radio_airtime']+=max(0.,end-self.active_packet['tx_start'])
        rows=[]
        for u in self.units:
            clock=u.finish if u.status=='done' else self.horizon
            if u.status=='travel':u.travel+=clock-u.entered
            elif u.status=='service':u.service+=clock-u.segment_start
            elif u.status=='inspection':u.inspection+=clock-u.segment_start
            elif u.status=='hold':u.hold+=clock-u.segment_start
            elif u.status=='queue':u.wait+=clock-u.queue_start
            elapsed=clock-u.depart;assert abs(elapsed-u.travel-u.service-u.wait-u.inspection-u.hold)<1e-7
            rows.append(dict(convoy=u.cid,target=u.target,deadline=u.deadline,on_time=int(u.status=='done' and clock<=u.deadline),delivered=int(u.status=='done'),censored=int(u.status!='done'),elapsed=elapsed,nominal=u.nominal,travel=u.travel,service=u.service,wait=u.wait,inspection=u.inspection,hold=u.hold,encounters=u.encounters,path=repr(u.path)))
        result=dict(on_time=float(np.mean([r['on_time'] for r in rows])),delivery=float(np.mean([r['delivered'] for r in rows])),elapsed=float(np.mean([r['elapsed'] for r in rows])),rejections=self.rejections,**self.stats)
        return result,rows
    def run(self):return self.advance()
    def transitions(self,team_return):
        samples=[]
        for trajectory in self.history.values():
            for i,item in enumerate(trajectory):
                terminal=i==len(trajectory)-1;following=trajectory[i+1] if not terminal else None
                reward=(team_return if terminal else following['phi'])-item['phi']
                samples.append((item['x'][item['chosen']],float(reward),np.empty((0,len(FEATURES)),np.float32) if terminal else following['x'],float(team_return-item['phi']),0. if terminal else float(-following['phi'])))
        return samples


def paired_packet(snapshot,cid,p):
    """Snapshot is taken after pop, before admission, at an atomic event boundary.

    Both branches consume this same pending MESSAGE exactly once, then resume
    the saved heap. Future closures and keyed sensor/loss fields are identical.
    """
    outcomes=[]
    for admitted in [True,False]:
        branch=copy.deepcopy(snapshot);branch.capture=None;branch.branch_stop=False
        if admitted:branch.admit(cid,p)
        else:branch.rejections+=1
        result,rows=branch.advance(initialize=False)
        assert branch.seed==snapshot.seed and branch.schedule.digest==snapshot.schedule.digest and branch.schedule.intervals==snapshot.schedule.intervals
        outcomes.append((result,rows))
    return outcomes


class ReturnGate:
    """Actor-aware admit-minus-reject fleet return ensemble, safe default ALL.

    Tree dispersion and benefit frequency are heuristic uncertainty measures.
    One learned rejection is permitted per fleet episode. No bandwidth reward.
    """
    def __init__(self,beta=1.,margin=0.,risk_limit=.1,disabled=False):
        self.beta=beta;self.margin=margin;self.risk_limit=risk_limit;self.disabled=disabled;self.depth=7
    def fit(self,x,y,seed):
        from sklearn.ensemble import ExtraTreesRegressor
        x=np.asarray(x,np.float32);y=np.asarray(y,float)
        targets=np.stack([y,(y>0).astype(float),(y<0).astype(float)],axis=1)
        model=ExtraTreesRegressor(n_estimators=96,max_depth=self.depth,min_samples_leaf=4,max_features=.8,bootstrap=True,max_samples=.8,n_jobs=1,random_state=seed).fit(x,targets)
        n=max(t.tree_.node_count for t in model.estimators_);self.left=np.zeros((96,n),int);self.right=self.left.copy();self.feature=self.left.copy();self.threshold=np.zeros((96,n));self.values=np.zeros((96,n,3))
        for i,tree in enumerate(model.estimators_):
            tr=tree.tree_;k=tr.node_count;self.left[i,:k]=tr.children_left;self.right[i,:k]=tr.children_right;self.feature[i,:k]=np.maximum(tr.feature,0);self.threshold[i,:k]=tr.threshold;self.values[i,:k]=tr.value[:,:,0]
        for row,expected in zip(x[:10],model.predict(x[:10])):assert np.allclose(self.predict(row)[[0,2,3]],expected,atol=1e-12)
        return self
    def predict(self,x):
        x=np.asarray(x);nodes=np.zeros(len(self.left),int);rows=np.arange(len(nodes))
        for _ in range(self.depth+1):
            left=self.left[rows,nodes];active=left>=0
            if not active.any():break
            right=self.right[rows,nodes];choice=x[self.feature[rows,nodes]]<=self.threshold[rows,nodes]
            nodes=np.where(active,np.where(choice,left,right),nodes)
        values=self.values[rows,nodes];mean=values.mean(0)
        return np.array([mean[0],values[:,0].std(),mean[1],mean[2]])
    def admit(self,x):
        if self.disabled:return True
        mean,std,benefit,_=self.predict(x)
        return not(mean+self.beta*std < -self.margin and benefit<=self.risk_limit)
    def save(self,path):
        np.savez_compressed(path,features=np.array(GATE_FEATURES),left=self.left,right=self.right,feature=self.feature,threshold=self.threshold,values=self.values,depth=self.depth)
    @classmethod
    def load(cls,path,**kwargs):
        gate=cls(**kwargs)
        with np.load(path,allow_pickle=False) as z:
            assert z['features'].tolist()==GATE_FEATURES;gate.depth=int(z['depth'])
            for name in ['left','right','feature','threshold','values']:setattr(gate,name,z[name])
        return gate
