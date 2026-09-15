# Data dictionary

## Snapshot and accounting scope

The September 15, 2026 snapshot includes one final outcome for each of the 672 problems in the evaluated benchmark revision. The evaluation uses the answer-given `wsolution` variant.

`reviewed_accepted` means the retained record reports verifier success and final fresh-review approval. `statement_false` records the one non-accepted formal statement. The export preserves this distinction.

Resource summaries use only the 671 accepted task records. Costs, runtime, turns, and tokens describe those retained final task records and their retained actor and reviewer calls. Archived or superseded attempts are outside this export. These measurements should not be read as total project expenditure or a complete historical execution trace.

## Per-problem fields

| Field | Meaning |
| --- | --- |
| `problem_id` | Stable upstream problem identifier |
| `year` | Putnam competition year |
| `outcome` | `reviewed_accepted` or `statement_false` |
| `actor_model`, `reviewer_model` | Recorded model family |
| `effort` | Recorded reasoning effort |
| `review_rounds` | Final recorded review round |
| `compilations` | Compiler invocations recorded by the task verifier |
| `submissions` | Submission attempts recorded by the task verifier |
| `actor_turns` | Sum of actor turn counters in retained response records |
| `continuation_requests` | Number of retained actor calls after a continuation request within a review round |
| `elapsed_seconds` | Elapsed time recorded by the final task runner |
| `actor_cost_usd` | Actor cost recorded by the task runner, in USD |
| `reviewer_cost_usd` | Sum of costs in retained reviewer response records, in USD |
| `total_cost_usd` | Actor cost plus reviewer cost |
| `actor_input_tokens`, `reviewer_input_tokens` | Reported uncached input-token counters |
| `actor_cache_creation_input_tokens`, `reviewer_cache_creation_input_tokens` | Reported cache-write input-token counters |
| `actor_cache_read_input_tokens`, `reviewer_cache_read_input_tokens` | Reported cache-read input-token counters |
| `actor_output_tokens`, `reviewer_output_tokens` | Reported output-token counters |
| `input_tokens` | Sum of uncached, cache-write, and cache-read input counters for both roles |
| `output_tokens` | Sum of actor and reviewer output counters |

Token counters are summed once per retained response record. Input totals include repeated cache reads and therefore do not represent unique prompt content. Output counters are used as reported. Separately reported reasoning-token details are not added again.

Actor costs retain the runner's original decimal precision. Reviewer costs are summed from response records. Costs are serialized to nine decimal places for reproducible arithmetic. Extra decimal places do not imply greater billing precision.

The false-statement row preserves its recorded actor cost. Its remaining resource fields are blank because it is outside the accepted-task analysis. Blank values mean unreported here, not zero. Its recorded actor cost is not asserted to cover the complete investigation of that statement.

## Verification metadata

`verification.json` exports only problem IDs, outcomes, proof hashes, controlled verdict labels, and the result of the export-time hash comparison. Hashes use SHA-256 over the exact private proof-file bytes.

`verifier_status` is `solved` for accepted records and `not_accepted` for the false-statement case. `reviewer_verdict` is `APPROVE` for accepted records. Missing hashes and null verdicts in the false-statement case do not imply a verified solution.

These fields summarize retained evidence. They are not independent public certificates of proof correctness.

## Aggregation conventions

The analysis script uses all accepted rows without weighting. It reports the ordinary median and arithmetic mean. The 90th percentile uses the nearest-rank definition. Costs are summed with decimal arithmetic and report statistics are rounded to six decimal places. Display tables use two decimal places. Year counts include the false-statement disposition separately.

No confidence intervals or claims about repeated-run variability are included.
