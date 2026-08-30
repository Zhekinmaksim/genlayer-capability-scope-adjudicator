# Capability Scope Adjudicator

A GenLayer Intelligent Contract for granting capabilities to autonomous agents.
An agent asks for a set of permissions; a resource owner has already committed,
publicly and in advance, to a risk taxonomy and to what happens at each level of
it. The contract places every requested capability in that taxonomy and then
applies the committed policy.

## The design decision this is built around

**The model classifies. The contract decides.**

The judgment never sees the policy. It is asked exactly one thing - which tier
does this capability belong to - and the consequence of each tier was fixed
before anyone knew what would be requested. That separation is not decoration;
it is what makes the primitive worth deploying:

- A compromised or manipulated judgment can move a capability between declared
  tiers. It cannot invent a consequence, and it cannot know which answer would
  be convenient, because the mapping from tier to outcome is not in the prompt.
- The approver commits to consequences in the abstract, before seeing the ask.
  Nobody writes a policy that happens to fit exactly one request.
- A reader can audit the decision without trusting the model at all: the tier
  vector is on chain, the policy is on chain, and the outcome follows from the
  two by table lookup.

Ask a model "should this agent be allowed to transfer funds" and you get an
opinion mixed with a policy the model invented. Ask it "which of these three
tiers does this capability fall into" and you get a placement you can check.

## The problem

Agents are being handed tool access, spending limits and delegated credentials
faster than anyone is writing the authorization layer underneath. The two things
in production today are a human eyeballing a permission list, and a wildcard
grant nobody re-reads. Neither leaves a record of why a capability was allowed,
and neither survives the capability list changing next week.

## Consensus design

**Stage A - deterministic.** The approver publishes the taxonomy and the policy,
hashed. The requester then pins the purpose and the capability set, one shot,
and the params hash is extended to cover all four. Neither half can be revised
after seeing the other. No LLM, no web fetch.

**Stage B - non deterministic.** One bounded choice per capability. The compared
object is:

```json
{"ok": true, "params": "0x...", "tiers": "012", "reason": "", "notes": ["..."]}
```

`tiers` is a fixed-length digit string, one digit per capability. The
equivalence principle compares `ok`, `params`, `tiers` and `reason` only, so the
per-capability reasoning in `notes` is recorded without entering consensus.

The current source declares the comparative callback directly inside `evaluate`
and passes that local function directly to
`gl.eq_principle.prompt_comparative`. There is no callback factory or helper
wrapper between the public method and the non-deterministic call. This is
intentional: the GenVM source check must be able to recognize `exec_prompt` as
reachable from the comparative-consensus block.

**Stage C - deterministic.** Look up each tier in the committed policy table,
build a deny mask and a review mask, aggregate by worst case. No counting, no
thresholds, no judgment left to make.

## Outcomes

| Outcome | Meaning |
| --- | --- |
| `GRANTED` | Every capability landed in an allow tier. |
| `REVIEW_REQUIRED` | No denials, but at least one capability needs sign-off. The mask names which. |
| `DENIED` | At least one capability landed in a deny tier. The mask names which. |
| `UNDETERMINED` | Integrity failure, unreadable judgment, a tier outside the declared range, or a params hash that does not match. |

Worst-case aggregation is deliberate: a request is not partially granted here.
A caller that wants the allowed subset can read the masks and re-request, which
is a new commitment rather than a silent downgrade.

## Adversarial analysis

- **Ordering replaces the countersign.** A countersign is the fix for a party
  that would otherwise choose both halves of a question. Here each party owns
  exactly one half - the approver owns the consequences, the requester owns the
  ask - and each half is one shot. The approver cannot see the request before
  writing the policy; the requester cannot change the policy after writing the
  request.
- **The policy is withheld from the prompt.** Even a successful injection in a
  capability description can only argue about placement, and it has to move the
  same digit across independent validators to settle.
- **The prompt is instructed to classify what a capability permits, not what
  the purpose claims it is for.** A stated benign purpose is not enforceable;
  the capability is. This is written into the prompt because it is the most
  common way a permission review gets talked out of a correct answer.
- **Breadth resolves upward.** A capability spanning two tiers is classified by
  the most it can do.
- **A policy that allows every tier is rejected before hashing.** It is not a
  policy, and a contract applying it would be a rubber stamp with a consensus
  mechanism bolted on.
- **Duplicate tiers and duplicate capabilities are rejected before hashing**, as
  are an empty purpose and an empty capability set.
- **`evaluate` is permissionless and terminal.** Terminality matters especially
  here: a re-runnable permission check is a permission check you retry until it
  says yes.
- **`close`** lets the approver retire a policy nobody has requested against, so
  a requester that never asks cannot pin a stale policy open forever. It is
  blocked the moment a request lands.

## Interface

| Method | Who | Effect |
| --- | --- | --- |
| `open_scope(scope_id, requester, tiers_text, policy_text)` | approver | Publishes the taxonomy (2 to 5 tiers) and one decision per tier: `allow`, `review` or `deny`. Returns the policy hash. |
| `submit_request(scope_id, purpose, capabilities_text, request_hash)` | requester | Pins purpose and capabilities (1 to 12). One shot. Returns the extended params hash. |
| `close(scope_id)` | approver | Retires a policy with no request against it. |
| `evaluate(scope_id)` | anyone | Classifies, applies the policy, settles. Terminal. |
| `status_of`, `outcome_of`, `reason_of` | view | Lifecycle and outcome. |
| `tiers_of`, `policy_of`, `capabilities_of`, `params_hash_of` | view | The frozen halves and the pin. |
| `assignment` | view | The tier vector exactly as it reached consensus. |
| `classified` | view | Each capability next to its tier and the resulting decision. |
| `denied_capabilities`, `review_capabilities` | view | The masks, resolved to text. |
| `tier_notes` | view | Per capability reasoning. Audit only, never consensus. |
| `scope_ids` | view | Enumerates scopes. |

### Hash convention

All hashes are `keccak256` over canonical text: line endings normalised to `\n`,
trailing whitespace stripped per line, ends stripped, empty lines dropped, each
line collapsed to single spaces. The policy hash covers tiers then decisions;
the request hash covers purpose then capabilities; the final params hash covers
all four in that order.

## Cost

One LLM call per `evaluate`, replicated per validator. No web fetch. Capabilities
cap at 12, tiers at 5.

## Testing

```
python3 sim/check.py
```

Seven cases, all passing. The one to read is case 2: an identical tier vector
under a different committed policy produces a different outcome, which is the
separation the whole contract exists to enforce.

This does **not** test consensus or the hosted GenVM source linter - that is
what hosted Studio exercises, and `TEST_PLAN.md` records what was run there.
Before submission, the Explorer source must match the GitHub commit exactly and
must still show the inline `evaluate` callback form described above. Full live
LLM classification is not simulated offline.

## Layout

```
contract.py     the Intelligent Contract
README.md       this file
TEST_PLAN.md    seven cases, expected results, Studio notes
SUBMISSION.md   portal-ready short notes and evidence checklist
sim/            offline stand-in for the SDK plus the seven-case check
```

Solo project. MIT licensed.
