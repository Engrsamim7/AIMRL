from dataclasses import replace
import math
import numpy as np
from timed_network import Calibration,Scenario,Schedule,TimedNetwork,Graph,graph_for,path


def calibration():
 m=Calibration();m.count[:]=1000;m.success[1]=1000;m.prior_count[:]=1000;m.prior_success[:]=100
 return m


def diamond():
 src=np.array([0,1,0,2]);dst=np.array([1,3,2,3]);out=[[0,2],[1],[3],[]]
 return Graph(4,0,[3],src,dst,np.array([1.,1.,1.3,1.3]),np.full(4,.1),np.full(4,10.),np.arange(4),out)


def configured(method,closed=True,inspection=4.):
 case=Scenario(n_convoys=2,scout_lead=1.,hub_service=0.,coverage=0.,delay=0.,packet_time=0.,inspection=inspection,perfect_sensors=True,closure_fraction=0.)
 s=TimedNetwork(diamond(),case,method,31,calibration(),record=True)
 s.schedule.intervals={1:(0.,5.)} if closed else {}
 return s


def test_genuine_timely_warning_changes_actual_route_and_avoids_blocked_entry():
 a=configured('NONE');b=configured('AGE_ALL');sa,ra=a.run();sb,rb=b.run()
 assert sa['encounters']>sb['encounters']
 assert sb['peer_action_changes']>0 and sb['transmitted']>0
 assert ra[1]['elapsed']>rb[1]['elapsed']
 assert all(not b.schedule.closed(e,t) for e,t in [] )


def test_physical_block_is_not_traversed_and_accounting_balances():
 s=configured('NONE');stats,rows=s.run()
 for row in rows:
  assert math.isclose(row['elapsed'],sum(row[k] for k in ['travel','service','wait','inspection','hold']),abs_tol=1e-9)
  assert math.isclose(row['nominal'],sum(s.g.c[e] for e in eval(row['path'],{'__builtins__':{}})))
 assert stats['encounters']>0 and rows[1]['inspection']>0


def test_finite_schedule_is_independent_of_policy_and_exact_budget():
 g=graph_for(17,19);case=Scenario()
 a=TimedNetwork(g,case,'NONE',18,calibration());b=TimedNetwork(g,case,'VALUE',18,calibration())
 assert a.schedule.digest==b.schedule.digest and len(a.schedule.intervals)==round(case.closure_fraction*g.m)


def test_hidden_remote_truth_does_not_enter_actor_choice():
 s=configured('AGE_ALL');u=s.units[1];u.node=0;s.t=1.
 before=s.choose(u)[0];s.schedule.intervals={0:(0.,100.),1:(0.,100.),2:(0.,100.)}
 assert s.choose(u)[0]==before


def test_sender_uses_public_manifest_not_live_receiver_positions():
 a=configured('VALUE');b=configured('VALUE');b.units[1].node=2;b.units[1].status='travel'
 for s in [a,b]:s.radio_busy=True;s.offer(s.units[0],1,True,0.,1.)
 assert a.radio==b.radio


def test_real_packet_serialization_adds_queue_age_and_no_comm_sends_zero():
 s=configured('AGE_ALL');s.case=replace(s.case,packet_time=1.);stats,rows=s.run()
 assert stats['radio_queue_delay']>0 and all(p['tx_end']>=p['tx_start']+s.scale-1e-9 for p in s.packets)
 none=configured('NONE');assert none.run()[0]['transmitted']==0


def test_pending_packets_coalesce_and_value_can_transmit_clearance():
 s=configured('LATEST');s.radio_busy=True;u=s.units[0]
 s.offer(u,1,True,0.,1.);s.t=1.;s.offer(u,1,False,1.,1.)
 assert len(s.radio)==1 and not s.radio[0]['blocked'] and s.stats['coalesced']==1
 s=configured('VALUE');s.radio_busy=True;u=s.units[0];u.advertised[1]=(True,0.,1.);s.t=1.;s.offer(u,1,False,1.,1.)
 assert len(s.radio)==1 and not s.radio[0]['blocked']


def test_explicit_zero_inspection_control_makes_time_progress():
 s=configured('NONE',inspection=0.);stats,rows=s.run()
 assert stats['routing_calls']<100 and all(row['elapsed']>0 for row in rows)


def test_all_graph_sizes_preserve_target_reachability():
 for size in [19,51,131]:
  g=graph_for(29,size);assert g.n==size
  assert all(path(g,g.depot,t,g.c) for t in g.targets)


def test_stale_report_is_reinterpreted_and_persistent_truth_is_retained_by_age_aware():
 s=configured('AGE_ALL',closed=False);u=s.units[1];s.t=4.;u.peer[1]=(True,0.,1.)
 # A synthetic known recovery law for this isolated interpretation fixture.
 s.model.success[1,2:]=0
 age_choice=s.choose(u)[0];s.method='RAW_ALL';raw_choice=s.choose(u)[0]
 assert age_choice==0 and raw_choice==2
 s.model.success[1]=1000;s.method='AGE_ALL';assert s.choose(u)[0]==2
 s.method='FRC';assert s.choose(u)[0]==0


def test_hub_queue_wait_ages_retained_reports_before_actual_decision():
 case=Scenario(n_convoys=5,scout_lead=0.,hub_service=1.,hub_capacity=1,coverage=0.,closure_fraction=0.,packet_time=0.)
 s=TimedNetwork(diamond(),case,'FRC',32,calibration(),record=True)
 s.observation_edges=lambda u:[]
 for u in s.units:u.peer[1]=(True,0.,1.)
 stats,rows=s.run()
 early=next(r for r in s.decisions if r['convoy']==0)
 late=next(r for r in s.decisions if r['convoy']==4)
 assert early['peer_reports']>0 and late['t']>=5 and late['peer_reports']==0
 assert rows[4]['wait']>0


def test_zero_admission_threshold_is_a_matched_priority_only_ablation():
 a=configured('VALUE');b=configured('VALUE');a.value_threshold=0.;b.value_threshold=.05
 for s in [a,b]:
  s.radio_busy=True
  s.offer(s.units[0],3,False,0.,1.)
  s.offer(s.units[0],1,True,0.,1.)
 assert a.stats['value_rejected']==0 and b.stats['value_rejected']>0
 common={p['id']:p for p in a.radio}
 assert b.radio and all(common[p['id']]==p for p in b.radio)
 assert a.model.state()==b.model.state()


def test_partial_frame_charges_started_bytes_and_exact_airtime():
 case=Scenario(n_convoys=1,packet_time=100.,closure_fraction=0.,hub_service=0.,perfect_sensors=True)
 s=TimedNetwork(diamond(),case,'AGE_ALL',44,calibration(),record=True)
 before=s.model.state();stats,rows=s.run()
 assert stats['tx_started']==1 and stats['transmitted']==0
 assert stats['attempted_tx_bytes']==64 and stats['tx_bytes']==0
 assert math.isclose(stats['radio_airtime'],rows[0]['elapsed'])
 assert before==s.model.state()
