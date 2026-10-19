# Manuscript claim after the matched-training study — 19 October 2026

## Decision

**The new study does not establish an added delivery benefit from the learned message-value component over identical safeguards alone.** This is the predeclared primary result for both DQN and MAPPO. It is not proof that the methods are equivalent, that learning can never help, or that every adaptive gate fails.

| Algorithm | Safeguards only, delivery | Combined, delivery | Combined minus safeguards | Corrected interval, percentage points |
|---|---:|---:|---:|---:|
| DQN | 82.9805% | 83.2402% | +0.2598 pp | −0.4271 to +1.1149 |
| MAPPO | 79.1543% | 78.8594% | −0.2949 pp | −3.7354 to +3.6384 |

These means equally weight all eight conditions, including controls. Each algorithm has eight paired training seeds; each final actor receives 300 common ALL warmup and 300 arm-specific adaptation episodes. SAFE and COMBINED share exactly the same constraints. SAFE is a new factorial baseline and differs from the previous SAFE-ALL implementation. The 64 final checkpoints are not 64 independent initializations.

## Supported bounded result

The combination improves DQN delivery over ALL in two specified short-delay corruption conditions after the declared correction:

- Familiar rate 6, delay 1, honest-message loss 0.1: ALL **69.7031%**, COMBINED **81.1250%**; difference **+11.4219 pp**, interval **+5.2369 to +18.0262 pp**. SAFE already achieves **80.8281%**.
- Unseen rate 8, delay 1, honest-message loss 0.2: ALL **66.0000%**, COMBINED **74.8438%**; difference **+8.8438 pp**, interval **+3.3594 to +14.6250 pp**. SAFE achieves **73.5938%**.

COMBINED also outperforms VALUE without safeguards in four DQN conditions and two MAPPO conditions. Across the 50 declared new delivery contrasts, eight support a benefit and none support a disadvantage. **No COMBINED-versus-SAFE comparison supports superiority**, either pooled or by individual condition. No absence of detected harm establishes noninferiority.

A suitable results statement is:

> In a prospective matched-adaptation study with eight paired training seeds per algorithm, a safeguarded message-value gate improved DQN delivery over ungated communication in two specified short-delay corruption conditions, including an unseen higher-rate corruption setting. Its incremental delivery advantage over identical conservative safeguards was not established for DQN or MAPPO. These results support bounded communication resilience and the importance of safeguards, while leaving the added value of this learned component unresolved.

Do not use “generally superior,” “best across all baselines,” “learned gating is necessary,” “every KPI improves,” or a MAPPO-over-ALL superiority claim based on these new data. FRC was not separately retrained in this four-arm study; its earlier frozen-model results must be identified as such.

## Mechanism, costs and limitations

Holding the COMBINED-trained actor fixed and swapping SAFE versus COMBINED filtering gives descriptive pooled differences of **+0.1484 pp for DQN** and **+0.0703 pp for MAPPO** on separate layouts/tapes. These small conditional effects do not establish a new benefit and may depend on the actor's familiarity with its training gate. They must not replace the confirmatory primary comparison.

Seed variation is particularly large for MAPPO. The learned value model was fitted to the frozen warmup actor and held fixed while routing adapted; its values can become stale. This is a plausible limitation, not a proven explanation for the result. A fresh study would be required to test actor-specific value refresh or joint adaptation. More seeds would improve precision but cannot be assumed to reveal a positive effect.

All arms have matched routing-episode budgets and evaluation schedules, but learned arms additionally use auxiliary causal replay labels. Across sixteen actor/seed pairs, 2,560 factual auxiliary episodes generated 18,518 packet interventions and 37,036 replay branches. Total computational cost is not matched. Full and follower delivery, defined utility, common-survivor costs/time, packet admission and larger-layout breakdowns are retained. Survivor costs are conditional; filtering admissions is not transmitted-bandwidth reduction.

Final testing uses sixteen fresh three/four-fork layouts (four-fork size absent from training), eight conditions and ten environment tapes per graph/case, shared across training seeds and methods. Forged targets and payloads are independent of live hazards; confidence matches honest-message confidence. Identities are unauthenticated, and honest-only transport loss is distinct from receiver-side forged injection. This is a structured mechanism benchmark, not operational logistics validation.

Each new interval uses 200,000 paired graph/episode-clustered, training-seed-crossed bootstrap draws and the conservative 248-test threshold (50 current plus 198 earlier comparisons). Historical published intervals remain unchanged; no revised simultaneous-coverage claim is made for all historical tables. The new primary endpoint and all secondary contrasts are reported regardless of outcome.

## Practical manuscript direction

Use the safeguard mechanism and the named resilience results as established evidence. Present the learned component as an evaluated extension whose incremental benefit remains unestablished. Keep the earlier frozen-model study, unconstrained failures and current null results distinct. Do not select a favorable case or change the primary endpoint after seeing these outcomes. Any stronger learned-component claim requires a new protocol and fresh held-out confirmation.

See [the complete results](matched-gate-results/README.md), [the prospective protocol](matched-gate-protocol.md), and [the figure guide](matched-gate-figure-guide.md).
