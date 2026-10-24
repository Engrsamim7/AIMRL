import copy
from dataclasses import replace
import numpy as np
import pytest
import torch
from delivery_learning import DeliveryNetwork,Actor
from pretransmission import PreTransmissionNetwork,paired_radio
from tests_timed_network import diamond,calibration
from timed_network import Scenario


def fixture(method='RAW_ALL',packet_time=.6,actor=None):
    c=Scenario(n_convoys=2,coverage=0.,scout_lead=1.,hub_service=0.,closure_fraction=0.,
               delay=0.,packet_time=packet_time,inspection=4.,perfect_sensors=True)
    s=PreTransmissionNetwork(diamond(),c,method,31,calibration(),value_threshold=0.,actor=actor,receiver='ALL',record=True)
    s.schedule.intervals={1:(0.,5.)}
    return s


@pytest.mark.parametrize('packet_time',[0.,.25,1.])
@pytest.mark.parametrize('method',['RAW_ALL','WARN_PRIORITY','VALUE'])
def test_noop_reservation_preserves_complete_original_physics_and_order(packet_time,method):
    s=fixture(method,packet_time)
    original=DeliveryNetwork(s.g,s.case,method,31,calibration(),value_threshold=0.,record=True)
    original.schedule.intervals=copy.deepcopy(s.schedule.intervals)
    expected=original.run();actual=s.run()
    assert expected==actual
    assert original.packets==s.packets and original.decisions==s.decisions


def paused_queue(actor=None):
    s=fixture(actor=actor);s.radio_busy=True
    s.offer(s.units[0],3,False,0.,1.)
    s.offer(s.units[0],1,True,0.,1.)
    s.radio_busy=False;s.start_radio();s.radio_capture=lambda env:True
    assert s.run() is None
    return s


def test_factual_send_reproduces_uninterrupted_baseline():
    s=paused_queue();pairs=paired_radio(s,['send','drop','defer','swap'])
    s.radio_capture=None;s.intervene('send');actual=s.advance(initialize=False)
    assert pairs['send']==actual
    assert pairs['swap'][0]['on_time']>pairs['send'][0]['on_time']


def test_drop_removes_unsent_reservation_without_ghost_transmission():
    s=paused_queue();number=s.reservation['packet']['number'];seq=s.reservation['event_sequence']
    s.radio_capture=None;s.intervene('drop')
    assert not any(e[1]==seq for e in s.events)
    s.advance(initialize=False)
    # Semantic loss IDs may recur for duplicate offers of the same observation;
    # the removed reservation is identified by its distinct offer number.
    assert all(p['number']!=number for p in s.packets)
    assert s.stats['transmitted']<=s.stats['tx_started']


def test_defer_delays_only_selected_packet_not_urgent_alternative():
    s=paused_queue();pid=s.reservation['packet']['id']
    s.intervene('defer')
    assert s.active_packet is not None and s.active_packet['edge']==1
    assert s.active_packet['tx_start']==s.t
    delayed=next(p for p in s.radio if p['id']==pid)
    assert delayed['ready_at']==s.t+s.case.packet_time*s.scale


def test_future_ready_offer_can_use_radio_while_deferred_packet_waits():
    s=paused_queue();s.radio=[];s.intervene('defer');assert not s.radio_busy
    s.t+=.1*s.scale;s.offer(s.units[0],1,True,s.t,1.)
    assert s.radio_busy and s.active_packet['edge']==1 and s.active_packet['tx_start']==s.t


def test_mac_features_exclude_remote_positions_flow_and_hidden_closures():
    s=paused_queue();before=s.radio_features()
    s.units[1].node=3;s.units[1].peer[1]=(False,0.,1.);s.flow[:]=999
    s.schedule.intervals={0:(0.,999.),2:(0.,999.)}
    assert np.array_equal(before,s.radio_features())


def test_frozen_actor_shared_but_branch_queues_are_independent():
    torch.set_num_threads(1);s=paused_queue(Actor(9));b=copy.deepcopy(s)
    assert b.actor is s.actor and b.radio is not s.radio
    assert b.reservation['packet'] is b.active_packet
    b.intervene('drop');assert s.radio_paused and s.reservation is not None


def test_zero_inspection_noisy_radio_run_terminates():
    torch.set_num_threads(1);s=fixture('VALUE',0.,Actor(9));s.case=replace(s.case,inspection=0.,perfect_sensors=False,accuracy_scale=.5)
    stats,rows=s.run();assert stats['routing_calls']<500
    for r in rows:assert np.isclose(r['elapsed'],sum(r[k] for k in ['travel','service','wait','inspection','hold']))


def test_batched_priority_reselects_using_queue_information_only():
    s=fixture('VALUE');s.radio_busy=True
    s.offer(s.units[0],3,False,0.,1.);s.offer(s.units[0],1,True,0.,1.)
    s.radio_busy=False;s.start_radio();assert s.active_packet['edge']==1
    # A better packet arriving in the enclosing atomic event can replace a
    # lower-priority reservation before any airtime is consumed.
    s.active_packet['score']=-1.;s.radio[0]['score']=2.;s.batch_priority=True
    assert not s.boundary() and s.active_packet['edge']==3
    assert s.reservation is None and s.stats['tx_started']==1
