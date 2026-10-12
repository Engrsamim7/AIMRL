# Adaptive message-value gate: implementation and experiment contract

This extends the repaired simulator without changing its core sensor/observation contract or invalidating the previously fitted deep models. `simulator/adaptive_gate.py` implements a model-based routing and admission policy. It is not a newly trained neural gate and does not claim calibrated Bayesian beliefs or general superiority.

## Evidence, uncertainty and estimated decision value

Every convoy owns fresh episode state: latest admitted report per (edge, sender), pending local-feedback records, confirmed packet identifiers, and sender agreement counts. This state is copied in exact packet replay and is never shared across episodes. Repeated reports from one sender are not treated as independent evidence. Different claimed sender identities are treated as independent sources; this is an explicit vulnerability when identity is unauthenticated.

A missing local observation remains unknown under the declared scout/follower sensor mask. A newer valid local observation overrides older peer evidence. Future-dated, expired, duplicate, locally superseded and same-source older reports are rejected. Genuine/spoof labels are used only for experiment accounting; they never enter routing, reliability feedback, probability estimates or gate decisions.

For an unknown dynamic block, the fixed initial probability is 0.05, distinct from static edge threat `rho`. Static prior threat remains part of base planning cost `c * (1 + 6*rho)`. The 0.05 dynamic-block prior is an explicit modeling assumption, not a calibrated operational probability.

Sender agreement begins with Beta-style counts `(2,1)`. A report's credibility score is `r = 0.5 + 0.49 * confidence * sender_agreement`. Report evidence is discounted by `exp(-(age + estimated_time_to_edge_source)/(age_scale * estimated_edge_travel))`. Travel estimates use only declared visible flow; remote flow uses nominal cost. Signed log-odds contributions are combined across admitted sources. All evidence expires at the outer eight-unit TTL, including after queue/service delays.

Disagreement increases an uncertainty score. Planning uses `risk = clip(p + risk_aversion * uncertainty * sqrt(p*(1-p)), 0, 1)` and cost `base_cost + 12*risk`. Local observations have zero uncertainty. These quantities are approximate evidence/risk scores, not credible intervals or guaranteed probabilities.

For a candidate message, the policy temporarily recomputes the optimal route under the proposed evidence. Its decision-value proxy is the old route's new estimated cost minus the new optimal route's estimated cost, plus `innovation_weight * abs(new_p-old_p) * old_uncertainty`. It accepts reachable relevant evidence when this proxy exceeds `min_value`. This estimates routing regret and evidence innovation under the policy's own model; it does not know the message's true causal benefit. Estimated regret, innovation and sender agreement are logged per processed packet.

Agreement updates use only later local observations within eight units, once per packet, with `exp(-age/8)` weight. Changes in hazards between observation times can cause disagreement even for an honest source. The score is observed short-window agreement, not authentication or a dishonesty verdict. Rejected valid packets can still supply later feedback, reducing admission-based feedback bias.

## Conservative clearance safeguard

V2 adds a risk floor for uncorroborated clear reports. One unverified clear packet cannot lower an unknown edge below its prior risk or erase a fresh warning anchor, even if it claims the same sender as that warning. Direct local sensing overrides the safeguard. Two fresh clear reports from different claimed identities, with confidence at least .6 and sender agreement at least .6, can release it. Pending valid received clear reports count toward corroboration even when not yet admitted, avoiding a deadlock. Positive warning anchors expire at the outer TTL. Their decayed positive-only risk is a conservative floor, not a claim that the warning is certainly true.

This safeguard can delay legitimate clearance and maintain false warnings until sensing, corroboration or expiry resolves them. Multiple forged identities can defeat it; the tests include that failure. Claimed-source quorum is not cryptographic authentication. The safeguard affects VALUE-GATE; matched SOFT-ALL and SOFT-FRC retain the probabilistic estimator without this extra guard. The NO-CLEARANCE-GUARD ablation isolates its contribution.

## Baselines and ablations

- **NC / COMM-ALL / FRC / FRC-v2:** existing binary-belief routing with identical response strength 12; fixed FRC thresholds are respectively eta=1/confidence=.6 and eta=1/confidence=.4.
- **SOFT-NC:** the same uncertain risk planner with no peer admission.
- **SOFT-ALL:** the same fusion, feedback, aging and risk planner without value filtering, subject to common packet validity rules.
- **SOFT-FRC:** the same risk planner with fixed freshness/confidence/reachability admission; retained freshness is rechecked.
- **VALUE-GATE:** the uncertain risk planner with model-based decision-value admission.
- **NO-FEEDBACK / NO-RISK-AVERSION / NO-AGE-DISCOUNT:** separate component ablations. SOFT-ALL is also the no-value-filter ablation.
- **DQN/PPO/IPPO/MAPPO:** the existing 20 fitted models are reused with frozen weights for ALL and FRC inference on the original topology. No new offline training or deep-gate learning is claimed. Their five-seed results are descriptive secondary baselines; the primary contrasts isolate the model-based method.

Improvement over binary COMM-ALL alone cannot establish that value filtering caused the improvement: uncertain fusion and planning also differ. VALUE-GATE versus SOFT-ALL tests the additional value-admission component with otherwise matched parameters. Every heuristic uses the same response-strength coefficient, but soft probability weighting changes effective risk response; the matched soft comparators make this explicit.

## Frozen validation and new tests

Validation evaluates 27 parameter combinations: risk aversion 0/.25/.5, age scale 2/4/8, minimum value .02/.1/.3. It uses the original topology and one separate validation graph each at 39 and 51 nodes, with ten episode schedules in each of four regimes. Candidates must admit at least 5% of processed genuine reports in aggregate validation. Ranking first maximizes mean delivery, then minimizes delivered-only elapsed time and admitted packets, with deterministic parameter tie order. Thresholds are frozen before held-out evaluation. Delivered-only time is not mission completion time.

Regimes are prespecified: reliable communication (delay 1, no packet loss/spoofing); delayed spoofing (delay 4, loss .2, spoof rate 2); heavy spoofing (delay 4, loss .2, spoof rate 8); and reactive/targeted spoofing (delay 4, loss .2, spoof rate 2). Attacks use rate .5, duration 15–30, budget 5 and blocked-entry destruction probability .7. Three convoys, hub capacity two, service time one, reveal delay five, congestion factor .15 and horizon 300 are fixed. V2 spoofing mixes 60% forged clear reports about adversary-known active interdictions and 40% forged block reports about other edges. Fake claimed confidence has the same .85/.1 distribution as genuine confidence. Heavy/reactive regimes impersonate an existing convoy identifier with probability .25; the other regime uses a stable adversarial identifier. The policy never sees an authenticity label. Random-attack spoof locations depend only on the adversary's own exogenous interdictions, not future convoy paths, so controlled replay remains possible there. These are model units and synthetic mechanisms.

V2 held-out evaluation uses the original topology plus ten fresh graphs each at 39 and 51 nodes, thirty episode schedules per topology/regime. Sensor coverage is explicitly mixed: scout two-hop sensing, follower one-hop sensing with topology-determined gaps. Comparators share exact convoy schedules. V2 validation graph seeds start at 18200+size; test graph seeds at 19200+size. Validation episodes use `13000000 + graph_id*1000 + regime_index*100 + episode`; tests use `14000000 + graph_id*1000 + regime_index*100 + episode`. They are distinct from earlier studies and baseline training.

The 24 primary delivery contrasts are VALUE-GATE versus COMM-ALL and SOFT-ALL across three topology families and four regimes. Paired hierarchical graph/episode bootstrap intervals are Bonferroni-adjusted across those 24 comparisons. Original-topology intervals condition on that one graph. Supplementary fixed-gate/ablation contrasts are exploratory and are labeled separately. Tests estimate performance over the stated synthetic distributions, not universal superiority or operational validity.

## Controlled probes and replay

Additional fixtures compare accurate warnings, low-confidence false clear reports, high-confidence false clear reports, and false clear reports impersonating the scout, across delays 1/4 and loss 0/.2. Both hot branches are alternated. False reports use the configured delay. These constructed cases expose mechanism behavior and failure boundaries, not sampled real-world prevalence. The validation-selected parameters are used, so these experiments also test transfer from M4 to CC2.

Packet replay suppresses every processed packet in selected exogenous episodes, including rejected packets. It copies complete event/sensor/convoy/adaptive state and checks the exogenous attack sequence. Reports have conditional realized effects that are not additive. Reactive/targeted scenarios are total policy comparisons, not controlled message attribution.

## Reproduce and inspect

After `bash setup_local.sh`, activate `.venv` and run from `simulator/`:

```bash
python -m pytest -q tests_core.py tests_revision.py tests_manuscript_gate.py tests_reviewer_model.py tests_adaptive_gate.py
python run_adaptive_experiments.py --output out/my-adaptive-run
python run_clearance_stress.py --input out/my-adaptive-run
python run_adaptive_actor_eval.py --input out/my-adaptive-run
python report_adaptive_results.py --input out/my-adaptive-run --output ../revision/my-adaptive-results
```

The runner needs the existing baseline weights at `out/reviewer-revision-v2/models/`; the adaptive package includes them and their original training records. It creates a fresh output directory and locks source/topology fingerprints. Reports audit raw outcomes, packet ages, integer counts, path-cost bounds and elapsed-time decomposition before plotting. Large raw packet/decision CSVs may also be distributed as lossless `.csv.gz`; pandas reads them directly and the report supports either form.

Possible claim wording must follow the executed effects and simultaneous intervals. Identify the baseline, sensor assumptions, graph family and communication regime for any supported superiority claim. If only uncertain fusion improves outcomes while VALUE-GATE matches SOFT-ALL, attribute the gain to the full fusion/planning method rather than value filtering. If neither improves reliably, report that and revise the mechanism without selecting favorable test settings.

## Preserved prototype and changes before v2 testing

The first prototype evaluated 21,680 held-out episodes and 5,600 controlled episodes. Its 24 corrected primary comparisons supported no delivery superiority. It matched SOFT-ALL in delivery and failed against a single spoofed scout identity in the controlled fixture. Its exact source and results are preserved under `out/adaptive-gate-v1/executed_source` and `revision/adaptive-gate-v1-results`.

The v2 design was changed after that diagnosis: clearance safeguards, a mixed false-block/false-clear channel, identity spoofing in two regimes, thirty episode schedules per test topology/regime, and completely new validation/test graph and episode seeds. V2 settings are reselected only on its new validation data. This is an iterative experimental development process, not a retrospective declaration that v1 succeeded.

## Integration with frozen neural actors

`adaptive_actor.py` runs the admission/clearance mechanism before the existing actor. It projects admitted hazard statements into the original binary belief/age/confidence features, preserves warning anchors until corroboration or expiry, and gives fresher local observations priority. It does not feed untrained continuous-probability features into the old network. MAPPO privileged critic values are never used by the gate. The value proxy remains a public reference risk planner, not the actor's learned action value. Actor-specific message-value learning remains future work.

`run_adaptive_actor_eval.py` evaluates 7,200 new original-topology episodes: twenty existing models, four regimes, thirty schedules, three communication modes. Network weights remain fixed. Thirty-two exploratory algorithm/regime/baseline contrasts use crossed training-seed/episode bootstrap intervals with Bonferroni correction within that secondary family; they are not primary evidence of broad superiority.

The additional 750 clearance-stress episodes inject external-observer confirmation messages; platform motion for these observers is not modeled. They expose the detour from withholding one legitimate clearance, release after two confirmations, and failure against two forged identities. These are mechanism probes, not operational prevalence estimates.

Actual delivery and blocked-entry counts are the primary comparable outcomes. Unexpected-entry counts use each method's belief convention (probability threshold for the soft planner versus binary warning flags for the legacy/frozen actors), so they must not be interpreted as a common calibrated knowledge metric across those representations.
