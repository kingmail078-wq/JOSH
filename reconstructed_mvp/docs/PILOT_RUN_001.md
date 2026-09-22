# Pilot Run 001 — The Last Point on the Map

## Outcome

**PASS — workflow boundary validated.**

Pilot Run 001 tested the reconstructed Phase 0–2 workflow with `ART-LIGHTHOUSE-001` without claiming a visual completion judgment. Current artwork images were not part of this run.

## Intake

- Artwork ID: `ART-LIGHTHOUSE-001`
- Canonical title in retrieved record: `The Last Point on the Map`
- Preserved unresolved alias: `Lighthouse Map`
- Starting version: `4`
- Starting status: `active`
- Primary Lab: `perspective_environments`
- Protected constraint: `Protect the lighthouse lamp as the brightest point`
- Request: prepare a bounded Finish Cycle inventory review focused on spatial hierarchy and lighting values without changing ownership or declaring completion.

## Routing

- Primary Lab retained: `perspective_environments`
- Consultant selected: `lighting_values`
- Total activated Labs: 2
- Other Labs activated: none
- Routing reason: canonical ownership plus request relevance

## Findings

The deterministic pilot specialists produced proposal-labeled guidance only:

1. Protect the spatial hierarchy; correct the largest depth or convergence problem before surface detail.
2. Protect the focal light; simplify value groups and verify cast-shadow direction before polishing.

No visual claim was promoted to retrieved fact because the artwork images were unavailable to this run.

## Approval boundary

- Run ID: `RUN-213C3DDF6FE0`
- Approval ID: `APR-PILOT-001`
- Proposal hash: `2fd142565d45c92ad8c490dd17ad16f33fb48cbe61c26a5a18758c307741b4b9`
- Human approval: approved by Joshua Lee Joseph / Chef Joseph Ramsey
- Approval scope:
  - `current_goal` → `Complete a bounded Finish Cycle review`
  - `next_action` → `Review the current artwork images for essential perspective and value corrections before any finish decision`
- Status change: none; remains `active`
- Title change: none
- Primary Lab change: none

## Commit and restart verification

- Canonical commit result: success
- New version: `5`
- Version 4 preserved: yes
- Version 5 bound to `APR-PILOT-001`: yes
- Exact version-5 retrieval after process restart: passed
- Audit events preserved: artwork creation, approval request, canonical version commit
- Alias uncertainty preserved as an unresolved conflict record: yes

## Pass criteria

| Criterion | Result |
|---|---|
| Exact artwork retrieved | PASS |
| Primary Lab preserved | PASS |
| No more than two consultants | PASS |
| Evidence/proposal boundary preserved | PASS |
| No unapproved canonical write | PASS |
| Approval bound to exact proposal | PASS |
| New version created | PASS |
| Prior version retained | PASS |
| Exact retrieval after restart | PASS |
| Unresolved title relationship retained | PASS |

## Next safe action

Supply the current artwork images for a real Finish Cycle assessment. That assessment must separate essential corrections from optional polish and must not mark the artwork finished without a separate explicit approval.
