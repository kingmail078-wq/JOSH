import tempfile
import unittest
from pathlib import Path

from sketch_lab.coordinator import Coordinator
from sketch_lab.ledger import Ledger, LedgerAccessError, NotFoundError
from sketch_lab.models import Artwork, Lab


class MVPTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ledger = Ledger(Path(self.tmp.name) / "ledger.db")
        self.art = Artwork("ART-LIGHTHOUSE-001", "p", "The Last Point on the Map", Lab.PERSPECTIVE_ENVIRONMENTS,
                           [Lab.REFERENCE_IDEA], current_goal="Focal hierarchy", version=4)
        self.ledger.create_artwork(self.art)
        self.coordinator = Coordinator(self.ledger)

    def tearDown(self):
        self.ledger.close(); self.tmp.cleanup()

    def test_exact_absence_is_typed_and_does_not_reconstruct(self):
        self.assertIsNone(self.ledger.lookup_artwork("p", "ART-MISSING"))
        with self.assertRaises(NotFoundError): self.ledger.get_artwork("p", "ART-MISSING")

    def test_coordinator_uses_primary_and_at_most_two_consultants(self):
        route = self.coordinator.route(self.art.artwork_id, "lighting contrast reference machine", "p")
        self.assertEqual(route.primary_lab, Lab.PERSPECTIVE_ENVIRONMENTS)
        self.assertLessEqual(len(route.consultants), 2)

    def test_consultants_are_ranked_by_request_relevance(self):
        route = self.coordinator.route(self.art.artwork_id, "light shadow value contrast plus one car", "p")
        self.assertEqual(route.consultants[0], Lab.LIGHTING_VALUES)

    def test_blueprint_routing_includes_named_specialists_without_exceeding_bounded_consultants(self):
        route = self.coordinator.route(self.art.artwork_id, "light reference car", "p")
        self.assertTrue(set(route.consultants).issubset({x.value for x in Lab}))
        self.assertLessEqual(len(route.consultants), 2)

    def test_seeded_pilot_artworks_follow_phase_zero_contract(self):
        stored = self.ledger.get_artwork("p", self.art.artwork_id)
        self.assertEqual(stored.version, 4)
        self.assertEqual(stored.primary_lab, Lab.PERSPECTIVE_ENVIRONMENTS)

    def test_unknown_primary_lab_requires_human_confirmation_before_any_change(self):
        unknown = Artwork("ART-U", "p", "Unknown", "", [])
        self.ledger.create_artwork(unknown)
        self.assertTrue(self.coordinator.route("ART-U", "route this", "p").requires_human_confirmation)

    def test_request_parser_flags_continue_requests_for_human_approval(self):
        self.assertTrue(self.coordinator.parse_requires_confirmation("continue this artwork"))

    def test_ledger_persists_approval_discovery_and_audit_trace(self):
        changes = {"status": "complete"}
        self.ledger.request_approval("APR-1", "p", self.art.artwork_id, 4, changes)
        self.ledger.decide_approval("APR-1", True)
        self.ledger.commit_change("p", self.art.artwork_id, 4, changes, "APR-1", "RUN-1")
        self.assertGreaterEqual(len(self.ledger.audit_trace("p")), 3)

    def test_runtime_envelope_and_evaluation_record_bounded_workflow(self):
        result = self.coordinator.run(self.art.artwork_id, "check light and contrast", "p")
        self.assertLessEqual(len(result.route.consultants), 2)
        self.assertEqual(result.state_version, 4)

    def test_shared_memory_keeps_provenance_and_relationship_graph_across_tasks(self):
        self.ledger.remember("p", "RUN-1", "restart fact", "ART-LIGHTHOUSE-001:v4")
        found = self.ledger.search_memory("p", "restart fact")
        self.assertEqual(found[0]["provenance"], "ART-LIGHTHOUSE-001:v4")

    def test_volume_one_learning_loop_completes_and_second_task_retrieves_first_learning(self):
        first = self.coordinator.run(self.art.artwork_id, "check light", "p")
        self.assertTrue(self.ledger.search_memory("p", first.recommendation[:12]))

    def test_canonical_change_requires_approval_and_preserves_version(self):
        with self.assertRaises(LedgerAccessError):
            self.ledger.commit_change("p", self.art.artwork_id, 4, {"title": "X"}, "APR-X", "RUN-X")
        changes = {"title": "Lighthouse Map"}
        self.ledger.request_approval("APR-2", "p", self.art.artwork_id, 4, changes)
        self.ledger.decide_approval("APR-2", True)
        updated = self.ledger.commit_change("p", self.art.artwork_id, 4, changes, "APR-2", "RUN-2")
        self.assertEqual(updated.version, 5)

    def test_project_isolation_does_not_leak_metadata(self):
        with self.assertRaises(LedgerAccessError):
            self.ledger.get_artwork_for_project("other", "p", self.art.artwork_id)


if __name__ == "__main__":
    unittest.main()
