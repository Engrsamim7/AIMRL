# Recovery-gate implementation contract

The executable specification is `recovery_gate.py`; training and selection are in `run_recovery_gate_study.py`. The prospective scientific protocol is `../revision/recovery-gate-protocol.md`. This extension leaves prior simulator studies unchanged.

## What the gate knows

The input is a 30-dimensional receiver-local/public vector: reported blocked status, confidence and age/TTL; prior peer and own knowledge; prior warning age/confidence; claimed-source agreement based on later own observations; counts of fresh claimed warning/clear sources; two-source clearance corroboration; nominal directed reachability; reference shortest-route membership and first-action change under admission; nominal distance and detour cost; remaining reference cost; edge cost; warning-clear conflict; follower role; elapsed time; later same-edge packet counts/claimed sources and age; whether the edge starts at the current node; reference route length after admission. Exact names and scales are `FEATURES` and `RecoveryPolicy.features`.

Reference routes use public nominal costs, threat weights and the current belief response. They do not query the active hazard state or probe the actual neural actor's action. Real packet origin, physical recovery schedules, condition labels and future events are excluded. Origin is used only for auditing. Source identity is claimed and can be impersonated; two identities do not imply two authenticated observers.

## Inference

Common eligibility checks precede admission: suppressed, expired/future, duplicate and superseded packets cannot be revived by the learned gate. A fresh own observation has timestamp precedence. Packets are processed chronologically; accepted evidence affects subsequent interpretation. Later-inbox features use packets already received at the current decision, not future transmissions.

SAFE admits an eligible warning; an eligible clearance against a peer warning needs two fresh claimed clear sources. All other eligible messages are admitted. For a reachable edge the learned model returns utility mean `mu`, bootstrap standard deviation `sigma`, estimated risk of accepting and estimated risk of rejecting.

```
choice = SAFE(packet, receiver_state)
if nominally_reachable(edge) and overrides_used_by_receiver < 2:
    proposed_accept = mu > 0
    gain_score = abs(mu) - 0.5 * sigma
    risk = accept_risk if proposed_accept else reject_risk
    if proposed_accept != choice and gain_score > margin and risk <= risk_limit:
        choice = proposed_accept
        overrides_used_by_receiver += 1
```

The rejection-only ablation additionally forbids accepting a packet SAFE would reject. The budget limits override count, not the magnitude of harm. Bootstrap disagreement and risk-head probabilities are heuristic, **not calibrated confidence or safety bounds**. No packet transmission is suppressed; this is receiver-side filtering, so no transmitted-bandwidth saving is claimed.

## Labels and estimator

For one eligible packet, clone the full pre-decision simulator and frozen neural actor twice. Force that packet accepted in one branch and rejected in the other after outer eligibility. Retain the remaining current inbox and all future events. Continue both episodes. The factual choice must exactly reproduce all convoy outcomes; common-time exogenous attacks and initial recovery schedule must agree.

Target `y = receiver_utility_accept - receiver_utility_reject`, where each receiver utility is `40*delivered - 40*destroyed - 40*censored - elapsed`. A second target is receiver delivery difference in `{-1,0,+1}`. Contextual marginal effects are nonadditive. The estimator targets receiver value; the primary experiment evaluates fleet utility, so alignment is empirical rather than guaranteed. Accept/reject branch records permit inspection of team effects.

Each of three bootstrap networks has shared 48-Tanh/48-Tanh layers and five outputs: impact logit, conditional utility/80, and three delivery-class logits. Fit 100 full-batch Adam steps at .003 with gradient clipping5. Loss is binary cross-entropy for `abs(y)>.1`, mean-square conditional utility error on those examples, and .5 times delivery cross-entropy. Per-member utility prediction is impact probability times conditional utility times80; return the mean and standard deviation across members. Accept risk is the negative-delivery class probability mean plus half its standard deviation, clipped0..1; reject risk analogously uses the positive-delivery class.

Normalization uses fitting examples only. Bootstrap resampling is at the example level and is an uncertainty heuristic. Eight complete episodes, one per condition, are excluded from each label collection for internal error diagnostics. These diagnostic labels are not the final-test environments. The three bootstrap members are not independent routing-training seeds.

## Training and validation

For each algorithm/seed, collect64 initial factual episodes with a frozen SAFE-warmup actor and balanced baseline behavior; sample within public packet strata using fixed outcome-independent random selection. Fit on first56 episodes. After150 learned-arm adaptation episodes, collect64 more with the current frozen learned-arm actor and gate; refit using both first56 collections. Holdouts remain excluded. Other arms do not receive additional routing-optimizer updates during this collection. Auxiliary compute and label interactions are extra.

The five routing arms share identical initial warmup actor/optimizer/replay/RNG state and adaptation environment tapes. Each final actor sees600 routing-training episodes. Inference settings are selected only on independent validation layouts and tapes; final checkpoints, estimators and settings are hashed and locked before final tests. See `design.json` and `locked_settings.json` in the delivered raw run for exact values, and the results for supported and unsupported comparisons. Neither 600 episodes nor a successful optimizer establishes convergence.
