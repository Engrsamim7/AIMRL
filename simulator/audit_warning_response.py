"""Diagnostic single-action response to received genuine on-route warnings.

Each intervention follows a feasible route avoiding the reported edge once,
then resumes the unchanged policy. Choice uses public reference weights only.
Genuine label selects the diagnostic population, never a deployable policy.
This is not a new competing algorithm or a bound on attainable performance.
"""
import argparse
import copy
import hashlib
import heapq
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ammarl2.graph import dijkstra
from ammarl2.reviewer import m4_sensing
from ammarl2.sim import DEPART
from audit_communication_opportunities import decision_probe
from run_adaptive_experiments import MixedSpoofSim, REGIMES, adaptive, config, fingerprint, graph_cases

ROOT = Path(__file__).resolve().parents[1]


class OneAction:
    def __init__(self, inner, cid, t, first_edge, warned_edge):
        self.inner, self.cid, self.t = inner, cid, t
        self.first_edge, self.warned_edge = first_edge, warned_edge
        self.used = False

    def __getattr__(self, name):
        # Explicit access avoids recursion during deepcopy/unpickling.
        inner = object.__getattribute__(self, 'inner')
        return getattr(inner, name)

    def decide(self, sim, cv, t):
        edge = self.inner.decide(sim, cv, t)
        if not self.used and cv.id == self.cid and t == self.t:
            self.used = True
            cv.believed_blocked.add(self.warned_edge)
            sim.decisions[-1]['edge'] = self.first_edge
            trace = list(sim.trace[-1]);trace[3] = self.first_edge
            sim.trace[-1] = tuple(trace)
            return self.first_edge
        return edge


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', default='simulator/out/communication-opportunity-audit')
    args = ap.parse_args()
    out = Path(args.run).resolve()
    manifest = json.loads((out/'manifest.json').read_text())
    assert manifest['status'] == 'completed' and manifest['source_hash'] == fingerprint()
    script_digest = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    packet_path = out/'packets.csv'
    packets = pd.read_csv(packet_path if packet_path.exists() else packet_path.with_suffix('.csv.gz'))
    selected = packets[(packets.scope == 'network') & (packets.method == 'SOFT-ALL') &
                       packets.structural_warning_opportunity & (packets.regime != 'reactive-spoof')]
    selected = selected.drop_duplicates(['graph','regime','episode','convoy','decision_t','edge'])
    params = json.loads((ROOT/'simulator/out/adaptive-gate-v2/selected.json').read_text())['parameters']
    graphs = {gid:g for gid, _, g in graph_cases(False, manifest['arguments']['graphs'])}
    results = []
    for (gid, regime, ep), targets in selected.groupby(['graph','regime','episode']):
        g, cfg = graphs[gid], config(regime)
        seed = 14000000+gid*1000+REGIMES.index(regime)*100+ep
        snapshots = []
        def capture(sim, cv, t):
            rows = targets[(targets.convoy == cv.id) & np.isclose(targets.decision_t,t,rtol=0,atol=1e-12)]
            if rows.empty:
                return
            _, _, weights, _ = decision_probe(sim,cv,t)
            for _, r in rows.iterrows():
                assert any(m['id'] == r.id for m in cv.inbox)
                alt = dijkstra(g,cv.node,cv.target,weights,banned={int(r.edge)})
                assert alt
                hook = sim.before_decision;sim.before_decision = None
                try:
                    shadow = copy.deepcopy(sim)
                finally:
                    sim.before_decision = hook
                heapq.heappush(shadow.ev,(t,-1,DEPART,cv.id))
                shadow.policy = OneAction(shadow.policy,cv.id,t,alt[0],int(r.edge))
                snapshots.append((shadow,r))
        sim = MixedSpoofSim(g,cfg,adaptive('SOFT-ALL',params,mode='all'),seed,m4_sensing(g,True))
        sim.before_decision = capture
        factual = sim.run()
        assert len(snapshots) == len(targets)
        for shadow, r in snapshots:
            counter = shadow.run()
            assert shadow.policy.used
            common = min(sim.t,shadow.t)
            assert [a for a in sim.attack_log if a[0]<=common] == [a for a in shadow.attack_log if a[0]<=common]
            cid = int(r.convoy);a,b = factual['rows'][cid],counter['rows'][cid]
            results.append(dict(
                family=r.family,graph=gid,regime=regime,episode=ep,convoy=cid,
                decision_t=r.decision_t,edge=int(r.edge),message_id=r.id,
                active_at_decision=bool(r.active_at_decision),
                alternative_clear_now=bool(r.alternative_clear_now),
                alternative_extra_model_cost=r.alternative_extra_model_cost,
                innovation=r.innovation,estimated_route_regret=r.estimated_route_regret,
                changed_receiver_path=sim.cv[cid].path != shadow.cv[cid].path,
                gain_delivery=b['delivered']-a['delivered'],
                gain_episode_deliveries=sum(x['delivered'] for x in counter['rows'])-sum(x['delivered'] for x in factual['rows']),
                delta_blocked_encounters=b['blocked_enc']-a['blocked_enc'],
                delta_nominal=b['nominal']-a['nominal'],
                delta_realized_common_survivor=b['realized']-a['realized'] if a['delivered'] and b['delivered'] else np.nan,
            ))
    pd.DataFrame(results).to_csv(out/'warning_action_effects.csv',index=False)
    assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == script_digest
    assert len(results) == len(selected)
    meta = dict(status='completed',source_hash=fingerprint(),script_sha256=script_digest,
                interventions=len(results),
                selection='All SOFT-ALL genuine fresh not-locally-superseded on-route block reports with an alternative, in exogenous network regimes; collapse same decision and edge',
                action='One next hop on public-weight shortest route avoiding warned edge; then resume unchanged policy',
                limits='Uses genuine labels to select diagnostic cases. No learned or deployable oracle gate; no optimal bound. Does not force subsequent avoidance beyond first action; no test-set tuning.')
    (out/'warning_response_manifest.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(json.dumps(meta))


if __name__ == '__main__':
    main()
