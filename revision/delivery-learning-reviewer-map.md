# Delivery-primary revision: reviewer concerns and remaining gaps

This map describes the new timed-network learned-routing experiment. Earlier
GNN, MAPPO and reactive-adversary experiments are separate implementations; their
features and conclusions must not be attributed to this experiment.

| Concern | Current implementation and evidence | Remaining limitation |
|---|---|---|
| Hub-only state and information-insensitive routing | Twenty-six public/local belief, history, timing and graph-derived action features; a real shared Double-DQN optimizer and saved training/checkpoint validation records. | Approximate history summaries, not a sufficient Markov state; a bounded planning-prior residual, not a GNN or MAPPO. A selected initial checkpoint is disclosed. |
| Ineffective hazards and inconsistent costs | Closures prevent entry; inspections, travel, service, FIFO waiting and holding consume time; deadlines determine primary success. Raw convoy records balance elapsed components. Same-time sensor samples preserve direct encounter evidence; a regression exercises noisy zero-inspection termination. | Synthetic closures, model time units, no destruction or operational calibration. Historical timed-network source is preserved; current actors are retrained after the evidence-ordering correction. |
| Why would a gate help delivery? | Paired complete-state admit/reject packet continuations measure the actual fleet on-time effect under a frozen actor. Both fleet branches are saved; factual continuations reproduce uninterrupted outcomes. | Training opportunities use a buffer-only actor-change proxy. Labels are contextual and limited to sampled opportunities; they do not prove a universal mechanism. |
| Static freshness and delayed information | A fitted report interpreter uses age/confidence; local accepted-report change summaries enter routing. FIXED_RX rechecks age at use, and delayed/lost/miscalibrated/rapid/persistent conditions are retained. | Report calibration is inherited from a separate synthetic training phase; uncertainty is not calibrated for deployment. |
| Filtering versus response/scheduling confounds | ALL and LEARN use exactly the same frozen actor, report interpreter and zero-threshold value transport. KEEP_ONE matches rejection authority; KEEP and two planner references remain. | Baselines are not each independently retrained under their own receiver. Gate fitting adds compute. This is a controlled receiver comparison, not a completed matched-training algorithm benchmark. |
| Causal attribution and denominators | LEARN permits one fleet rejection, then uses ALL. Paired held-out LEARN/ALL outcomes identify that rejected packet's complete downstream delivery effect. Non-rejection episodes must tie. | One shared public token requires coordination; these effects are not all-transmission FIR, and no endogenous adversary is included. |
| Tiny graph and replication | Eight routing seeds; six independently parameterized graph instances at 19/51/131 nodes; new schedules and 131-node transfer beyond training sizes. | Adjacency templates are fixed within each size; these are not six independent topologies. Only two weighted instances per size. The fixed training budget does not establish convergence or broad scaling. |
| Selection and statistical support | Training, actor validation, packet labels, gate validation and test use separate namespaces. Model/settings hashes lock before test. Three primary paired contrasts have corrected bounds and a specified one-point practical target. | The program has earlier development experiments. This is a prospectively specified simulation study, not external preregistration or independent replication. Bootstrap uncertainty remains conditional on the synthetic design. |
| Reproducibility and accessible figures | Source, original uploads, model candidates, fitted models, raw records, tables, PDF/PNG figures and offline HTML are packaged together with SHA-256 integrity checks. | Manuscript equations, numerical tables and response letter still need revision against these measured outcomes. |

Read [the findings](delivery-learning-findings.md),
[the protocol](delivery-learning-protocol.md) and
[the result tables](delivery-learning-results/README.md) together. A passing
implementation audit does not by itself support the paper's superiority claim.
