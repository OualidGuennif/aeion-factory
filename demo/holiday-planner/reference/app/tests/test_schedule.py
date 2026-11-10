import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "domain"))
from schedule import Overlap, Refused, Schedule  # noqa: E402


class ScheduleTests(unittest.TestCase):
    def test_activities_ordered_by_start(self):
        day = Schedule()
        day.add("b", "Beach", 840, 120)
        day.add("a", "Museum", 540, 60)
        self.assertEqual([a.id for a in day.activities], ["a", "b"])

    def test_invalid_times_refused(self):
        day = Schedule()
        for start, duration, field in ((1440, 30, "start_minute"), (600, 0, "duration"), (1400, 60, "duration")):
            with self.assertRaises(Refused) as caught:
                day.add("x", "Late", start, duration)
            self.assertEqual(caught.exception.field, field)
        self.assertEqual(day.activities, [])

    def test_overlap_refused(self):
        day = Schedule()
        day.add("museum", "Museum", 540, 60)
        with self.assertRaises(Overlap):
            day.add("tour", "Tour", 570, 60)
        self.assertEqual([a.id for a in day.activities], ["museum"])

    def test_back_to_back_accepted(self):
        day = Schedule()
        day.add("museum", "Museum", 540, 60)
        day.add("lunch", "Lunch", 600, 60)
        self.assertEqual([a.id for a in day.activities], ["museum", "lunch"])


if __name__ == "__main__":
    unittest.main()
