# Portal submission - Capability Scope Adjudicator

Use this only after the hosted Studio deploy succeeds and the Explorer source
matches the GitHub commit exactly.

## Title

Capability Scope Adjudicator

## Notes under 1000 chars

```text
GenLayer IC for granting agent capabilities without letting the model invent the policy.

Consensus boundary:
- approver freezes risk tiers and tier outcomes first
- requester then pins purpose and capabilities one-shot
- LLM only classifies each capability into a tier
- validators compare params hash, fixed-length tier vector and reason
- policy lookup and worst-case aggregation are deterministic

The policy is withheld from the prompt, so injection can only try to move a tier digit; it cannot know or change the consequence. A policy that allows every tier is rejected before hashing. No inference from silence: no request means no evaluation.

GenVM-lint structure fixed: exec_prompt is inside the inline callback passed directly to prompt_comparative. No helper/factory callback.

Offline tests 7/7. Studio deploy/evidence to be filled tomorrow. Method surface to verify: open_scope/submit_request/close/evaluate.
```

## Links / evidence

- GitHub: https://github.com/Zhekinmaksim/genlayer-capability-scope-adjudicator
- Explorer contract: 0x...
- Deploy tx: 0x...
- Smoke tx: 0x...
- Commit: ...
- Studio date: 2026-08-31
- Explorer source contains inline `evaluate` callback and no `_judgment_fn`
- `python3 sim/check.py`: 7/7 pass

