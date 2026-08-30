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

Offline tests 7/7. Studio deploy finalized; Explorer source matches GitHub source. Method surface verified: open_scope/submit_request/close/evaluate.
```

## Links / evidence

- GitHub: https://github.com/Zhekinmaksim/genlayer-capability-scope-adjudicator
- Explorer contract: https://explorer-studio.genlayer.com/address/0xcD6B7df7D492d5f19d1030c2de35202118CC9A28
- Deploy tx: https://explorer-studio.genlayer.com/tx/0xd6e71401496ef0fcc8d580ed39d4a5ff0773ff055bcb088e1ad2a6b91080f11d
- Smoke tx: not run; deploy and method-surface verification only
- Contract source commit: d09baf12bbcb080ec1c62af58395e6706c5bcfb9
- Studio date: 2026-08-30
- Explorer source contains inline `evaluate` callback and no `_judgment_fn`
- Explorer `contract_code` contains the GitHub `contract.py` exactly
- `python3 sim/check.py`: 7/7 pass
