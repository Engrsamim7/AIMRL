"""Metrics with explicit denominators; never mix reward penalties into nominal cost."""
import numpy as np
import pandas as pd


def episode_metrics(rows):
    df = rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)
    delivered = df[df.delivered == 1]
    gap = delivered.nominal - delivered.nominal_optimal
    if (gap < -1e-8).any():
        raise AssertionError('Delivered nominal cost below shortest path for identical depot/target')
    return dict(n_convoys=len(df), n_delivered=int(df.delivered.sum()),
                n_destroyed=int(df.destroyed.sum()), n_censored=int(df.censored.sum()),
                delivery_rate=float(df.delivered.mean()),
                nominal_all_mean=float(df.nominal.mean()),
                nominal_delivered_mean=float(delivered.nominal.mean()),
                nominal_excess_delivered_mean=float(gap.mean()),
                realized_delivered_mean=float(delivered.realized.mean()),
                blocked_encounters_total=int(df.blocked_enc.sum()),
                surprise_blocked_encounters_total=int(df.surprise_blocked_enc.sum()),
                surprise_blocked_encounters_per_convoy=float(df.surprise_blocked_enc.mean()),
                mission_complete=bool(df.delivered.all()),
                makespan_delivered_subset=float((delivered.depart_t+delivered.realized).max()-df.depart_t.min()),
                blocked_encounters_per_convoy=float(df.blocked_enc.mean()),
                hub_wait_per_convoy=float(df.wait.mean()),
                hub_service_per_convoy=float(df.service.mean()))


def paired_delivery_difference(a, b):
    """Match convoy outcomes before comparing survivor costs to avoid selection bias."""
    joined = a.merge(b, on=['convoy', 'target', 'depart_t'], suffixes=('_a', '_b'), validate='one_to_one')
    if len(joined) != len(a) or len(a) != len(b):
        raise ValueError('Paired evaluation requires identical convoy schedules')
    both = joined[(joined.delivered_a == 1) & (joined.delivered_b == 1)]
    return dict(n_common_delivered=len(both),
                delivery_rate_difference=float((joined.delivered_a - joined.delivered_b).mean()),
                nominal_difference_common_delivered=float((both.nominal_a - both.nominal_b).mean()))
