import copy
import json
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path
from unittest import mock

import pytz
import requests
from icalendar import Calendar, Event

from src import update_calendar


FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "football_web_pages_2026_27.json"
)
REFERENCE_TIME = datetime(2026, 7, 17, 12, 0, tzinfo=pytz.utc)


class UpdateCalendarTests(unittest.TestCase):
    def setUp(self):
        self.api_response = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def _process_full_schedule(self):
        return update_calendar.process_fixtures(
            self.api_response,
            now=REFERENCE_TIME,
        )

    def _mock_api_response(
        self,
        *,
        status=200,
        content=b"{}",
        content_type="application/json",
    ):
        response = mock.Mock()
        response.status_code = status
        response.content = content
        response.headers = (
            {"Content-Type": content_type}
            if content_type is not None
            else {}
        )
        response.history = []
        response.json.return_value = self.api_response
        return response

    def test_fixture_labels_authoritative_schedule_and_synthetic_api_schema(self):
        metadata = self.api_response["_fixture-metadata"]

        self.assertTrue(metadata["schedule-authoritative"])
        self.assertIn(
            "https://www.footballwebpages.co.uk/larkhall-athletic/fixtures-results",
            metadata["schedule-source"],
        )
        self.assertIn("not a direct API capture", metadata["api-schema"])
        self.assertEqual(
            len(self.api_response["fixtures-results"]["matches"]),
            44,
        )

    def test_fetch_uses_team_1169_without_a_guessed_season(self):
        response = self._mock_api_response()

        with mock.patch.object(
            update_calendar.requests, "get", return_value=response
        ) as request_get:
            result = update_calendar.fetch_fixtures("test-key")

        self.assertEqual(result, self.api_response)
        request_get.assert_called_once_with(
            update_calendar.API_ENDPOINT,
            headers={
                "FWP-API-Key": "test-key",
                "Accept": "application/json",
                "User-Agent": update_calendar.API_USER_AGENT,
            },
            params={"team": 1169},
            timeout=update_calendar.REQUEST_TIMEOUT_SECONDS,
        )

    def test_fetch_retries_transient_non_json_body_then_succeeds(self):
        body_marker = b"<html>DO_NOT_LOG_TRANSIENT_BODY</html>"
        invalid_response = self._mock_api_response(
            content=body_marker,
            content_type="text/html",
        )
        invalid_response.json.side_effect = requests.exceptions.JSONDecodeError(
            "Expecting value",
            body_marker.decode("ascii"),
            0,
        )
        valid_response = self._mock_api_response()

        with (
            mock.patch.object(
                update_calendar.requests,
                "get",
                side_effect=[invalid_response, valid_response],
            ) as request_get,
            mock.patch.object(update_calendar.time, "sleep") as sleep,
            self.assertLogs("calendar_updater", level="WARNING") as logs,
        ):
            result = update_calendar.fetch_fixtures("DO_NOT_LOG_API_KEY")

        self.assertEqual(result, self.api_response)
        self.assertEqual(request_get.call_count, 2)
        sleep.assert_called_once_with(1)
        self.assertEqual(invalid_response.json.call_count, 1)
        self.assertEqual(valid_response.json.call_count, 1)
        rendered_logs = "\n".join(logs.output)
        self.assertIn("reason=invalid_json", rendered_logs)
        self.assertIn("status=200", rendered_logs)
        self.assertIn("content_type=text/html", rendered_logs)
        self.assertIn(f"body_bytes={len(body_marker)}", rendered_logs)
        self.assertNotIn("DO_NOT_LOG_TRANSIENT_BODY", rendered_logs)
        self.assertNotIn("DO_NOT_LOG_API_KEY", rendered_logs)

    def test_fetch_accepts_valid_json_when_content_type_is_mislabelled(self):
        response = self._mock_api_response(
            content=b'{"fixtures-results": {"matches": []}}',
            content_type="text/plain",
        )

        with (
            mock.patch.object(
                update_calendar.requests,
                "get",
                return_value=response,
            ) as request_get,
            mock.patch.object(update_calendar.time, "sleep") as sleep,
        ):
            result = update_calendar.fetch_fixtures("test-key")

        self.assertEqual(result, self.api_response)
        request_get.assert_called_once()
        sleep.assert_not_called()
        response.json.assert_called_once_with()

    def test_fetch_exhausts_non_json_retries_without_leaking_content(self):
        body_marker = b"DO_NOT_LOG_EXHAUSTED_BODY"
        response = self._mock_api_response(
            content=body_marker,
            content_type="text/html; boundary=DO_NOT_LOG_HEADER_PARAMETER",
        )
        response.json.side_effect = requests.exceptions.JSONDecodeError(
            "Expecting value",
            body_marker.decode("ascii"),
            0,
        )

        with (
            mock.patch.object(
                update_calendar.requests,
                "get",
                return_value=response,
            ) as request_get,
            mock.patch.object(update_calendar.time, "sleep") as sleep,
            self.assertLogs("calendar_updater", level="WARNING") as logs,
            self.assertRaises(update_calendar.FixtureDataError) as error,
        ):
            update_calendar.fetch_fixtures("DO_NOT_LOG_API_KEY")

        self.assertEqual(request_get.call_count, 3)
        self.assertEqual(response.json.call_count, 3)
        self.assertEqual(sleep.call_args_list, [mock.call(1), mock.call(2)])
        rendered_output = "\n".join([*logs.output, str(error.exception)])
        self.assertIn("reason=invalid_json", rendered_output)
        self.assertIn("content_type=text/html", rendered_output)
        self.assertNotIn("DO_NOT_LOG_EXHAUSTED_BODY", rendered_output)
        self.assertNotIn("DO_NOT_LOG_HEADER_PARAMETER", rendered_output)
        self.assertNotIn("DO_NOT_LOG_API_KEY", rendered_output)

    def test_fetch_does_not_retry_client_auth_error(self):
        response = self._mock_api_response(
            status=403,
            content=b"DO_NOT_LOG_CLIENT_ERROR_BODY",
            content_type="text/html",
        )

        with (
            mock.patch.object(
                update_calendar.requests,
                "get",
                return_value=response,
            ) as request_get,
            mock.patch.object(update_calendar.time, "sleep") as sleep,
            self.assertLogs("calendar_updater", level="WARNING") as logs,
            self.assertRaisesRegex(
                update_calendar.FixtureDataError,
                "status=403",
            ),
        ):
            update_calendar.fetch_fixtures("DO_NOT_LOG_API_KEY")

        request_get.assert_called_once()
        sleep.assert_not_called()
        response.json.assert_not_called()
        rendered_logs = "\n".join(logs.output)
        self.assertIn("reason=client_status", rendered_logs)
        self.assertNotIn("DO_NOT_LOG_CLIENT_ERROR_BODY", rendered_logs)
        self.assertNotIn("DO_NOT_LOG_API_KEY", rendered_logs)

    def test_fetch_retries_empty_success_response_then_fails_closed(self):
        response = self._mock_api_response(
            status=204,
            content=b"",
            content_type=None,
        )

        with (
            mock.patch.object(
                update_calendar.requests,
                "get",
                return_value=response,
            ) as request_get,
            mock.patch.object(update_calendar.time, "sleep") as sleep,
            self.assertRaisesRegex(
                update_calendar.FixtureDataError,
                "reason=empty_body status=204",
            ),
        ):
            update_calendar.fetch_fixtures("test-key")

        self.assertEqual(request_get.call_count, 3)
        self.assertEqual(sleep.call_args_list, [mock.call(1), mock.call(2)])
        response.json.assert_not_called()

    def test_fetch_retries_retryable_status_then_succeeds(self):
        retryable_response = self._mock_api_response(
            status=503,
            content=b"temporarily unavailable",
            content_type="text/plain",
        )
        valid_response = self._mock_api_response()

        with (
            mock.patch.object(
                update_calendar.requests,
                "get",
                side_effect=[retryable_response, valid_response],
            ) as request_get,
            mock.patch.object(update_calendar.time, "sleep") as sleep,
        ):
            result = update_calendar.fetch_fixtures("test-key")

        self.assertEqual(result, self.api_response)
        self.assertEqual(request_get.call_count, 2)
        sleep.assert_called_once_with(1)
        retryable_response.json.assert_not_called()

    def test_fetch_uses_numeric_retry_after_for_rate_limit(self):
        rate_limited_response = self._mock_api_response(
            status=429,
            content=b"rate limited",
            content_type="text/plain",
        )
        rate_limited_response.headers["Retry-After"] = "60"
        valid_response = self._mock_api_response()

        with (
            mock.patch.object(
                update_calendar.requests,
                "get",
                side_effect=[rate_limited_response, valid_response],
            ) as request_get,
            mock.patch.object(update_calendar.time, "sleep") as sleep,
        ):
            result = update_calendar.fetch_fixtures("test-key")

        self.assertEqual(result, self.api_response)
        self.assertEqual(request_get.call_count, 2)
        sleep.assert_called_once_with(60)
        rate_limited_response.json.assert_not_called()

    def test_fetch_bounds_or_defaults_invalid_retry_after(self):
        cases = [
            ("0", 1),
            ("61", 60),
            ("not-a-number", 60),
            ("DO_NOT_LOG_RETRY_AFTER", 60),
            (None, 60),
        ]

        for retry_after, expected_delay in cases:
            with self.subTest(
                retry_after=retry_after,
                expected_delay=expected_delay,
            ):
                rate_limited_response = self._mock_api_response(
                    status=429,
                    content=b"rate limited",
                    content_type="text/plain",
                )
                if retry_after is not None:
                    rate_limited_response.headers["Retry-After"] = retry_after
                valid_response = self._mock_api_response()

                with (
                    mock.patch.object(
                        update_calendar.requests,
                        "get",
                        side_effect=[rate_limited_response, valid_response],
                    ) as request_get,
                    mock.patch.object(update_calendar.time, "sleep") as sleep,
                    self.assertLogs(
                        "calendar_updater",
                        level="WARNING",
                    ) as logs,
                ):
                    result = update_calendar.fetch_fixtures("test-key")

                self.assertEqual(result, self.api_response)
                self.assertEqual(request_get.call_count, 2)
                sleep.assert_called_once_with(expected_delay)
                rate_limited_response.json.assert_not_called()
                self.assertNotIn(
                    "DO_NOT_LOG_RETRY_AFTER",
                    "\n".join(logs.output),
                )

    def test_fetch_retries_timeout_and_connection_error_without_logging_details(self):
        for request_error, expected_reason in [
            (requests.Timeout("DO_NOT_LOG_TIMEOUT_DETAIL"), "timeout"),
            (
                requests.ConnectionError("DO_NOT_LOG_CONNECTION_DETAIL"),
                "connection_error",
            ),
        ]:
            with self.subTest(expected_reason=expected_reason):
                valid_response = self._mock_api_response()
                with (
                    mock.patch.object(
                        update_calendar.requests,
                        "get",
                        side_effect=[request_error, valid_response],
                    ) as request_get,
                    mock.patch.object(update_calendar.time, "sleep") as sleep,
                    self.assertLogs("calendar_updater", level="WARNING") as logs,
                ):
                    result = update_calendar.fetch_fixtures("DO_NOT_LOG_API_KEY")

                self.assertEqual(result, self.api_response)
                self.assertEqual(request_get.call_count, 2)
                sleep.assert_called_once_with(1)
                rendered_logs = "\n".join(logs.output)
                self.assertIn(f"reason={expected_reason}", rendered_logs)
                self.assertNotIn("DO_NOT_LOG", rendered_logs)

    def test_full_2026_27_schedule_new_opponents_and_uk_timezone_generate_events(self):
        fixtures = self._process_full_schedule()

        self.assertEqual(len(fixtures), 44)
        self.assertEqual(
            [fixture["opponent"] for fixture in fixtures[:4]],
            ["Kidlington", "Weymouth", "Worcester Raiders", "Dorchester Town"],
        )
        self.assertEqual(
            fixtures[0]["date"],
            datetime(2026, 8, 8, 14, 0, tzinfo=pytz.utc),
        )
        winter_fixture = next(
            fixture
            for fixture in fixtures
            if fixture["opponent"] == "Bideford"
            and fixture["date"].date().isoformat() == "2026-11-07"
        )
        self.assertEqual(
            winter_fixture["date"],
            datetime(2026, 11, 7, 15, 0, tzinfo=pytz.utc),
        )

        calendar = update_calendar.create_calendar(fixtures)
        events = [
            component
            for component in calendar.walk()
            if component.name == "VEVENT"
        ]

        self.assertEqual(len(events), 44)
        self.assertEqual(len({str(event.get("uid")) for event in events}), 44)
        event_starts = [event.decoded("dtstart") for event in events]
        self.assertGreaterEqual(
            min(event_starts),
            datetime(2026, 8, 8, 14, 0, tzinfo=pytz.utc),
        )
        self.assertLessEqual(
            max(event_starts),
            datetime(2027, 4, 17, 14, 0, tzinfo=pytz.utc),
        )
        self.assertEqual(
            str(events[0].get("summary")),
            "Kidlington vs Larkhall Athletic",
        )
        self.assertEqual(events[0].decoded("location"), b"")
        self.assertEqual(
            str(events[1].get("summary")),
            "Larkhall Athletic vs Weymouth",
        )
        self.assertEqual(events[1].decoded("location"), b"Plain Ham")
        self.assertEqual(
            events[0].decoded("dtstart"),
            datetime(2026, 8, 8, 14, 0, tzinfo=pytz.utc),
        )

    def test_empty_upstream_match_list_is_deferred_to_existing_calendar_guard(self):
        self.assertEqual(
            update_calendar.process_fixtures(
                {"fixtures-results": {"matches": []}},
                now=REFERENCE_TIME,
            ),
            [],
        )

    def test_malformed_upstream_shape_fails_closed(self):
        malformed_responses = [
            {},
            {"fixtures-results": None},
            {"fixtures-results": {"matches": {}}},
            {"fixtures-results": {"matches": ["not-a-match"]}},
        ]

        for response in malformed_responses:
            with self.subTest(response=response):
                with self.assertRaises(update_calendar.FixtureDataError):
                    update_calendar.process_fixtures(
                        response,
                        now=REFERENCE_TIME,
                    )

    def test_malformed_past_row_does_not_block_future_schedule(self):
        response = copy.deepcopy(self.api_response)
        response["fixtures-results"]["matches"].insert(
            0,
            {"id": "old-malformed-row", "date": "2025-01-01"},
        )

        fixtures = update_calendar.process_fixtures(
            response,
            now=REFERENCE_TIME,
        )

        self.assertEqual(len(fixtures), 44)

    def test_future_tbc_match_is_a_tentative_date_only_event(self):
        response = copy.deepcopy(self.api_response)
        response["fixtures-results"]["matches"][0]["time"] = ""

        fixtures = update_calendar.process_fixtures(
            response,
            now=REFERENCE_TIME,
        )
        calendar = update_calendar.create_calendar(fixtures)
        event = next(
            component
            for component in calendar.walk()
            if component.name == "VEVENT"
        )

        self.assertEqual(len(fixtures), 44)
        self.assertEqual(fixtures[0]["date"], date(2026, 8, 8))
        self.assertEqual(fixtures[0]["status"], "tentative")
        self.assertEqual(
            str(event.get("summary")),
            "TBD: Kidlington vs Larkhall Athletic",
        )
        self.assertEqual(event.decoded("dtstart"), date(2026, 8, 8))
        self.assertEqual(event.decoded("dtend"), date(2026, 8, 9))
        self.assertEqual(str(event.get("status")), "TENTATIVE")
        self.assertIn(
            "Kick-off time to be confirmed",
            str(event.get("description")),
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "fixtures.ics"
            update_calendar.write_calendar(
                calendar,
                str(output_path),
                now=REFERENCE_TIME,
            )
            self.assertTrue(output_path.exists())

    def test_future_malformed_kickoff_time_fails_closed(self):
        response = copy.deepcopy(self.api_response)
        response["fixtures-results"]["matches"][0]["time"] = "three-ish"

        with self.assertRaisesRegex(
            update_calendar.FixtureDataError,
            "unparseable kick-off time",
        ):
            update_calendar.process_fixtures(
                response,
                now=REFERENCE_TIME,
            )

    def test_future_match_requires_exactly_one_larkhall_and_named_opponent(self):
        malformed_matches = []

        missing_opponent = copy.deepcopy(
            self.api_response["fixtures-results"]["matches"][0]
        )
        missing_opponent["home-team"] = {}
        malformed_matches.append(missing_opponent)

        unnamed_opponent = copy.deepcopy(
            self.api_response["fixtures-results"]["matches"][0]
        )
        unnamed_opponent["home-team"]["name"] = ""
        malformed_matches.append(unnamed_opponent)

        both_larkhall = copy.deepcopy(
            self.api_response["fixtures-results"]["matches"][0]
        )
        both_larkhall["home-team"] = {"id": 1169, "name": "Larkhall Athletic"}
        malformed_matches.append(both_larkhall)

        neither_larkhall = copy.deepcopy(
            self.api_response["fixtures-results"]["matches"][0]
        )
        neither_larkhall["away-team"] = {"id": 9999, "name": "Another Team"}
        malformed_matches.append(neither_larkhall)

        for match in malformed_matches:
            with self.subTest(match=match):
                with self.assertRaises(update_calendar.FixtureDataError):
                    update_calendar.process_fixtures(
                        {"fixtures-results": {"matches": [match]}},
                        now=REFERENCE_TIME,
                    )

    def test_completed_season_is_successful_noop_preserving_existing_file(self):
        response = copy.deepcopy(self.api_response)
        for match in response["fixtures-results"]["matches"]:
            match["date"] = "2025-01-01"

        self.assertEqual(
            update_calendar.process_fixtures(response, now=REFERENCE_TIME),
            [],
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "fixtures.ics"
            output_path.write_bytes(b"last known good calendar")

            with (
                mock.patch.object(update_calendar, "get_api_key", return_value="key"),
                mock.patch.object(
                    update_calendar,
                    "fetch_fixtures",
                    return_value=response,
                ),
                mock.patch.object(
                    update_calendar,
                    "OUTPUT_FILE",
                    str(output_path),
                ),
            ):
                update_calendar.main()

            self.assertEqual(
                output_path.read_bytes(),
                b"last known good calendar",
            )

    def test_empty_source_fails_with_empty_or_future_existing_calendar(self):
        empty_response = {"fixtures-results": {"matches": []}}
        fixtures = self._process_full_schedule()
        future_calendar = update_calendar.create_calendar(fixtures)

        with tempfile.TemporaryDirectory() as temp_dir:
            empty_path = Path(temp_dir) / "empty.ics"
            empty_calendar = Calendar()
            empty_calendar.add("prodid", "-//test//EN")
            empty_calendar.add("version", "2.0")
            empty_path.write_bytes(empty_calendar.to_ical())

            future_path = Path(temp_dir) / "future.ics"
            update_calendar.write_calendar(
                future_calendar,
                str(future_path),
                now=REFERENCE_TIME,
            )

            for output_path in [empty_path, future_path]:
                with self.subTest(output_path=output_path):
                    with (
                        mock.patch.object(
                            update_calendar,
                            "get_api_key",
                            return_value="key",
                        ),
                        mock.patch.object(
                            update_calendar,
                            "fetch_fixtures",
                            return_value=empty_response,
                        ),
                        mock.patch.object(
                            update_calendar,
                            "OUTPUT_FILE",
                            str(output_path),
                        ),
                        self.assertRaises(SystemExit) as exit_context,
                    ):
                        update_calendar.main()

                    self.assertEqual(exit_context.exception.code, 1)

    def test_empty_source_noops_with_nonempty_entirely_past_calendar(self):
        empty_response = {"fixtures-results": {"matches": []}}
        past_calendar = Calendar()
        past_calendar.add("prodid", "-//test//EN")
        past_calendar.add("version", "2.0")
        past_event = Event()
        past_event.add("uid", "past@example.com")
        past_event.add(
            "dtstart",
            datetime(2025, 1, 1, 15, 0, tzinfo=pytz.utc),
        )
        past_calendar.add_component(past_event)

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "fixtures.ics"
            output_path.write_bytes(past_calendar.to_ical())
            original_bytes = output_path.read_bytes()

            with (
                mock.patch.object(update_calendar, "get_api_key", return_value="key"),
                mock.patch.object(
                    update_calendar,
                    "fetch_fixtures",
                    return_value=empty_response,
                ),
                mock.patch.object(update_calendar, "OUTPUT_FILE", str(output_path)),
            ):
                update_calendar.main()

            self.assertEqual(output_path.read_bytes(), original_bytes)

    def test_empty_calendar_cannot_replace_existing_file(self):
        empty_calendar = Calendar()
        empty_calendar.add("prodid", "-//test//EN")
        empty_calendar.add("version", "2.0")

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "fixtures.ics"
            output_path.write_bytes(b"existing calendar")

            with self.assertRaisesRegex(
                update_calendar.FixtureDataError,
                "zero events",
            ):
                update_calendar.write_calendar(
                    empty_calendar,
                    str(output_path),
                    now=REFERENCE_TIME,
                )

            self.assertEqual(output_path.read_bytes(), b"existing calendar")

    def test_full_validation_runs_before_existing_file_is_replaced(self):
        invalid_calendar = Calendar()
        invalid_calendar.add("prodid", "-//test//EN")
        invalid_calendar.add("version", "2.0")
        for _ in range(update_calendar.BOOTSTRAP_MIN_UPCOMING_EVENTS):
            invalid_calendar.add_component(Event())

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "fixtures.ics"
            output_path.write_bytes(b"existing calendar")

            with self.assertRaisesRegex(
                update_calendar.FixtureDataError,
                "failed full validation",
            ):
                update_calendar.write_calendar(
                    invalid_calendar,
                    str(output_path),
                    now=REFERENCE_TIME,
                )

            self.assertEqual(output_path.read_bytes(), b"existing calendar")

    def test_current_empty_calendar_rejects_one_event_bootstrap(self):
        fixtures = self._process_full_schedule()
        one_event_calendar = update_calendar.create_calendar(fixtures[:1])
        empty_calendar = Calendar()
        empty_calendar.add("prodid", "-//test//EN")
        empty_calendar.add("version", "2.0")

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "fixtures.ics"
            output_path.write_bytes(empty_calendar.to_ical())
            original_bytes = output_path.read_bytes()

            with self.assertRaisesRegex(
                update_calendar.FixtureDataError,
                "Refusing bootstrap calendar with 1 events",
            ):
                update_calendar.write_calendar(
                    one_event_calendar,
                    str(output_path),
                    now=REFERENCE_TIME,
                )

            self.assertEqual(output_path.read_bytes(), original_bytes)

    def test_material_partial_response_cannot_truncate_future_baseline(self):
        fixtures = self._process_full_schedule()
        full_calendar = update_calendar.create_calendar(fixtures)
        partial_calendar = update_calendar.create_calendar(fixtures[:1])

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "fixtures.ics"
            update_calendar.write_calendar(
                full_calendar,
                str(output_path),
                now=REFERENCE_TIME,
            )
            original_bytes = output_path.read_bytes()

            with self.assertRaisesRegex(
                update_calendar.FixtureDataError,
                "Refusing material truncation to 1 events",
            ):
                update_calendar.write_calendar(
                    partial_calendar,
                    str(output_path),
                    now=REFERENCE_TIME,
                )

            self.assertEqual(output_path.read_bytes(), original_bytes)

    def test_future_baseline_allows_single_fixture_removal(self):
        fixtures = self._process_full_schedule()
        full_calendar = update_calendar.create_calendar(fixtures)
        remaining_calendar = update_calendar.create_calendar(fixtures[1:])

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "fixtures.ics"
            update_calendar.write_calendar(
                full_calendar,
                str(output_path),
                now=REFERENCE_TIME,
            )
            update_calendar.write_calendar(
                remaining_calendar,
                str(output_path),
                now=REFERENCE_TIME,
            )

            published = Calendar.from_ical(output_path.read_bytes())
            event_count = sum(
                1
                for component in published.walk()
                if component.name == "VEVENT"
            )
            self.assertEqual(event_count, 43)

    def test_valid_calendar_atomically_replaces_existing_file(self):
        fixtures = self._process_full_schedule()
        calendar = update_calendar.create_calendar(fixtures)

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "fixtures.ics"
            output_path.write_bytes(b"stale calendar")

            update_calendar.write_calendar(
                calendar,
                str(output_path),
                now=REFERENCE_TIME,
            )

            published = Calendar.from_ical(output_path.read_bytes())
            event_count = sum(
                1
                for component in published.walk()
                if component.name == "VEVENT"
            )
            self.assertEqual(event_count, 44)


if __name__ == "__main__":
    unittest.main()
