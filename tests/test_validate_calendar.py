import tempfile
import unittest
from datetime import datetime
from pathlib import Path

import pytz
from icalendar import Calendar, Event

from src import validate_calendar


class ValidateCalendarTests(unittest.TestCase):
    def test_empty_calendar_is_invalid(self):
        calendar = Calendar()
        calendar.add("prodid", "-//test//EN")
        calendar.add("version", "2.0")

        with tempfile.TemporaryDirectory() as temp_dir:
            calendar_path = Path(temp_dir) / "empty.ics"
            calendar_path.write_bytes(calendar.to_ical())

            self.assertFalse(
                validate_calendar.validate_ics_file(str(calendar_path))
            )

    def test_non_empty_calendar_is_valid(self):
        calendar = Calendar()
        calendar.add("prodid", "-//test//EN")
        calendar.add("version", "2.0")
        event = Event()
        event.add("uid", "20260829-test@example.com")
        event.add(
            "dtstart",
            datetime(2026, 8, 29, 14, 0, tzinfo=pytz.utc),
        )
        calendar.add_component(event)

        with tempfile.TemporaryDirectory() as temp_dir:
            calendar_path = Path(temp_dir) / "fixtures.ics"
            calendar_path.write_bytes(calendar.to_ical())

            self.assertTrue(
                validate_calendar.validate_ics_file(str(calendar_path))
            )


if __name__ == "__main__":
    unittest.main()
