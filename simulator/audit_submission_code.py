"""Read preserved submission code; execute only selected definitions and CC2 fixtures.
Never imports final_pipeline or the top-level gated evaluation campaign.
"""
import ast,copy,hashlib,json,random,sys
from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd
root=Path(__file__).resolve().parents[1];src=root/'revision/submission-code';out=root/'revision/submission-code-audit';out.mkdir(exist_ok=True)
sys.path.insert(0,str(src))
from ammarl_sim_core import ContestedRoutingSim,Convoy,make_network
from cc2_scenario import run_cc2_episode
text=(src/'ammarl_gated_eval.py').read_text();tree=ast.parse(text)
names={'GatedQAgent','NoGateQAgent','MAPPOAgent','run_gated_episode'}
selected=ast.Module(body=[n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in names],type_ignores=[])
ns=dict(np=np,random=random,defaultdict=defaultdict,ContestedRoutingSim=ContestedRoutingSim,Convoy=Convoy,make_network=make_network)
exec(compile(selected,str(src/'ammarl_gated_eval.py'),'exec'),ns)
Agent=ns['GatedQAgent'];agent=Agent(0,13,eps=0)
agent.receive_hazard(1,.9,100.,1.)
checks={}
checks['future_timestamp_accepted']=bool(agent._gate_check(1,0.)[0])
agent.reset();checks['hazard_buffer_survives_episode_reset']=bool(agent.hazard_buf)
checks['retained_future_report_after_reset_is_accepted']=bool(agent._gate_check(1,0.)[0])
# Q scoring and simulated infrastructure smoke, without running full imported campaigns.
rows=[]
for seed in [42,137,271,999,1337]:
 g=make_network(seed=42);agents=[Agent(i,g.graph['targets'][i],eps=0) for i in range(3)]
 stats=ns['run_gated_episode'](agents,seed,lambda:make_network(seed=42),3,2,5.,5,1,train=False)
 rows.append(dict(seed=seed,**{k:float(v) for k,v in stats.items() if isinstance(v,(int,float,np.number))},hazard_entries=sum(len(a.hazard_buf) for a in agents),hazard_uses=sum(a.msgs_used for a in agents)))
checks['m4_hazard_entries_total']=sum(r['hazard_entries'] for r in rows)
checks['m4_hazard_uses_total']=sum(r['hazard_uses'] for r in rows)
pd.DataFrame(rows).to_csv(out/'m4_smoke.csv',index=False)
cc=[]
for seed in range(20):
 for mode in ['NC','AMMARL']:
  st,sim,convoys=run_cc2_episode(seed,mode)
  cc.append(dict(seed=seed,mode=mode,**{k:float(v) for k,v in st.items() if isinstance(v,(int,float,np.number))}))
pd.DataFrame(cc).to_csv(out/'cc2_smoke.csv',index=False)
tuning=pd.read_csv(src/'ammarl_tuning_best.csv')
checks['tuning_rows']=len(tuning)
checks['tuning_m4_gated_above_iql']=int((tuning.m4_amm_surv>tuning.m4_iql_surv).sum())
checks['tuning_cc_gated_above_nc']=int((tuning.cc_amm_surv>tuning.cc_nc_surv).sum())
# Extract fixed anchors without executing the graphics pipeline.
final=ast.parse((src/'final_pipeline.py').read_text())
anchors={}
for n in final.body:
 if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ['PAPER_FINAL','PAPER_STD'] for t in n.targets):
  anchors[n.targets[0].id]=ast.literal_eval(n.value)
(out/'fixed_presentation_anchors.json').write_text(json.dumps(anchors,indent=2))
report=dict(checks=checks,cc2_summary=pd.DataFrame(cc).groupby('mode')[['surv','dr','cost','msgs_fused']].mean().to_dict('index'),source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in src.iterdir() if p.is_file()},limits=['Five M4 episodes and twenty paired CC2 episodes are mechanism smoke checks, not full reproduction','Only selected gated classes/runner executed; top-level campaigns excluded','Fixed anchor provenance before entering final_pipeline is unverified'])
(out/'audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report['checks'],indent=2));print(json.dumps(report['cc2_summary'],indent=2))
