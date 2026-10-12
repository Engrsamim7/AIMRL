"""Fresh paired frozen-weight actor test; no new offline training."""
import argparse,copy,json,hashlib,time
from pathlib import Path
import pandas as pd
import torch
from adaptive_actor import AdaptiveActor
from run_adaptive_experiments import MixedSpoofSim,config,REGIMES,fingerprint,write_json
from run_reviewer_revision import load
from ammarl2.reviewer import original_graph,m4_sensing
from ammarl2.metrics import episode_metrics


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--input',default='out/adaptive-gate-v2');ap.add_argument('--episodes',type=int,default=30);a=ap.parse_args();run=Path(a.input);out=run/'actor-inference';out.mkdir(exist_ok=False);params=json.loads((run/'selected.json').read_text())['parameters'];torch.set_num_threads(1)
    weights=sorted((run/'baseline_models').glob('*.pt'));assert len(weights)==20
    rows=[];raw=[];g=original_graph()
    for path in weights:
        fitted=load(path)
        for ri,regime in enumerate(REGIMES):
            for ep in range(a.episodes):
                all_actor=copy.deepcopy(fitted);all_actor.comm='all';all_actor.name=fitted.algo.upper()+'-ALL'
                frc=copy.deepcopy(fitted);frc.comm='gate';frc.name=fitted.algo.upper()+'-FRC';frc.eta=1.;frc.kappa_min=.6
                adaptive=AdaptiveActor.from_fitted(fitted,params)
                for actor in [all_actor,frc,adaptive]:
                    before={name:tensor.clone() for name,tensor in actor.net.state_dict().items()}
                    sim=MixedSpoofSim(g,config(regime),actor,19000000+ri*100+ep,m4_sensing(g,True));start=time.perf_counter();result=sim.run()
                    assert all(torch.equal(tensor,before[name]) for name,tensor in actor.net.state_dict().items())
                    key=dict(algo=fitted.algo,training_seed=fitted.seed,regime=regime,episode=ep,method=actor.name)
                    rows.append(dict(**key,**episode_metrics(result['rows']),**result['stats'],seconds=time.perf_counter()-start));raw.extend(dict(**key,**r) for r in result['rows'])
        print('actor tested '+path.name,flush=True)
    pd.DataFrame(rows).to_csv(out/'episodes.csv',index=False);pd.DataFrame(raw).to_csv(out/'convoys.csv',index=False)
    write_json(out/'manifest.json',dict(status='completed',source_hash=fingerprint(),actor_source_sha256=hashlib.sha256(Path(__file__).with_name('adaptive_actor.py').read_bytes()).hexdigest(),runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),episodes=len(rows),new_offline_training_episodes=0,scope='original topology, frozen weights, reference-planner gate proxy; no actor-specific value learning',checks=['network weights unchanged','same episode schedules across modes']))

if __name__=='__main__':main()
