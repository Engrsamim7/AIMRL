import numpy as np
import pandas as pd
from run_recovery_gate_study import select_settings, DESIGN
from report_recovery_gate_study import bounds, CORRECTION

def test_validation_rejects_high_utility_option_that_breaks_delivery_constraint():
 rows=[]
 for algo in ['dqn','mappo']:
  rows.append(dict(algo=algo,method='SAFE',config=0,delivery_rate=.8,utility_mean=0.))
  for method in ['LEARN','AGE']:
   for i in range(len(DESIGN['validation_candidates'][method])):
    rows.append(dict(algo=algo,method=method,config=i,delivery_rate=.7 if i==0 else .8,utility_mean=100. if i==0 else 2. if i==1 else 0.))
 settings,audit=select_settings(pd.DataFrame(rows))
 for algo in settings:
  for method in settings[algo]:assert settings[algo][method]==DESIGN['validation_candidates'][method][1]
 assert sum(r['selected'] for r in audit)==4

def test_validation_fallback_prioritizes_delivery_when_every_option_fails():
 rows=[]
 for algo in ['dqn','mappo']:
  rows.append(dict(algo=algo,method='SAFE',config=0,delivery_rate=1.,utility_mean=0.))
  for method in ['LEARN','AGE']:
   for i in range(len(DESIGN['validation_candidates'][method])):
    rows.append(dict(algo=algo,method=method,config=i,delivery_rate=.8 if i==2 else .7,utility_mean=0. if i==2 else 100.))
 settings,_=select_settings(pd.DataFrame(rows))
 for algo in settings:
  for method in settings[algo]:assert settings[algo][method]==DESIGN['validation_candidates'][method][2]

def test_simultaneous_interval_retains_signed_effects():
 samples=np.tile([[-2.,3.]],(200,1));lo,hi=bounds(samples)
 assert CORRECTION==388 and np.array_equal(lo,[-2.,3.]) and np.array_equal(hi,lo)
