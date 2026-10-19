"""Read-only decision audit of the frozen original-family tabular study.

Counterfactual actions are local score probes, not counterfactual fleet outcomes.
No test data are used to fit/select a gate or retrain a routing model.
"""
import argparse
import hashlib
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from types import MethodType
import numpy as np
import pandas as pd
from original_tabular import repaired_episode, q_state
from run_original_tabular_study import fingerprint, load_agents, SEEDS, WEIGHTS, MODES, CASES


def score_probe(agent, valid_actions, belief, now, fork_node, mode):
    valid = [v for v in valid_actions if v not in agent.visited or v == agent.target] or list(valid_actions)
    scores, used, report_details = {}, [], []
    for v in valid:
        own = belief.get((agent.pos, v), {})
        report = agent.hazard_buf.get((agent.pos, v))
        use = False
        if report:
            threat, ts, confidence = report
            age = now - ts
            eligible = 0 <= age <= agent.tau_stale and own.get('age', -np.inf) < ts
            if eligible and mode == 'ALL':
                use = True
            elif eligible and mode in ['FRC', 'TRAVEL'] and fork_node is not None and confidence >= .6:
                limit = agent.eta * agent.tau_stale if mode == 'FRC' else min(agent.tau_stale, agent.eta * own.get('estimated_time', own.get('cost', 3.)))
                use = age <= limit
            report_details.append(dict(action=v, age=age, confidence=confidence,
                                       own_newer=own.get('age', -np.inf) >= ts, eligible=eligible,
                                       used_in_score=bool(use and fork_node is not None)))
        score = agent.Q.get(agent.pos, {}).get(v, 0.)
        if fork_node is not None:
            score -= agent.peer_weight * report[0] if use else agent.local_weight * own.get('threat', .35)
        scores[v] = score
        if use and fork_node is not None:
            used.append(v)
    return (max(scores, key=scores.get) if scores else None), scores, used, report_details


def observe(agent, rows, env_holder):
    original_act = agent.act
    def act(self, valid_actions, belief, now=0., fork_node=None):
        probes = {mode: score_probe(self, valid_actions, belief, now, fork_node, mode)
                  for mode in ['NONE', 'ALL', 'FRC', 'TRAVEL']}
        chosen = original_act(valid_actions, belief, now, fork_node)
        assert self.epsilon == 0. and chosen == probes[self.mode][0]
        env = env_holder[0]
        valid = list(probes[self.mode][1])
        q = sorted([self.Q.get(self.pos, {}).get(v, 0.) for v in valid], reverse=True)
        report_details = probes[self.mode][3]
        rows.append(dict(convoy=self.id, t=now, node=self.pos, action=chosen,
            choices=len(valid), fork=int(fork_node is not None),
            q_gap=q[0]-q[1] if len(q)>1 else np.nan,
            q_margin_exceeds_any_penalty=int(len(q)>1 and q[0]-q[1]>max(self.peer_weight,self.local_weight)),
            buffered_candidates=len(report_details), eligible_candidates=sum(x['eligible'] for x in report_details),
            own_newer_candidates=sum(x['own_newer'] for x in report_details),
            score_applications=len(probes[self.mode][2]),
            all_action=probes['ALL'][0], none_action=probes['NONE'][0], frc_action=probes['FRC'][0],
            all_frc_change=int(probes['ALL'][0]!=probes['FRC'][0]),
            all_none_change=int(probes['ALL'][0]!=probes['NONE'][0]),
            frc_none_change=int(probes['FRC'][0]!=probes['NONE'][0]),
            after_first_wave=int(now>=15.),
            # Evaluator truth below is never used by actor/probes.
            any_blocked_option=int(any(not env.edge_state[(self.pos,v)]['active'] for v in valid)),
            chosen_blocked=int(chosen is not None and not env.edge_state[(self.pos,chosen)]['active']),
            used_block_warnings=sum(int(env.edge_state[(self.pos,v)]['true_blocked']) for v in probes[self.mode][2])))
        return chosen
    agent.act = MethodType(act, agent)


def job(task):
    weight,sensing,si,gi,parent=task
    parent=Path(parent); decisions=[]; episodes=[]
    settings=json.loads((parent/'locked_settings.json').read_text())['travel_eta']
    network_seed=42 if gi==0 else 100099+gi
    # Obtain the environment reference without adding RNG draws or decisions.
    import original_tabular
    base=original_tabular.RepairedSim
    holder=[None]
    class ObservedSim(base):
        def __init__(self,*a,**kw):
            super().__init__(*a,**kw); holder[0]=self
    original_tabular.RepairedSim=ObservedSim
    try:
        for mode in MODES:
            agents=load_agents(parent/'models'/f'{weight}_{sensing}_{mode}_s{SEEDS[si]}.json')
            for a in agents:
                a.eta=settings[weight][sensing] if mode=='TRAVEL' else .4
            before=json.dumps(q_state(agents),sort_keys=True)
            for ci,c in enumerate(CASES):
                case=dict(c);name=case.pop('name')
                for ep in range(10):
                    local=[]
                    for a in agents:observe(a,local,holder)
                    stats,rs,env=repaired_episode(agents,320000000+gi*10000+ci*100+ep,network_seed=network_seed,sensing=sensing,**case)
                    key=dict(weight=weight,sensing=sensing,mode=mode,seed=SEEDS[si],graph=gi,case=name,episode=ep)
                    decisions.extend(dict(**key,**r) for r in local)
                    episodes.append(dict(**key,**stats,route_score_all=np.mean([r['route_prior_score'] for r in rs])))
                    # Restore wrappers before the next episode, avoiding nesting.
                    for a in agents:del a.act
            assert before==json.dumps(q_state(agents),sort_keys=True)
    finally:original_tabular.RepairedSim=base
    return decisions,episodes


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--parent',default='simulator/out/original-tabular-study');ap.add_argument('--output',default='simulator/out/tabular-decision-audit');ap.add_argument('--workers',type=int,default=4);args=ap.parse_args()
    parent=Path(args.parent).resolve();out=Path(args.output);out.mkdir(parents=True,exist_ok=False)
    design=dict(status='specified_before_audit',scope='read-only diagnostic of existing test outcomes; no fresh superiority test',
        parent_source_hash=fingerprint(),audit_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        probes='same frozen actor, same candidates, same belief, same coefficient specification; change receiver mode only',
        limitation='one-step score probes do not estimate fleet outcomes or isolated-message causal effects')
    (out/'design.json').write_text(json.dumps(design,indent=2)+'\n')
    tasks=[(w,s,i,g,str(parent)) for w in WEIGHTS for s in ['uniform','mixed'] for i in range(5) for g in range(9)]
    import gzip
    episode_rows=[]
    with ProcessPoolExecutor(max_workers=args.workers) as pool,gzip.open(out/'decisions.csv.gz','wt') as dest:
        for i,(ds,es) in enumerate(pool.map(job,tasks)):
            pd.DataFrame(ds).to_csv(dest,index=False,header=i==0);episode_rows.extend(es)
            if (i+1)%30==0:print(f'AUDIT {i+1}/{len(tasks)}',flush=True)
    observed=pd.DataFrame(episode_rows);observed.to_csv(out/'episodes.csv.gz',index=False)
    expected=pd.read_csv(parent/'test_episodes.csv.gz');keys=['weight','sensing','mode','seed','graph','case','episode']
    columns=['delivery_rate','route_score_all','nominal_all_mean','elapsed_mean','blocked_total','messages_sent','messages_delivered','hazard_uses','gate_queries']
    pd.testing.assert_frame_equal(observed.set_index(keys)[columns].sort_index(),expected.set_index(keys)[columns].sort_index(),check_exact=False,rtol=0,atol=1e-12,check_dtype=False)
    (out/'verification.json').write_text(json.dumps(dict(design=design,status='passed',parent_outcomes_reproduced=len(observed),checkpoint_q_unchanged=True,greedy_score_probe_matches_every_actual_action=True),indent=2)+'\n')
    print('READ-ONLY AUDIT COMPLETE',flush=True)

if __name__=='__main__':main()
