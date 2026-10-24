# Mathematical diagnosis and a delivery-first redesign

This is an analysis of the completed v3 experiment, followed by a proposed new
design. It contains no new superiority result. The existing test outcomes are now
development evidence for any redesign; a new confirmation requires fresh data.

## 1. Keep the correct objective

For N convoys with arrival times T_i and deadlines D_i, use

$$Y=\frac{1}{N}\sum_{i=1}^{N}\mathbf{1}\{T_i\leq D_i\},\qquad
J(\pi,g)=\mathbb E[Y].$$

Censored/non-arriving convoys have indicator zero. By linearity,
J=(1/N) sum_i P(T_i<=D_i); no independence between convoy outcomes is needed.
The current reward already targets this quantity. Adding a bandwidth reward
would change the objective and is not the proposed repair.

## 2. The observed loss has an exact decomposition

There are M=3,456 paired LEARN/ALL episodes, with N=8 convoys each. For an episode
where the gate rejects a packet, define G=Y_reject-Y_admit. There is at most one
rejection, both methods share the same prefix, and ALL follows afterward. Thus
G is that packet's complete downstream fleet effect under the frozen actor.
Episodes without a rejection exactly tie.

Let q be the rejection-episode frequency, p_+ and p_- the frequencies of positive
and negative G among rejections, and mu_+, mu_- their positive mean magnitudes.
The following empirical identity is exact:

$$\widehat{\Delta J}
=q\,\overline G_{\mathrm{rejected}}
=q(p_+\mu_+-p_-\mu_-).$$

The rejected packets recover **147** on-time convoy arrivals but lose **182**:

$$\widehat{\Delta J}
=\frac{147-182}{3456\times8}
=-0.001265914\ldots.$$

This is -0.126591 percentage points: +0.531684 points recovered and -0.658275
points lost. There are 130 helpful, 153 harmful and 1,284 zero-delivery-effect
rejections. Counts alone omit unequal effect sizes; the objective depends on
their magnitudes too.

At the same observed activity q=1567/3456, an overall one-point gain would require

$$\mathbb E[G\mid\mathrm{reject}]\geq\frac{0.01}{q}
\approx0.022055,$$

or +2.2055 percentage points per rejected episode. The observed conditional
mean is -0.2792 points. This is a design diagnostic holding activity fixed, not
a prediction: a different gate changes which episodes it selects and hence q.

## 3. The predictor has too little rare-effect evidence

Of 2,464 actor-changing training labels, 103 show harmful admission, 102 show
helpful admission and 2,259 have no delivery effect. Individual gate estimators
have only **3 to 34 harmful-admission examples**, before allowing for correlated
labels from the same episode. Ninety-six trees do not create additional evidence.

There is also a concrete estimator-design issue. The current multi-output forest
fits [delta, 1(delta>0), 1(delta<0)] using an equally averaged squared-error
splitting criterion. Delta is a fleet fraction, while the indicators have unit
scale. On each complete per-seed fit sample, the value output contributes only
**1.60–2.56% of the sum of target variances**. Actual bootstrap-node contributions
vary; this is not an exact percentage of every split's gain. It exposes an
implicit scale weighting, not proof of the observed failure's cause.

A focused first ablation is to fit scalar expected delivery value separately
from harm/benefit classifiers, or explicitly declare and validate task scaling.
Changing value units from fleet fraction to convoy count multiplies its squared
error by64 for N=8, illustrating why an unexamined shared loss is unit-dependent.
Do not assume rescaling alone will improve delivery; compare under identical
data, actor and validation budgets. A useful diagnostic factorization is

$$\mathbb E[G\mid x]
=p_{\ne0}(x)\{r(x)\mu_+(x)-[1-r(x)]\mu_-(x)\},$$

where p_ne0 is the probability of a nonzero effect, r is the beneficial fraction
conditional on such an effect, and mu_+,mu_- are its positive/negative mean
magnitudes. The existing forest already attempts mean-value prediction; this
factorization makes errors auditable, rather than defining a magically new
objective or guaranteeing a better estimator.

The target-unit sensitivity was tested as a **retrospective development
ablation**, holding the labels, actors, tree seeds/hyperparameters, thresholds
and physical validation contexts fixed. The value target was multiplied by 8
for fitting, then its predicted mean/dispersion divided by 8 before decisions.
All eight original estimators were first reproduced exactly. At the existing
setting 1, on-time validation delivery changed from 57.2266% to 57.0313%
(-0.1953 percentage points). All five settings are retained in the output;
none showed an observed gain. No new test episodes were run. This does not
establish inferiority statistically, but provides no observed support for
rescaling alone as the remedy. Separate value/risk estimators remain untested.

On selected test rejections, mean predicted admission-minus-rejection value is
-0.9003 percentage points, whereas the realized paired mean is +0.2792 points.
Average predicted rejection-harm frequency is 2.1456%; observed harm frequency
is 9.7639%. These are selected-case aggregate comparisons, not estimates of a
global false-rejection rate or conditional calibration at each state. The
observed aggregate harm is still below the rule's nominal 10% threshold; that
does not establish a calibrated risk guarantee.

Each paired label is a realized effect under one exogenous future, not the
conditional expected effect observable at decision time. Some helpful and
harmful cases may be indistinguishable from the permitted history. Removing
all 182 realized losses is not promised. Independent training histories, or a
verified sampler of posterior-consistent future continuations, are needed to
estimate expected effects and their uncertainty; arbitrary new futures cannot
contradict observations already in the saved history.

Training needs more independent, consequential examples and better coverage of
the intended deployment distribution. Sample observable urgency, contradiction,
age, regime and congestion strata; preserve benign/zero-effect controls and
record inclusion probabilities. Outcome-balanced sampling cannot be used as
deployment harm probabilities without correcting the sampling shift. Keep all
labels from an episode in one split. More branches of the identical saved
future produce identical outcomes, not independent evidence.

The current buffer-only action probe also holds accepted-report history fixed,
although actual admission changes that history. Its labels use correct full
admission, but its eligibility screen and features can miss later effects.
Replace the screen with full, restored admission-state probes and sample
packets whose benefit appears at later routing decisions. Do not require an
immediate next-hop change as the definition of usefulness.

## 4. Deadline probability differs from expected travel time

The planning prior ranks expected path time. The learned network can modify
this ranking, but its action residual is bounded. For the current implementation,

$$Q_\theta(h,a)=C_\theta(h)-0.1\,c_h(a)
 +0.05\tanh f_\theta(h,a),$$

where c_h(a) is expected route cost divided by the reference route time and
C_theta(h) is identical across candidate actions. Therefore

$$Q_\theta(h,a)-Q_\theta(h,b)
=-0.1[c_h(a)-c_h(b)]
+0.05[\tanh f_\theta(h,a)-\tanh f_\theta(h,b)].$$

The learned difference cannot exceed 0.1 in magnitude. If c_h(a)-c_h(b)>=1,
action a cannot outrank b, regardless of training. This is a representational
restriction; its frequency in actual decision states has not been measured,
so it is not established as the cause of the observed gate loss.

For example, with deadline 8, route A always takes 9, and route B takes 7 with
probability 0.8 or 20 otherwise. E[T_A]=9 < E[T_B]=9.6, but their on-time
probabilities are 0 and 0.8. Minimizing mean time is not equivalent to maximizing
deadline success.

A candidate repair is a bounded deadline-return critic estimating

$$Q^{\pi,g}(h,a)=\mathbb E[Y\mid h,a,\pi,g]\in [0,1],$$

or arrival-time distributions evaluated at deadlines, with complete fleet
externalities retained. For the current potential shaping, the corresponding
shaped critic is -Phi(h)+q_theta(h,a), with q_theta in [0,1]. This bounds return
without imposing a fixed expected-time ordering. Warm-start routing from the
planner, then assess an annealed prior and stable target/return fitting on
development data. This architecture is proposed, not yet implemented or proven
better. Monte Carlo returns from an old behavior policy are not automatically
unbiased values for a newly changed target policy.

## 5. Repair information representation before claiming rejection helps

The current ALL baseline stores the latest peer report per edge, with small
history summaries. It does not retain a full uncertainty/provenance history.
Keep observation time, source/provenance, relevant contradictory evidence and
uncertainty; protect direct encounter evidence and handle genuine reopening.

A posterior update, with H_t denoting history before incorporating m, has the form

$$b_t^+=\frac{L(m\mid X_t=1,H_t)b_t^-}
 {L(m\mid X_t=1,H_t)b_t^-+L(m\mid X_t=0,H_t)(1-b_t^-)}.$$

Here X_t is road state and the likelihood must marginalize the report's age,
latent persistence/recovery regime and source reliability. It is not simply the
sender's claimed confidence. Out-of-sequence observations require consistent
history handling. Correlated retransmissions must not count as independent
corroboration. A homogeneous Markov aging formula is not exact for the present
single-closure, finite-duration generator without appropriate state augmentation.

There is an essential limit to the hypothesis: if an ALL policy receives and
retains every report at the same times and costs, and can ignore any report,
it can emulate any receiving gate. Its optimal policy value is at least the
best gated value. Rejection does not create information. This does not rule out
a gate improving a finite learned algorithm, compressed memory, or a constrained
communication system. It rules out a universal information-removal advantage.
The current destructive latest-report representation does not satisfy the
full-history assumption of that comparison.

Temporary quarantine remains a candidate control, not an automatic solution:
it can preserve evidence or permit corroboration, but also delays useful
clearances. A fair ALL baseline must receive the same usable history and
reliability inputs and may learn to ignore suspect reports.

## 6. A more credible delivery mechanism acts before radio service

The current learned gate operates at receive(), after a packet used the radio.
Rejecting it cannot undo its service time or immediately advance other queued
packets. It can change later traffic through routing feedback, but cannot
directly solve the current channel-allocation problem.

Propose a communication controller with actions transmit, defer/quarantine and
discard, applied before committing non-preemptive radio service. For packet
size L_m and rate C, service time is tau_m=L_m/C. A necessary window constraint
is sum_m tau_m z_m <= W; release times, serialization and usefulness deadlines
also constrain feasibility. Keep J=E[Y] as the objective: airtime is a physical
constraint, not a replacement reward.

For visible history h, queue q and legal alternative u0, estimate

$$A^{g_0}(h,q,u)
=\mathbb E[Y\mid h,q,u,\pi,g_0]
 -\mathbb E[Y\mid h,q,u_0,\pi,g_0].$$

Labels must branch the complete queue and fleet before transmission, preserve
the same exogenous physical/sensor/loss fields across actions, and include
delays imposed on other packets. A public detour score or |belief change| is
not this quantity. Value/airtime ranking is a useful candidate heuristic but
is not generally optimal for indivisible, interacting packets.

There is a simple physical opportunity: service time tau, low-value packet L
available at 0, urgent packet H appearing at epsilon in(0,tau), and a routing
commitment d satisfying epsilon+tau < d < 2tau. Sending L immediately delays H
past the commitment; deferring L allows H to arrive in time. If timely H enables
an on-time detour for one convoy otherwise late, the episode improves by 1/N.
This constructed example establishes a mechanism, not a measured average gain
or superiority over a scheduler that also permits idling and deferral. A deployed
controller cannot know H will arrive; it must estimate that possibility from
legal history. A future-aware oracle is only a diagnostic, never the controller.

Sender estimates may use only information actually available there: own
observations, public manifests and received telemetry. Exact remote convoy
positions and future road states are prohibited. Any added telemetry consumes
the same modeled channel and may be delayed/lost. Offline full-state teachers
may label returns, but their privileged inputs cannot enter the deployed gate.

## 7. The mathematical condition for policy improvement

Fix routing policy pi for a gate-attribution comparison. Let H_t include the
relevant history, time, queue and remaining intervention budget. For reference
gate g0, define

$$A^{g_0}(H_t,u)=Q^{g_0}(H_t,u)-V^{g_0}(H_t).$$

In the same finite-horizon model with the same initial distribution, the
undiscounted performance-difference identity is

$$J(\pi,g)-J(\pi,g_0)
=\mathbb E_{\pi,g}\left[\sum_t A^{g_0}(H_t,u_t)\right].$$

It follows by telescoping V^{g0} across transitions, with terminal reward Y.
If each chosen deviation has nonnegative true advantage on histories reached
by g, and there is strictly positive total expected advantage, the new gate
strictly improves delivery. These are conditions, not properties already
established for our learned model.

If a valid error bound |Ahat-A|<=e is available at those histories, choosing a
deviation only when Ahat-e>0 is a sufficient local condition. Ensemble standard
deviation does not establish such a bound. Marginal conformal coverage for an
individual return is also not a uniform conditional-mean or adaptive-policy
safety guarantee.

The old isolated ALL-continuation labels are valid one-step baseline advantages;
they are not mathematically invalid. But they do not themselves solve the
optimal timing/budget problem or cover states reached after several deviations.
For a controller with deferral and multiple interventions, either learn its
remaining-budget Q-values under a specified continuation policy or perform
policy improvement using baseline advantages on the new policy's state
distribution. Refresh data as policies change; do not add fixed-trajectory
single-packet effects as if messages were independent.

## 8. Validate the policy rather than trusting model scores

The old gate selection used 192 actor/environment rows per setting, but these
share only 24 physical validation contexts and two weighted graphs. They are
not 192 independent new environments. A 0.326-point validation selection advantage
did not generalize.

For a fixed candidate g and paired independent evaluation units, let
D_j=Y_j^g-Y_j^baseline in [-1,1]. Under that independence assumption, a conservative
one-sided simultaneous bound for K fixed candidates is

$$\mathrm{LCB}_g=\overline D_g-
\sqrt{\frac{2\log(K/\alpha)}{n}}.$$

This is the bounded-difference Hoeffding/union-bound construction, not the
interval used for the existing study. It can be very loose. Correlated actor
rows cannot be substituted for independent n. For new-graph generalization,
training-seed and graph uncertainty also require appropriate replication.
Use variance-aware paired/cluster inference and development-based power
planning; keep candidate selection separate from final confirmation. If
validation cannot establish an improvement, retaining the reference is a
legitimate outcome, not evidence of superiority.

## 9. Concrete next sequence and fair comparisons

1. Complete this diagnostic, test separate value/risk estimation as a controlled
   development ablation, and preserve all old data. No parameter is selected
   using the completed test to relabel it as a new confirmation.
2. Implement full admission/history probes and richer belief/provenance storage.
   Verify reopening, correlated evidence, zero-inspection progress and hidden
   truth isolation. Give the strongest ALL router the same information.
3. Implement pre-transmission paired interventions and measure whether timely
   delivery opportunity exists under physically justified congestion. Keep
   unlimited-channel, clean, persistent and misleading-clearance controls.
   Any hostile report injection needs a defined budget/provenance model whose
   hidden attack labels are unavailable to all deployed policies.
4. Compare deadline-return routing against the current bounded residual under
   matched budgets. Collect sufficient independent consequential labels and
   validate value/risk on representative policy rollouts.
5. Train routing and communication alternately with refreshed labels, then freeze
   both. Also run a common-frozen-router comparison to isolate communication.
   Report auxiliary gate-labeling interactions and compute explicitly; provide
   matched-budget baselines rather than hiding this extra resource.
6. Keep FIFO/age/warning priorities, learned priority without admission, the same
   learned priority plus admission, and equally informed defer/corroboration
   controls. This separates scheduling, memory, filtering and routing effects.
7. Before a fresh test, specify the operating domain, practical delivery target,
   primary baselines, independent seeds/weighted graphs, uncertainty correction
   and adverse-case reporting. Finite-capacity conditions may define the intended
   domain if justified prospectively; an adverse test cell cannot be removed
   afterward to manufacture superiority.

The target is superiority over named, well-trained baselines in that declared
domain. No equation proves that a proposed learned estimator will satisfy the
conditions without evidence, and no benchmark establishes universal superiority.

## Reproduce this analysis

Run from root with the existing pinned environment:

```bash
MPLCONFIGDIR=/tmp/aimrl-mpl XDG_CACHE_HOME=/tmp/aimrl-cache \
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
.venv/bin/python simulator/analyze_delivery_gap.py
```

The script reads existing result tables, checks the exact gain/loss identity,
and writes source hashes, per-seed diagnostics and a descriptive two-panel
figure. If the saved validation rollouts are available, it also reports their
shared-environment clustering. It changes neither the simulator nor any trained
model. [Numeric audit](delivery-mathematical-analysis/analysis.json),
[figure PDF](delivery-mathematical-analysis/delivery_gap_decomposition.pdf),
[original completed findings](delivery-learning-findings.md).

The controlled development ablation is implemented in
`simulator/run_delivery_value_scale_ablation.py`. Its
[paired table](delivery-mathematical-analysis/value_scale_development_ablation.csv)
and verification record distinguish these additional validation rollouts from
the original test. Reproduce it with a fresh output folder:

```bash
.venv/bin/python simulator/run_delivery_value_scale_ablation.py \
  --output simulator/out/delivery-value-scale-reproduction \
  --report revision/delivery-value-scale-reproduction
```
