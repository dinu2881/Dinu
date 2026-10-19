import os
import tempfile
import unittest

from job_tracker.db import Tracker


class TrackerTest(unittest.TestCase):
    def setUp(self):
        self.t = Tracker(":memory:")

    def tearDown(self):
        self.t.close()

    def test_add_and_get(self):
        app_id = self.t.add(company="Acme", role="Developer")
        row = self.t.get(app_id)
        self.assertEqual(row["company"], "Acme")
        self.assertEqual(row["status"], "Applied")

    def test_requires_company_and_role(self):
        with self.assertRaises(ValueError):
            self.t.add(company="", role="Dev")

    def test_rejects_bad_status_and_date(self):
        with self.assertRaises(ValueError):
            self.t.add(company="A", role="B", status="Ghosted")
        with self.assertRaises(ValueError):
            self.t.add(company="A", role="B", follow_up="next week")

    def test_update_and_delete(self):
        app_id = self.t.add(company="Acme", role="Dev")
        self.t.update(app_id, status="Interview")
        self.assertEqual(self.t.get(app_id)["status"], "Interview")
        self.t.delete(app_id)
        self.assertIsNone(self.t.get(app_id))

    def test_list_filter_and_search(self):
        self.t.add(company="Acme", role="Dev")
        self.t.add(company="Globex", role="QA", status="Offer")
        self.assertEqual(len(self.t.list()), 2)
        self.assertEqual(len(self.t.list(status="Offer")), 1)
        self.assertEqual(self.t.list(search="acm")[0]["company"], "Acme")

    def test_due_follow_ups_skip_closed(self):
        self.t.add(company="A", role="R", follow_up="2026-01-01")
        self.t.add(company="B", role="R", follow_up="2026-01-01", status="Rejected")
        self.t.add(company="C", role="R", follow_up="2099-01-01")
        due = self.t.due_follow_ups(today="2026-06-01")
        self.assertEqual([r["company"] for r in due], ["A"])

    def test_stats_and_export(self):
        self.t.add(company="A", role="R")
        self.t.add(company="B", role="R", status="Offer")
        self.assertEqual(self.t.stats()["Offer"], 1)
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "out.csv")
            self.assertEqual(self.t.export_csv(path), 2)
            with open(path, encoding="utf-8") as f:
                self.assertEqual(len(f.read().strip().splitlines()), 3)


if __name__ == "__main__":
    unittest.main()
