"""Public full-inbox actor probes and one-override fleet-value admission.

Privileged future outcomes are used for development labels only. Routing
scores, never the privileged MAPPO critic value, enter deployment features.
"""
import copy
from dataclasses import dataclass
import numpy as np
import torch
from ammarl2.learn import build_ctx, gctx
from recovery_gate import FEATURES as BASE_FEATURES, RecoveryPolicy
from research_gate import ResearchPolicy
EXTRA_FEATURES=['probe_action_change','safe_accept','accept_message_edge','reject_message_edge',
 'accept_top_probability','reject_top_probability','accept_margin','reject_margin',
 'accept_remaining_cost','reject_remaining_cost','flip_nominal_saving',
 'accept_action_blocked','reject_action_blocked','accept_action_known','reject_action_known',
 'accept_action_age','reject_action_age','accept_action_confidence','reject_action_confidence',
 'actor_node_input_difference','actor_edge_input_difference','accept_message_probability','reject_message_probability']
FEATURES=BASE_FEATURES+EXTRA_FEATURES
ACTION_INDEX=FEATURES.index('probe_action_change')


def safe_accept(peer, feedback, packet, t, ttl):
 prior=peer.get(packet['e'])
 if packet['blocked'] or prior is None or not prior[0]:return True
 clear={r['sender'] for r in feedback.values() if r['e']==packet['e'] and not r['blocked'] and r['t_obs']>=prior[1] and 0<=t-r['t_obs']<=ttl}
 return len(clear)>=2


def finish_inbox(p,sim,cv,m,t,accept):
 """Reference continuation uses SAFE and received/public information only."""
 other=copy.deepcopy(cv);state=p.state(other);ttl=sim.cfg.tau_stale
 if accept:other.peer[m['e']]=(bool(m['blocked']),m['t_obs'],m['conf'])
 state['seen'].add(m['id'])
 for packet in p._ordered[p._positions[m['id']]+1:]:
  prior=p.merged(other,other.peer,t,ttl).get(packet['e'])
  eligible=(packet['id'] not in sim.suppressed_messages and 0<=t-packet['t_obs']<=ttl and packet['id'] not in state['seen'] and (prior is None or prior[1]<packet['t_obs']))
  if eligible:
   public={k:packet[k] for k in ['id','e','t_obs','conf','blocked','sender']};state['feedback'][packet['id']]=public
   if safe_accept(other.peer,state['feedback'],public,t,ttl):other.peer[packet['e']]=(bool(packet['blocked']),packet['t_obs'],packet['conf'])
  state['seen'].add(packet['id'])
 merged=p.merged(other,other.peer,t,ttl);blocked=p.banned(merged,t,ttl)
 context=build_ctx(sim,other,blocked,merged,t,ttl)
 # The critic has privileged inputs. They are neither read nor exported.
 context.glob.zero_()
 with torch.no_grad():scores,_=p.actor.agent_network(cv.id)(context)
 values=scores.detach().numpy();idx=int(values.argmax());edge=context.edges[idx]
 probability=torch.softmax(scores,0).numpy();ordered=np.sort(values)
 margin=float((ordered[-1]-ordered[-2])/(values.std()+1e-3)) if len(values)>1 else 0.
 rd=gctx(sim.g)[1][cv.target];belief=merged.get(edge)
 details=[float(probability[idx]),min(margin,10.)/10.,float((sim.g.c[edge]+rd[int(sim.g.dst[edge])])/40.),float(edge in blocked),float(belief is not None),(t-belief[1])/ttl if belief else 0.,belief[2] if belief else 0.,float(probability[context.edges.index(m['e'])]) if m['e'] in context.edges else 0.]
 return edge,details,context


class LeafForest:
 """Standard ExtraTrees fit, portable vectorized leaf inference; no pickle.

 Tree dispersion is a heuristic, not a calibrated probability or bound.
 """
 def fit(self,x,y,seed,n_estimators=160):
  from sklearn.ensemble import ExtraTreesRegressor
  x=np.asarray(x,float);y=np.asarray(y,float)
  self.features=list(FEATURES if x.shape[1]==len(FEATURES) else BASE_FEATURES)
  model=ExtraTreesRegressor(n_estimators=n_estimators,max_depth=8,min_samples_leaf=8,max_features=.8,bootstrap=True,max_samples=.8,n_jobs=1,random_state=seed).fit(x,y)
  n=max(t.tree_.node_count for t in model.estimators_);self.left=np.zeros((n_estimators,n),int);self.right=self.left.copy();self.feature=self.left.copy();self.threshold=np.zeros((n_estimators,n));self.values=np.zeros((n_estimators,n,2));self.depth=8
  for i,tree in enumerate(model.estimators_):
   tr=tree.tree_;k=tr.node_count;self.left[i,:k]=tr.children_left;self.right[i,:k]=tr.children_right;self.feature[i,:k]=np.maximum(tr.feature,0);self.threshold[i,:k]=tr.threshold;self.values[i,:k]=tr.value[:,:,0]
  for row,expected in zip(x[:10],model.predict(x[:10])):assert np.allclose(self.predict(row)[[0,2]],expected,atol=1e-12)
  return self
 def predict(self,x):
  x=np.asarray(x,float)[:len(self.features)];node=np.zeros(len(self.left),int);rows=np.arange(len(node))
  for _ in range(self.depth+1):
   left=self.left[rows,node];active=left>=0
   if not active.any():break
   right=self.right[rows,node];choice=x[self.feature[rows,node]]<=self.threshold[rows,node]
   node=np.where(active,np.where(choice,left,right),node)
  values=self.values[rows,node];mu=values.mean(0);std=values.std(0)
  return np.array([mu[0],std[0],mu[1],std[1]])
 def save(self,path):
  np.savez_compressed(path,features=np.array(self.features),left=self.left,right=self.right,feature=self.feature,threshold=self.threshold,values=self.values,depth=self.depth)
 @classmethod
 def load(cls,path):
  model=cls()
  with np.load(path,allow_pickle=False) as z:
   model.features=z['features'].tolist();model.depth=int(z['depth'])
   for name in ['left','right','feature','threshold','values']:setattr(model,name,z[name])
  assert model.features in [BASE_FEATURES,FEATURES];return model


class SingleAdmission:
 def __init__(self,p):self.p=p;self.records=[]
 def predict(self,x):
  p=self.p;safe=bool(x[len(BASE_FEATURES)+1]);chosen=safe;mu=std=dm=ds=0.;rule='safe_fallback'
  if p.method=='ALL':chosen=True;rule='all'
  elif p.method=='KEEP':chosen=not(x[0]<.5 and x[4]>.5);rule='keep'
  elif p.method=='AGE':chosen=x[1]>=p.confidence and (not(x[0]<.5 and x[4]>.5) or x[6]*8>=p.age_limit or x[12]>.5);rule='age'
  elif p.method=='LEARN' and p.base_model is not None and not p.override_used and x[13]>.5 and x[ACTION_INDEX]>.5:
   mu,std,dm,ds=map(float,p.base_model.predict(x))
   if mu-p.beta*std>p.margin and dm-p.beta*ds>=-p.delivery_tolerance:
    chosen=not safe;rule='actor_value_override';p.override_used=True
  forced=p.force.get((p._cv.id,float(p._t),p._packet_id))
  if forced is not None:chosen=bool(forced);p.force_hits+=1;rule='forced_intervention'
  self.records.append(dict(accepted=chosen,fallback=safe,rule=rule,prediction=mu,prediction_std=std,delivery_prediction=dm,delivery_std=ds,features=list(x)))
  return (1. if chosen else -1.),0.


@dataclass
class ActorAwarePolicy(RecoveryPolicy):
 beta:float=.5
 delivery_tolerance:float=0.
 def __post_init__(self):
  super().__post_init__();self.override_used=False;self.probe_records={}
  if self.actor is None or self.actor.train:raise ValueError('Actor-aware development requires a frozen routing actor')
 def features(self,sim,cv,m,t):
  x=RecoveryPolicy.features(self,sim,cv,m,t)
  a,da,ca=finish_inbox(self,sim,cv,m,t,True);r,dr,cr=finish_inbox(self,sim,cv,m,t,False)
  fallback=safe_accept(cv.peer,self.state(cv)['feedback'],m,t,sim.cfg.tau_stale)
  flip_saving=(da[2]-dr[2]) if fallback else (dr[2]-da[2])
  extra=[float(a!=r),float(fallback),float(a==m['e']),float(r==m['e']),da[0],dr[0],da[1],dr[1],da[2],dr[2],flip_saving,da[3],dr[3],da[4],dr[4],da[5],dr[5],da[6],dr[6],float((ca.X-cr.X).abs().mean()),float((ca.EF-cr.EF).abs().mean()),da[7],dr[7]]
  assert len(extra)==len(EXTRA_FEATURES) and np.isfinite(extra).all()
  self.probe_records[(cv.id,float(t),m['id'])]=dict(probe_accept_edge=a,probe_reject_edge=r)
  return x+extra
 def decide(self,sim,cv,t):
  from ammarl2.graph import dists
  self._cv=cv;self._t=t;self._routes={};self._dist=dists(sim.g,cv.node,sim.g.c)
  self._ordered=sorted(cv.inbox,key=lambda m:(m['t_obs'],m['id']));self._positions={m['id']:i for i,m in enumerate(self._ordered)}
  packets={m['id']:m for m in cv.inbox};adapter=SingleAdmission(self);self.value_model=adapter;start=len(sim.message_audit)
  try:edge=ResearchPolicy.decide(self,sim,cv,t)
  finally:self.value_model=None
  queries=iter(adapter.records)
  for record in sim.message_audit[start:]:
   if record['reason'] not in ['accepted','predicted_low_value']:continue
   q=next(queries);record.update(predicted_value=q['prediction'],value_uncertainty=q['prediction_std'],admission_rule=q['rule'])
   if self.collect:
    m=packets[record['id']];key=(cv.id,float(t),m['id'])
    self.candidates.append(dict(id=m['id'],convoy=cv.id,t=float(t),edge=m['e'],genuine=bool(m['genuine']),blocked_report=bool(m['blocked']),**{k:v for k,v in q.items() if k!='features'},**self.probe_records[key],**dict(zip(FEATURES,q['features']))))
  assert next(queries,None) is None;return edge


def policy(method,actor,model=None,**kwargs):
 return ActorAwarePolicy(method,method=method,actor=actor,base_model=model,weights='threat',use_obs=True,response_strength=12.,relevance_scope='reachable',**kwargs)
