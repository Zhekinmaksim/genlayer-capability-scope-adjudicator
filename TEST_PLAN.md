# Test plan - Capability Scope Adjudicator

Seven cases, all runnable offline against `sim/check.py` and again in hosted
Studio. The tier vector is injected directly offline, which is deliberate: the
contract's own logic is the policy lookup, and that is fully deterministic.

Fixture: three tiers (`read only`, `scoped write`, `custodial`), policy
`allow / review / deny`, and three requested capabilities that map to one tier
each.

## 1. Denied by the committed policy

Tier vector `012`.

Expected: `DENIED`. `denied_capabilities` returns the treasury transfer,
`review_capabilities` returns the scoped write, `classified` returns three lines
each showing capability, tier and resulting decision. `assignment` returns `012`.

## 2. Same tiers, different policy, different outcome

Identical tier vector `012`, but the committed policy is
`allow / allow / review`.

Expected: `REVIEW_REQUIRED`, no denials.

This is the case worth reading twice. The judgment did not change at all. The
outcome changed because the policy changed, and the policy was committed before
the request existed. That is the separation the contract is built to enforce,
and it is why the model is never shown the policy.

## 3. Fully granted

Tier vector `000`.

Expected: `GRANTED`, both masks empty.

## 4. Tier out of range and provider failure

A tier index of 7 against a three tier taxonomy -> `UNDETERMINED` with reason
`TIER_OUT_OF_RANGE`. `exec_prompt` raising -> `UNDETERMINED` with reason
`JUDGMENT_UNAVAILABLE`.

Neither becomes `GRANTED`. An unreadable classification must never fall through
to a permission.

## 5. Ordering and identity enforcement

- the approver tries to submit the request it will judge -> `NOT_REQUESTER`
- a third party tries to submit -> `NOT_REQUESTER`
- the requester submits with a wrong hash -> `HASH_MISMATCH`
- `evaluate` before any request -> `NOT_REQUESTED_OR_SETTLED`

The first one is the point: whoever writes the consequences must not also write
the ask.

## 6. One shot request and terminal verdict

Submitting a second, narrower capability set after the first -> 
`ALREADY_REQUESTED_OR_CLOSED`. Evaluating twice -> `NOT_REQUESTED_OR_SETTLED`.
`close` after a request has landed -> `ALREADY_REQUESTED_OR_CLOSED`.

A permission check that can be re-run is a permission check you retry until it
says yes, and a request that can be edited after a first look is a request you
tune until it passes.

## 7. Policy and taxonomy guards

- a policy of `allow / allow / allow` -> `POLICY_ALLOWS_EVERYTHING`
- two decisions for three tiers -> `POLICY_COUNT_MISMATCH`
- a decision word that is not allow, review or deny -> `UNKNOWN_DECISION`
- one tier -> `TOO_FEW_TIERS`
- `read only` and `READ ONLY` in one taxonomy -> `DUPLICATE_TIER`
- whitespace-only purpose -> `EMPTY_PURPOSE`
- duplicated capability lines -> `DUPLICATE_CAPABILITY`
- `close` before any request -> `CLOSED`

None of these reaches the LLM.

---

## Studio verification

Run in hosted Studio before submission:

- deploy and confirm the deploy transaction finalises
- confirm the submitted source is lint-clean in current GenVM, with the
  `exec_prompt` call recognized inside the inline comparative-consensus callback
  passed to `prompt_comparative`
- confirm Explorer source matches the GitHub commit exactly, not an older
  helper-based version
- `open_scope` smoke transaction, confirming the returned policy hash and the
  stored taxonomy and decisions
- `submit_request` from the designated agent address, and from a second address
  to confirm `NOT_REQUESTER` reverts on chain
- the case 7 guards, in particular `POLICY_ALLOWS_EVERYTHING`
- a live `evaluate`, recording the tier vector and the outcome as returned

Two funded accounts are needed, one approver and one agent. State plainly which
cases were run live, which were only exercised offline, and the transaction
hashes. Full live LLM classification across a full validator set is not
something I can force from Studio, so I say so rather than implying otherwise.
