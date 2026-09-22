from __future__ import annotations

import argparse
import json

from .coordinator import Coordinator
from .ledger import Ledger, NotFoundError
from .models import Artwork, Lab


def seed(ledger: Ledger) -> None:
    if ledger.lookup_artwork("sketch-lab", "ART-LIGHTHOUSE-001") is None:
        ledger.create_artwork(Artwork(
            artwork_id="ART-LIGHTHOUSE-001", project_id="sketch-lab",
            title="The Last Point on the Map", primary_lab=Lab.PERSPECTIVE_ENVIRONMENTS,
            supporting_labs=[Lab.REFERENCE_IDEA], current_goal="Clarify lighthouse focal hierarchy",
            constraints=["Protect the lighthouse lamp as the brightest point"],
            next_action="Run two-value comparison", version=4,
        ))


def main() -> None:
    parser = argparse.ArgumentParser(prog="sketch-lab")
    parser.add_argument("--db", default="sketch_lab.db")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    sub.add_parser("seed")
    status = sub.add_parser("status"); status.add_argument("artwork_id")
    run = sub.add_parser("run"); run.add_argument("artwork_id"); run.add_argument("request")
    args = parser.parse_args()
    ledger = Ledger(args.db)
    try:
        if args.command == "init":
            print(json.dumps({"status": "initialized", "database": args.db}))
        elif args.command == "seed":
            seed(ledger); print(json.dumps({"status": "seeded"}))
        elif args.command == "status":
            print(json.dumps(ledger.get_artwork("sketch-lab", args.artwork_id).payload(), indent=2))
        elif args.command == "run":
            result = Coordinator(ledger).run(args.artwork_id, args.request)
            print(json.dumps({
                "run_id": result.run_id, "artwork_id": result.artwork_id,
                "state_version": result.state_version,
                "route": {"primary_lab": result.route.primary_lab, "consultants": result.route.consultants, "reasons": result.route.reasons},
                "findings": result.findings, "recommendation": result.recommendation,
                "approval_required": result.approval_required,
            }, indent=2))
    except NotFoundError:
        print(json.dumps({"status": "not_found"}))
        raise SystemExit(2)
    finally:
        ledger.close()


if __name__ == "__main__":
    main()

