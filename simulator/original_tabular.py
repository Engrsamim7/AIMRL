"""Faithful submission definitions and explicit tabular-only repairs.

Preserved original files are never edited or imported through plot campaigns.
AST selection executes function/class bodies unchanged. Repairs are subclasses.
"""
import ast
import copy
import hashlib
import heapq
import importlib.util
import json
import random
import sys
import types
from collections import defaultdict
from dataclasses import dataclass,field
from pathlib import Path
import networkx as nx
import numpy as np
ROOT=Path(__file__).resolve().parents[1];SOURCE=ROOT/'revision/submission-code'
_CACHE=None
METRICS=['dr','cost','surv','blocked_enc','hub_wait','max_threat','corridor_sw','makespan','comm_eff','surv_var']


def definitions(path,names,namespace):
 tree=ast.parse(path.read_text());body=[n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in names]
 assert {n.name for n in body}==set(names)
 exec(compile(ast.Module(body=body,type_ignores=[]),str(path),'exec'),namespace)


def legacy():
 global _CACHE
 if _CACHE is not None:return _CACHE
 if 'ammarl_sim_core' not in sys.modules:
  spec=importlib.util.spec_from_file_location('ammarl_sim_core',SOURCE/'ammarl_sim_core.py');core=importlib.util.module_from_spec(spec);sys.modules[spec.name]=core;spec.loader.exec_module(core)
 else:core=sys.modules['ammarl_sim_core'];assert Path(core.__file__).resolve()==SOURCE/'ammarl_sim_core.py'
 common=dict(np=np,nx=nx,random=random,copy=copy,heapq=heapq,defaultdict=defaultdict,ContestedRoutingSim=core.ContestedRoutingSim,Convoy=core.Convoy,make_network=core.make_network,N_TRAIN=300,N_EVAL=20,METRICS=METRICS)
 marl=types.ModuleType('eval_marl');marl.__dict__.update(common);definitions(SOURCE/'eval_marl.py',{'QAgent','run_marl_episode'},marl.__dict__);sys.modules['eval_marl']=marl
 gated=dict(common,run_marl_episode=marl.run_marl_episode)
 definitions(SOURCE/'ammarl_gated_eval.py',{'GatedQAgent','NoGateQAgent','MAPPOAgent','run_gated_episode','run_classical','train_eval_gated','train_eval_iql','train_eval_nogate','train_eval_mappo'},gated)
 # CC2 is guarded at top level; import its definitions without campaigns anyway.
 cc=dict(common,SAFE_T=.05,DANGER_T=.75,BASE_T=.35,TAU_MSG=1.5,TAU_STALE=20.)
 for name in ['Event','CONVOY_DEPART','CONVOY_ARRIVE','RED_ATTACK','RED_REVEAL','MSG_DELIVER']:cc[name]=getattr(core,name)
 definitions(SOURCE/'cc2_scenario.py',{'make_cc2_map','CC2Sim','run_cc2_episode'},cc)
 _CACHE=types.SimpleNamespace(core=core,marl=marl,gated=gated,cc=cc)
 return _CACHE


def source_hashes():return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in SOURCE.iterdir() if p.is_file()}


def q_state(agents):
 return [dict(id=a.id,target=a.target,epsilon=a.epsilon,Q={str(s):{str(v):float(q) for v,q in acts.items()} for s,acts in a.Q.items()}) for a in agents]


@dataclass(order=True)
class OrderedEvent:
 time:float
 order:int
 etype:str=field(compare=False)
 payload:object=field(compare=False)


BaseSim=legacy().core.ContestedRoutingSim
BaseAgent=legacy().gated['GatedQAgent']


class FixedGateAgent(BaseAgent):
 """Same hub-indexed Q-learning and epsilon-greedy family; fixed rules only."""
 def __init__(self,*args,mode='FRC',peer_weight=8.,local_weight=2.,delta=.05,eta=.4,**kwargs):
  self.mode=mode;self.peer_weight=peer_weight;self.local_weight=local_weight;self.delta=delta;self.eta=eta;self.seen_ids=set();self.gate_log=[];self.edge_sources={}
  super().__init__(*args,**kwargs)
 def reset(self,depot=0):
  super().reset(depot);self.hazard_buf.clear();self.edge_sources={};self.seen_ids=set();self.gate_log=[]
 def receive(self,payload):
  edge=tuple(payload['edge']);old=self.hazard_buf.get(edge,(-1.,-np.inf,0.))
  if payload['timestamp']>old[1]:self.hazard_buf[edge]=(payload['threat_obs'],payload['timestamp'],payload['confidence'])
 def act(self,valid_actions,belief,now=0.,fork_node=None):
  valid=[v for v in valid_actions if v not in self.visited or v==self.target] or list(valid_actions)
  if not valid:return None
  scores={};fork=fork_node is not None
  for v in valid:
   edge=(self.pos,v);own=belief.get(edge,{});report=self.hazard_buf.get(edge);use=False;reason='no_report'
   if report:
    threat,ts,conf=report;age=now-ts
    if not 0<=age<=self.tau_stale:reason='invalid_age'
    elif own.get('age',-np.inf)>=ts:reason='own_timestamp_precedence'
    elif self.mode=='NONE':reason='no_communication'
    elif self.mode=='ALL':use=True;reason='all_valid'
    elif not fork:reason='not_relevant_fork'
    elif conf<.6:reason='low_confidence'
    else:
     limit=self.eta*self.tau_stale if self.mode=='FRC' else min(self.tau_stale,self.eta*own.get('estimated_time',own.get('cost',3.)))
     use=age<=limit;reason='gate_pass' if use else 'inner_freshness'
    self.gate_log.append(dict(edge=list(edge),t=now,age=age,confidence=conf,used=use,reason=reason))
   q=self.Q.get(self.pos,{}).get(v,0.)
   if fork:
    q-=self.peer_weight*report[0] if use else self.local_weight*own.get('threat',.35)
   if use and fork:self.msgs_used+=1
   scores[v]=q
  # Retain the original exploration call and visit-based preference.
  if random.random()<self.epsilon:return random.choice(valid)
  return max(scores,key=scores.get)
 def update_transition(self,s,a,reward,s2,terminal=False):
  future=0. if terminal else max(self.Q[s2].values(),default=0.)
  self.Q[s][a]+=self.alpha*(reward+self.gamma*future-self.Q[s][a])


class RepairedSim(BaseSim):
 """Original graph, events/attacks/travel model; repairs individually documented."""
 def __init__(self,*args,agents,sensing='uniform',loss=0.,**kwargs):
  self.agents={a.id:a for a in agents};self.sensing=sensing;self.loss=loss;self.order=0;self.message_seq=0;self.committed=[];self.transitions=[];self.fail_times={};self.sent_records=[];self.delivery_records=[];self.routing_records=[];self.arrival_paths=defaultdict(list)
  self.packet_rng=np.random.default_rng(np.random.SeedSequence([int(kwargs.get('seed',42)),9031]))
  super().__init__(*args,**kwargs)
 def _schedule(self,time,etype,payload):
  if time<=self.max_time:self.order+=1;heapq.heappush(self.event_queue,OrderedEvent(time,self.order,etype,payload))
 def visible(self,node,radius):
  seen={node};front={node}
  for _ in range(radius):
   nxt={v for u in front for v in list(self.G.successors(u))+list(self.G.predecessors(u))};front=nxt-seen;seen|=nxt
  return seen
 def blind(self,edge,cid):
  # Declared topology mask; no access to attacks or future routes.
  u,v=edge
  return self.sensing=='mixed' and cid!=0 and 1<=u<=12 and 1<=v<=12
 def _update_belief(self,cv,node,now):
  nodes=self.visible(node,2 if self.sensing=='mixed' and cv.cid==0 else self.obs_radius)
  for u in nodes:
   for v in self.G.successors(u):
    if v not in nodes:continue
    es=self.edge_state[(u,v)];old=cv.belief.get((u,v))
    if self.blind((u,v),cv.cid):
     if old is None:cv.belief[(u,v)]=dict(active=True,threat=.35,cost=es['cost'],congestion=0.,age=-np.inf,corridor=es['corridor'],estimated_time=es['cost'])
     continue
    active=not es['revealed_blocked'];threat=es['threat'] if active else 1.
    cv.belief[(u,v)]=dict(active=active,threat=threat,cost=es['cost'],congestion=es['congestion'],age=now,corridor=es['corridor'],estimated_time=self._traversal_time(u,v))
    # Generate genuine reports from observations only, including initially risky edges.
    changed=old is None or old.get('active')!=active or old.get('threat')!=threat
    if changed and (not active or threat>=.25):
     payload=dict(type='HAZARD',edge=[u,v],corridor_node=v,threat_obs=threat,timestamp=now,confidence=1.,id=f'{cv.cid}:{self.message_seq}')
     self.message_seq+=1
     for receiver in self.convoys.values():
      if receiver.cid==cv.cid or receiver.delivered or receiver.failed:continue
      cv.messages_sent+=1;self.sent_records.append(dict(sender=cv.cid,receiver=receiver.cid,t=now,edge=[u,v],id=payload['id']))
      if self.packet_rng.random()>=self.loss:
       self._schedule(now+self.tau_msg,legacy().core.MSG_DELIVER,dict(sender=cv.cid,recipient=receiver.cid,payload=copy.deepcopy(payload),sent_at=now))
 def _execute_msg_deliver(self,sender,recipient,payload,sent_at):
  self.delivery_records.append(dict(sender=sender,receiver=recipient,sent_at=sent_at,t=self.sim_time,id=payload.get('id')))
  super()._execute_msg_deliver(sender,recipient,payload,sent_at)
 def _process_inbox(self,cv):
  agent=self.agents[cv.cid]
  for msg in cv.inbox:
   payload=msg['payload'];pid=payload.get('id');age=self.sim_time-payload.get('timestamp',msg['sent_at'])
   if payload.get('type')=='HAZARD' and pid not in agent.seen_ids and 0<=age<=self.tau_stale:
    agent.receive(payload);agent.seen_ids.add(pid)
  cv.inbox.clear()
 def _choose_next_node(self,cv,policy,q_tables=None):
  a=self.agents[cv.cid];a.pos=cv.position
  valid=[v for v in self.G.successors(cv.position) if cv.belief.get((cv.position,v),{}).get('active',False)]
  # Preserve original exploration/visited relaxation, but never revive a known block.
  threats=[self.G[cv.position][v]['threat_level'] for v in self.G.successors(cv.position)]
  fork=cv.position if len(threats)>=2 and max(threats)-min(threats)>a.delta else None
  chosen=a.act(valid,cv.belief,self.sim_time,fork)
  self.routing_records.append(dict(convoy=cv.cid,t=self.sim_time,node=cv.position,action=chosen))
  return chosen
 def _execute_reveal(self,edge):
  self.edge_state[edge]['revealed_blocked']=True
  for cv in self.convoys.values():
   if not cv.in_transit and not cv.delivered and not cv.failed:self._update_belief(cv,cv.position,self.sim_time)
  self._log(self.sim_time,legacy().core.RED_REVEAL,f'Edge {edge} revealed')
 def failure(self,cv):
  cv.failed=True;self.fail_times[cv.cid]=self.sim_time
  if cv.cid in self.hub_present[cv.position]:self.hub_present[cv.position].remove(cv.cid)
  self._release_hub_slot(cv.position)
 def _try_depart(self,cid,policy,q_tables=None):
  cv=self.convoys[cid]
  if cv.delivered or cv.failed or cv.in_transit:return
  node=cv.position;occupied=len(self.hub_present[node])+self.hub_in_service.get(node,0)-int(cid in self.hub_present[node])
  if node!=self.depot and occupied>=self.hub_capacity:
   if cid in self.hub_present[node]:self.hub_present[node].remove(cid)
   if cid not in self.hub_queues[node]:self.hub_queues[node].append(cid);cv._wait_start[node]=self.sim_time
   return
  self._update_belief(cv,node,self.sim_time);self._process_inbox(cv)
  for _ in range(self.G.out_degree(node)+1):
   nxt=self._choose_next_node(cv,policy,q_tables)
   if nxt is None:self.failure(cv);return
   es=self.edge_state[(node,nxt)]
   if es['active']:break
   cv.blocked_enc+=1;es['revealed_blocked']=True
   cv.belief[(node,nxt)]={**cv.belief.get((node,nxt),{}),'active':False,'threat':1.,'age':self.sim_time}
   # A personally encountered block is known even with a remote sensing gap.
   self._update_belief(cv,node,self.sim_time)
  else:self.failure(cv);return
  duration=self._traversal_time(node,nxt);arrive=self.sim_time+duration
  self.committed.append(dict(convoy=cid,u=node,v=nxt,depart=self.sim_time,arrive=arrive,cost=es['cost']))
  cv.in_transit=True;cv.transit_edge=(node,nxt,self.sim_time,arrive);cv.position=None;es['flow']+=1
  if cid in self.hub_present[node]:self.hub_present[node].remove(cid)
  self.hub_in_service[node]+=1;self._schedule(arrive,legacy().core.CONVOY_ARRIVE,dict(cid=cid))
 def _execute_arrive(self,cid):
  cv=self.convoys[cid];u,v,depart,arrive=cv.transit_edge
  self.transitions.append(dict(convoy=cid,u=u,v=v,t=self.sim_time,cost=self.G[u][v]['travel_cost'],threat=self.G[u][v]['threat_level']))
  agent=self.agents[cid];agent.path.append(v);agent.visited.add(v);agent.cost+=self.G[u][v]['travel_cost'];agent.surv_acc+=1.-self.G[u][v]['threat_level'];agent.steps+=1
  self.arrival_paths[cid].append(v)
  super()._execute_arrive(cid)
  if cv.delivered and cid in self.hub_present[v]:self.hub_present[v].remove(cid);self._release_hub_slot(v)


def canonical_rows(env,convoys,version='original'):
 rows=[]
 for cv in convoys:
  repaired=isinstance(env,RepairedSim)
  fail=not cv.delivered and (cv.cid in env.fail_times if repaired else any(x['type']=='CONVOY_FAIL' and x['detail'].startswith(f'C{cv.cid} ') for x in env.event_log))
  censor=not cv.delivered and not fail
  if cv.delivered:end=cv.arrive_time
  elif censor:end=env.max_time
  elif repaired:end=env.fail_times[cv.cid]
  else:end=next(x['time'] for x in env.event_log if x['type']=='CONVOY_FAIL' and x['detail'].startswith(f'C{cv.cid} '))
  if repaired or hasattr(env,'_audit_committed'):
   edges=[r for r in (env.committed if repaired else env._audit_committed) if r['convoy']==cv.cid];completed=[r for r in edges if r['arrive']<=end+1e-9]
   nominal=sum(r['cost'] for r in completed);travel=sum(max(0.,min(r['arrive'],end)-r['depart']) for r in edges)
   wait=cv.hub_wait_time+sum(max(0.,end-t) for t in cv._wait_start.values());dispatch=max(0.,end-cv.depart_time-travel-wait)
   path=[0]+[r['v'] for r in completed]
  else:nominal=None;travel=cv.total_time;wait=cv.hub_wait_time;dispatch=None;path=None
  rows.append(dict(convoy=cv.cid,target=cv.target,depart_t=cv.depart_time,delivered=int(cv.delivered),failed=int(fail),censored=int(censor),outcome_time=end,elapsed=end-cv.depart_time,nominal_cost=nominal,legacy_time_weighted_cost=float(cv.total_cost),travel=float(travel),wait=float(wait),dispatch=dispatch,blocked_enc=int(cv.blocked_enc),route_prior_score=float(cv.avg_surv),path=json.dumps(path)))
 return rows


def repaired_episode(agents,seed,network_seed=42,rb=2,reveal=5.,delay=2.,loss=0.,sensing='uniform',train=False,horizon=400.):
 random.seed(seed);np.random.seed(seed);G=legacy().core.make_network(seed=network_seed)
 for a in agents:a.reset()
 cvs=[legacy().core.Convoy(cid=a.id,target=a.target) for a in agents]
 env=RepairedSim(G,red_budget=rb,red_period=15.,tau_reveal=reveal,tau_msg=delay,tau_stale=8.,hub_capacity=5,obs_radius=1,max_time=horizon,seed=seed,agents=agents,sensing=sensing,loss=loss)
 original_stats=env.run(cvs,{c.cid:'TABULAR' for c in cvs});rows=canonical_rows(env,cvs,'repaired')
 if train:
  for cv in cvs:
   a=agents[cv.cid];ts=[r for r in env.transitions if r['convoy']==cv.cid];pathcost=sum(r['cost'] for r in ts);proxy=np.mean([1-r['threat'] for r in ts]) if ts else .5
   for i,r in enumerate(ts):
    terminal=i==len(ts)-1 and not rows[cv.cid]['censored'];reward=40.+40.*proxy-.03*pathcost if i==len(ts)-1 and cv.delivered else -(r['cost']+16.*r['threat'])
    a.update_transition(r['u'],r['v'],reward,r['v'],terminal=terminal)
   a.decay()
 stats=dict(delivery_rate=np.mean([r['delivered'] for r in rows]),route_score_delivered=np.mean([r['route_prior_score'] for r in rows if r['delivered']]) if any(r['delivered'] for r in rows) else np.nan,nominal_all_mean=np.mean([r['nominal_cost'] for r in rows]),elapsed_mean=np.mean([r['elapsed'] for r in rows]),blocked_total=sum(r['blocked_enc'] for r in rows),messages_sent=len(env.sent_records),messages_delivered=len(env.delivery_records),hazard_uses=sum(a.msgs_used for a in agents),gate_queries=sum(len(a.gate_log) for a in agents),n_delivered=sum(r['delivered'] for r in rows),n_failed=sum(r['failed'] for r in rows),n_censored=sum(r['censored'] for r in rows))
 return stats,rows,env
