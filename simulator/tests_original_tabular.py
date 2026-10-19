import copy,json
import numpy as np
from original_tabular import legacy,FixedGateAgent,repaired_episode,RepairedSim,canonical_rows,source_hashes
from run_original_tabular_study import historical_job


def setup_agents(mode='FRC',eps=0.):
 g=legacy().core.make_network(42);return [FixedGateAgent(i,g.graph['targets'][i],mode=mode,eps=eps) for i in range(3)]


def test_original_instrumentation_preserves_exact_direct_source_metrics(tmp_path):
 (tmp_path/'original').mkdir();(tmp_path/'original_models').mkdir()
 direct=legacy().gated['run_classical']('B2',lambda:legacy().core.make_network(42),2,5.,5,1,42)
 recorded=historical_job(('B2',42,str(tmp_path)))
 assert {k:v for k,v in recorded.items() if k not in ['method','seed']}==direct


def test_original_source_hashes_match_uploaded_inventory():
 inventory=json.loads((__import__('pathlib').Path(__file__).resolve().parents[1]/'revision/submission-code/inventory.json').read_text())
 actual=source_hashes()
 assert all(actual[r['file']]==r['sha256'] for r in inventory)


def test_reset_retains_q_and_clears_transient_hazards():
 a=setup_agents()[0];a.Q[0][1]=5.;a.receive(dict(edge=[0,1],threat_obs=1.,timestamp=2.,confidence=1.));a.seen_ids.add('x');a.reset()
 assert a.Q[0][1]==5. and not a.hazard_buf and not a.seen_ids


def test_future_expired_and_own_superseded_reports_cannot_influence_score():
 a=setup_agents()[0];a.pos=1;belief={(1,5):dict(threat=.2,cost=4.,age=0.)};a.Q[1][5]=1.
 for ts,now,own in [(10.,3.,0.),(0.,20.,0.),(2.,3.,3.)]:
  a.hazard_buf={(1,5):(1.,ts,1.)};belief[(1,5)]['age']=own;a.gate_log=[]
  a.act([5],belief,now,fork_node=1);assert not a.gate_log[-1]['used']


def test_zero_peer_response_strength_makes_filtering_modes_equal():
 # Deliberate synthetic equality fixture; local penalty identical in all modes.
 a=FixedGateAgent(0,13,mode='ALL',peer_weight=0.,local_weight=0.,eps=0.);b=FixedGateAgent(0,13,mode='FRC',peer_weight=0.,local_weight=0.,eps=0.)
 for p in [a,b]:p.pos=1;p.Q[1].update({5:1.,6:2.});p.hazard_buf[(1,6)]=(1.,0.,.1)
 belief={(1,v):dict(threat=.3,cost=3.,age=-1.) for v in [5,6]}
 assert a.act([5,6],belief,2.,1)==b.act([5,6],belief,2.,1)==6


def test_terminal_update_has_no_bootstrap_and_censor_can_bootstrap():
 a=setup_agents()[0];a.Q[5][9]=100.;a.update_transition(1,5,2.,5,terminal=True);assert np.isclose(a.Q[1][5],.15*2.)
 a.Q[1][5]=0.;a.update_transition(1,5,2.,5,terminal=False);assert np.isclose(a.Q[1][5],.15*(2.+.93*100))


def test_uniform_sensing_delayed_peer_data_does_not_override_fresh_own_evidence():
 outputs=[]
 for mode in ['NONE','ALL','FRC']:
  stats,rows,sim=repaired_episode(setup_agents(mode),300000000,rb=2,train=False)
  outputs.append(rows);assert stats['hazard_uses']==0 and stats['messages_sent']>0
 assert outputs[0]==outputs[1]==outputs[2]


def test_repaired_commits_real_edges_and_balances_elapsed_and_outcomes():
 stats,rows,s=repaired_episode(setup_agents(),300000001,sensing='mixed',train=True)
 assert sum(r['delivered']+r['failed']+r['censored'] for r in rows)==3
 for r in rows:
  assert np.isclose(r['elapsed'],r['travel']+r['wait']+r['dispatch'])
  path=json.loads(r['path']);assert all(s.G.has_edge(u,v) for u,v in zip(path,path[1:]))
  assert np.isclose(r['nominal_cost'],sum(s.G[u][v]['travel_cost'] for u,v in zip(path,path[1:])))
 assert all(a.path==[0]+s.arrival_paths[a.id] for a in s.agents.values())


def test_mixed_sensor_gap_preserves_unknown_prior_without_live_truth():
 a=setup_agents();g=legacy().core.make_network(42);s=RepairedSim(g,agents=a,sensing='mixed');s._init_edge_state();cv=legacy().core.Convoy(1,14);s.convoys={1:cv};s._update_belief(cv,1,2.)
 assert cv.belief[(1,5)]['age']==-np.inf and cv.belief[(1,5)]['threat']==.35
 s.edge_state[(1,5)]['revealed_blocked']=True;s.edge_state[(1,5)]['threat']=.99;s._update_belief(cv,1,3.)
 assert cv.belief[(1,5)]['age']==-np.inf and cv.belief[(1,5)]['threat']==.35
