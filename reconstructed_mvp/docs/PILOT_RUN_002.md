# Pilot Run 002 — Read-only inventory retrieval

## Artwork

- ID: `ART-LAST-CAR-001`
- Title: `Last Car at the Gas Station`
- Primary Lab: `lighting_values`
- Status: `complete`
- Current goal: `Finish Cycle complete — pencil down`
- Baseline version: `1` (isolated pilot import)
- Next route: Archive completion record, then Portfolio Hub evaluation

## Request

```text
Retrieve the current inventory status only. Do not critique, revise, route, reopen, or change the artwork.
```

## Initial result

**ADJUST — operational defect found.**

Passed:

- Exact record retrieved after restart.
- Primary Lab preserved.
- No consultants added.
- Canonical version unchanged.

Failed:

- The coordinator generated refinement advice for a finished artwork.
- The coordinator persisted the proposal to memory during a read-only request.

The defect was preserved as GitHub Issue #3. No real artwork record was reopened.

## Authorized minimal repair

Joshua approved a narrow request-intent boundary repair. No architecture expansion was authorized.

For explicit status/retrieval requests, the coordinator now:

1. performs exact ledger lookup;
2. returns the canonical Primary Lab and state version;
3. activates no consultants;
4. produces no findings;
5. produces no recommendation;
6. performs no memory write;
7. requests no approval because no change is proposed.

Ordinary critique requests continue to activate specialists and preserve their proposal memory.

## Verification

- Original acceptance tests: 13 PASS
- New regression tests: 2 PASS
- Total: 15 PASS
- Pilot Run 002 retest: PASS

Retest evidence:

```text
status: complete
version: 1
primary_lab: lighting_values
consultants: []
findings: []
recommendation: ""
memory_rows_before: 0
memory_rows_after: 0
```

## Final disposition

**PASS — read-only and pencil-down boundaries preserved.**

The fix is limited to the operational defect demonstrated by Pilot Run 002.
