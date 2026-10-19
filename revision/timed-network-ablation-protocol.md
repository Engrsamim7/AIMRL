# Matched admission ablation

Specified before this ablation is executed. The initial network pilot suggests large transmission savings from the VALUE package. That package includes admission, priority and queue coalescing; comparing it only with FIFO does not isolate filtering. This follow-up addresses the confound without changing the fitted model, selecting favorable cells or tuning any parameter.

Run VALUE_PRIORITY, the same VALUE sender with threshold zero, on all 972 pilot schedules/cells and all 6,912 surface schedules/cells. Its routing interpreter, source observations, public value score, priority, coalescing, packet capacity and safeguards are identical to VALUE. Only the admission threshold changes from the locked 0.05 to zero. Every score is nonnegative, so zero retains every offered packet while still coalescing superseded pending updates. There is no trained new estimator or new routing actor.

The controlled component path is AGE_ALL -> LATEST (coalescing), LATEST -> VALUE_PRIORITY (value scheduling), VALUE_PRIORITY -> VALUE (admission). WARN_PRIORITY remains a strong simple scheduling comparator; RAW_ALL retains its observed pilot advantage rather than being omitted. These are package/component effects under closed-loop routing, not isolated-message causal FIR.

The ablation reuses the existing schedules to obtain paired descriptive component comparisons. It adds 7,884 method episodes and 63,072 convoy records; it is not an untouched confirmation. The whole development evidence becomes 63,072 method episodes / 504,576 convoy records across the pilot and response surface. Report every condition and adverse result; do not attribute priority benefits to admission if the matched admission contrast does not support that interpretation.
