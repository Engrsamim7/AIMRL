# Frozen-model development response surface

The initial timed-network development pilot exposed meaningful encounters and radio savings, but many easy cells still had 100% on-time delivery. This follow-up varies physical constraints systematically, while preserving the pilot results and freezing its calibration model and VALUE threshold. It is development evidence, not an untouched confirmation or a search for favorable cells.

Before running, specify the full cross-product:

- Deadline ratio: 1.1, 1.35, 1.75, 2.5 times public free-flow-service lower bound.
- Closure duration: 0.25, 1, 4 times median reference mission duration.
- Unique closure fraction/budget: 0.1 or 0.3 of directed edges.
- Scout lead: 0 or 2 median-edge travel units.
- Inspection delay: 0 or 1 times attempted edge nominal traversal time.
- Packet serialization duration: 0, 0.25 or 1 median-edge unit.
- Sizes: 19, 51 and 131 nodes; two new graph instances at each size.
- Four new exogenous schedules per cell; all seven methods.

This gives 96 physical cases, 864 size/case/channel cells, 48,384 method episodes and 387,072 convoy records. All cells are retained. New graph seeds are 720010+graph index, and schedule namespace is 720000000+graph*1000000+case*100+episode. The initial pilot uses 712000000+ and remains separate. Public model/threshold selection uses only the parent pilot's training/validation data; the surface has no parameter selection.

The endpoint remains on-time delivery, with whole-horizon delivery, time, path cost, integer encounters, completed and attempted frame bytes, partial-frame airtime, queue age and actual peer-induced route changes separate. Compare VALUE against RAW_ALL, AGE_ALL, LATEST and WARN_PRIORITY, not only a weak comparator. Describe every adverse condition and show deadline/persistence/capacity response surfaces. This is a structured sensitivity study with a fitted planning interpreter and heuristic sender gate; it does not yet supply trained MARL comparisons, confidence-corruption theory, causal packet FIR or operational validation.
