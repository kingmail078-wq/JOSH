# Sketch Lab Agent Network — Reconstructed MVP

This branch reconstructs the recoverable Phase 0–2 plan from the surviving product specification and GitHub test evidence. The original `/workspaces/JOSH/josh` source was excluded by `.gitignore`, so this is a clean-room implementation, not a claim that the lost source was recovered.

## Preserved contract

- Joshua Lee Joseph / Chef Joseph Ramsey is the Human Controller and final creative authority.
- Every artwork has exactly one Primary Lab.
- A normal run uses the Primary Lab and no more than two justified consultants.
- Missing exact records return `not_found`; the system never reconstructs them from hints.
- Canonical changes require approval, create a new version, and preserve history.
- Specialist disagreement and evidence provenance are retained.
- Project isolation fails closed without leaking record metadata.
- CrewAI is an optional orchestration adapter, never the canonical archive.

## Architecture

The recovered design uses four runtime components carrying thirteen logical roles:

1. `SketchLabFlow`: Grandfather / Executive Chef, Coordinator, Router, approval gates, final delivery.
2. `ReasoningCrew`: Researcher, Analyst, Critic, Synthesizer. The reconstructed MVP runs deterministic Critic/Synthesizer behavior; Researcher/Analyst are deferred extensions.
3. `SketchLabCrew`: six bounded Lab profiles. Perspective & Environments and Lighting, Shading & Values are active pilot specialists.
4. `LedgerService`: deterministic SQLite authority layer and append-only audit trail.

This is intentionally not 26 always-running agents. The larger historical count appears to have mixed logical reasoning roles, governance roles, coordinators, archive/audit functions, and specialist profiles.

## Run locally

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
sketch-lab --db sketch_lab.db init
sketch-lab --db sketch_lab.db seed
sketch-lab --db sketch_lab.db status ART-LIGHTHOUSE-001
sketch-lab --db sketch_lab.db run ART-LIGHTHOUSE-001 "Improve focal hierarchy without changing ownership"
```

No API key, paid provider, or network connection is required.

## Repository recovery status

See [`docs/RECOVERY_PROVENANCE.md`](docs/RECOVERY_PROVENANCE.md) for what was retrieved, inferred, and still missing.

