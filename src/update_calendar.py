#!/usr/bin/env python3
"""
Larkhall Athletic Fixtures Calendar Updater

This script fetches fixture data from the FootballWebPages API and generates
an iCalendar (.ics) file containing upcoming Larkhall Athletic fixtures.
The calendar is designed to be hosted on GitHub Pages and subscribed to by
supporters using their preferred calendar applications.

Usage:
    python update_calendar.py

Environment Variables:
    FOOTBALL_WEB_PAGES_API_KEY: API key for FootballWebPages API (required)
    (RAPIDAPI_KEY is also supported for backward compatibility)

Author: ElDataDude
Version: 1.0.0
Last Updated: March 28, 2025
"""

import os
import sys
import json
import logging
import tempfile
from datetime import date, datetime, timedelta
from typing import Dict, List, Any, Optional
import requests
from icalendar import Calendar, Event
import pytz
from dotenv import load_dotenv

try:
    from .validate_calendar import validate_ics_file
except ImportError:
    from validate_calendar import validate_ics_file

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("calendar_updater")

# Constants
TEAM_ID = 1169  # Larkhall Athletic
API_ENDPOINT = "https://api.footballwebpages.co.uk/v2/fixtures-results.json"
OUTPUT_FILE = "fixtures.ics"
CALENDAR_NAME = "Larkhall Athletic Fixtures"
CALENDAR_DESCRIPTION = "Official fixtures calendar for Larkhall Athletic Football Club"
HOME_VENUE = "Plain Ham, Bath"  # Default venue for home matches
MATCH_DURATION = timedelta(hours=1, minutes=45)  # Typical football match duration
REQUEST_TIMEOUT_SECONDS = 30
UK_TIMEZONE = pytz.timezone("Europe/London")
# With no future last-known-good baseline, reject implausibly small season bootstraps.
BOOTSTRAP_MIN_UPCOMING_EVENTS = 10
# Once a baseline exists, allow normal removals but reject material truncation.
MIN_RETAINED_FUTURE_RATIO = 0.5
TBC_TIME_VALUES = {"", "tbc", "tbd", "to be confirmed"}


class FixtureDataError(ValueError):
    """Raised when upstream data is unsafe to publish as a calendar."""


# Team information mapping (ID to name)
TEAM_INFO = {
    250: "Bashley",
    677: "Bemerton Heath Harlequins",
    412: "Bideford",
    387: "Bishops Cleeve",
    835: "Bristol Manor Farm",
    1509: "Cribbs",
    213: "Evesham United",
    1866: "Exmouth Town",
    851: "Frome Town",
    1431: "Hamworthy United",
    1169: "Larkhall Athletic",
    388: "Malvern Town",
    863: "Melksham Town",
    2522: "Mousehole AFC",
    217: "Paulton Rovers",
    795: "Tavistock",
    912: "Westbury United",
    471: "Willand Rovers",
    914: "Wimborne Town",
    224: "Yate Town"
}


def get_api_key() -> str:
    """
    Retrieve the API key from environment variables.
    
    Returns:
        str: The API key
        
    Raises:
        EnvironmentError: If the API key is not found
    """
    api_key = os.environ.get("FOOTBALL_WEB_PAGES_API_KEY") or os.environ.get(
        "RAPIDAPI_KEY"
    )
    if not api_key:
        raise EnvironmentError(
            "API key not found. Please set the FOOTBALL_WEB_PAGES_API_KEY environment variable."
        )
    return api_key


def fetch_fixtures(api_key: str) -> Dict[str, Any]:
    """
    Fetch fixture data from the FootballWebPages API.

    Args:
        api_key: The API key for authentication

    Returns:
        Dict[str, Any]: The JSON response from the API

    Raises:
        requests.RequestException: If the API request fails
    """
    headers = {
        "FWP-API-Key": api_key
    }
    params = {
        "team": TEAM_ID
    }

    try:
        logger.info(f"Fetching fixtures for team ID {TEAM_ID}")
        response = requests.get(
            API_ENDPOINT,
            headers=headers,
            params=params,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise FixtureDataError("Football Web Pages returned a non-object response")
        return data
    except requests.RequestException as e:
        logger.error(f"API request failed: {e}")
        raise


def process_fixtures(
    data: Dict[str, Any],
    now: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """
    Process the raw API response into a structured format.
    
    Args:
        data: The raw API response
        
    Returns:
        List[Dict[str, Any]]: A list of processed fixture data
    """
    if not isinstance(data, dict):
        raise FixtureDataError("Football Web Pages response must be an object")

    fixture_results = data.get("fixtures-results")
    if not isinstance(fixture_results, dict):
        raise FixtureDataError("Response is missing the fixtures-results object")

    raw_fixtures = fixture_results.get("matches")
    if not isinstance(raw_fixtures, list):
        raise FixtureDataError("Response fixtures-results.matches must be a list")
    if not raw_fixtures:
        logger.info("Football Web Pages returned an empty current fixture list")
        return []

    fixtures = []
    reference_time = now or datetime.now(pytz.utc)
    if reference_time.tzinfo is None:
        reference_time = pytz.utc.localize(reference_time)
    reference_date = reference_time.astimezone(UK_TIMEZONE).date()
    
    for fixture in raw_fixtures:
        if not isinstance(fixture, dict):
            raise FixtureDataError("Response contains a non-object match")

        date_str = fixture.get("date", "")
        try:
            match_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            raise FixtureDataError(
                f"Match {fixture.get('id', '<unknown>')} has no parseable date"
            )

        # Old malformed rows cannot affect the upcoming published calendar.
        if match_date < reference_date:
            continue

        time_str = fixture.get("time", "")
        normalized_time = str(time_str or "").strip()
        time_confirmed = normalized_time.lower() not in TBC_TIME_VALUES
        if time_confirmed:
            combined_datetime = f"{date_str}T{normalized_time}:00"
            fixture_date = parse_date(combined_datetime)
            if fixture_date is None:
                raise FixtureDataError(
                    f"Upcoming match {fixture.get('id', '<unknown>')} has an "
                    "unparseable kick-off time"
                )
        else:
            fixture_date = match_date
            logger.warning(
                f"Match {fixture.get('id', '<unknown>')} has no confirmed kick-off "
                "time; publishing a tentative date-only event"
            )

        home_team = fixture.get("home-team")
        away_team = fixture.get("away-team")
        if not isinstance(home_team, dict) or not isinstance(away_team, dict):
            raise FixtureDataError(
                f"Match {fixture.get('id', '<unknown>')} has malformed team data"
            )
        home_is_larkhall = str(home_team.get("id")) == str(TEAM_ID)
        away_is_larkhall = str(away_team.get("id")) == str(TEAM_ID)
        if home_is_larkhall == away_is_larkhall:
            raise FixtureDataError(
                f"Match {fixture.get('id', '<unknown>')} must contain exactly one "
                "Larkhall Athletic side"
            )

        opponent = away_team if home_is_larkhall else home_team
        if not opponent.get("id") or not str(opponent.get("name", "")).strip():
            raise FixtureDataError(
                f"Match {fixture.get('id', '<unknown>')} has no identifiable opponent"
            )
        
        # Skip past fixtures
        if time_confirmed and fixture_date < reference_time:
            continue
            
        # Get status from the status object
        status_obj = fixture.get("status", {})
        status = (
            status_obj.get("full", "scheduled")
            if time_confirmed
            else "tentative"
        )
        
        # Get competition name
        competition_obj = fixture.get("competition", {})
        competition = competition_obj.get("name", "League")
        
        processed = {
            "id": fixture.get("id", ""),
            "date": fixture_date,
            "status": status,
            "competition": competition,
            "is_home": is_home_fixture(fixture),
            "opponent": get_opponent_name(fixture),
            "venue": fixture.get("venue", ""),
            "time_confirmed": time_confirmed,
        }
        fixtures.append(processed)

    if not fixtures:
        logger.info(
            "No upcoming matches remain in the current fixture list; "
            "existing calendar preserved"
        )
        return []

    logger.info(f"Processed {len(fixtures)} upcoming fixtures")
    return fixtures


def parse_date(date_str: str) -> Optional[datetime]:
    """
    Parse a date string from the API into a datetime object.
    
    Args:
        date_str: The date string to parse
        
    Returns:
        Optional[datetime]: The parsed datetime or None if parsing fails
    """
    if not date_str:
        return None
        
    # Based on API testing, the date format is YYYY-MM-DDThh:mm:ss
    formats = [
        "%Y-%m-%dT%H:%M:%S",    # ISO format without Z
        "%Y-%m-%dT%H:%M:%SZ",   # ISO format with Z
        "%Y-%m-%d %H:%M:%S",    # Space-separated format
        "%Y-%m-%d %H:%M",       # Space-separated format without seconds
        "%d/%m/%Y %H:%M"        # UK format
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            # Ensure timezone awareness - use UK timezone (Europe/London)
            if dt.tzinfo is None:
                uk_tz = pytz.timezone("Europe/London")
                dt = uk_tz.localize(dt)
                # Convert to UTC for storage
                dt = dt.astimezone(pytz.utc)
            return dt
        except ValueError:
            continue
    
    logger.warning(f"Could not parse date: {date_str}")
    return None


def is_home_fixture(fixture: Dict[str, Any]) -> bool:
    """
    Determine if Larkhall Athletic is the home team for a fixture.
    
    Args:
        fixture: The fixture data
        
    Returns:
        bool: True if Larkhall is the home team, False otherwise
    """
    # Based on API testing, the home-team and away-team fields contain team information
    home_team_id = fixture.get("home-team", {}).get("id")
    return str(home_team_id) == str(TEAM_ID)


def get_opponent_name(fixture: Dict[str, Any]) -> str:
    """
    Get the name of Larkhall Athletic's opponent in a fixture.
    
    Args:
        fixture: The fixture data
        
    Returns:
        str: The opponent's name
    """
    # Based on API testing, the home-team and away-team fields contain team information
    if is_home_fixture(fixture):
        opponent_id = fixture.get("away-team", {}).get("id")
        opponent_name = fixture.get("away-team", {}).get("name")
    else:
        opponent_id = fixture.get("home-team", {}).get("id")
        opponent_name = fixture.get("home-team", {}).get("name")
    
    if not opponent_id or not opponent_name:
        raise FixtureDataError("Cannot publish a fixture without an identifiable opponent")

    # Use the team info mapping if available, otherwise use the name from the API
    return TEAM_INFO.get(opponent_id, opponent_name)


def get_venue(fixture: Dict[str, Any]) -> str:
    """
    Get the venue for a fixture.
    
    Args:
        fixture: The fixture data
        
    Returns:
        str: The venue name
    """
    # Based on API testing, the venue field is directly available in the fixture
    venue = fixture.get("venue")
    
    # If venue is not provided, use default home/away logic
    if not venue:
        if is_home_fixture(fixture):
            return HOME_VENUE
        else:
            # For away fixtures, try to determine the venue based on the opponent
            opponent_id = fixture.get("home-team", {}).get("id")
            # This would require a mapping of team IDs to venues
            # For now, just return a generic away venue
            return f"Away at {get_opponent_name(fixture)}"
    
    return venue


def create_calendar(fixtures: List[Dict[str, Any]]) -> Calendar:
    """
    Create an iCalendar object with fixture events.
    
    Args:
        fixtures: The processed fixture data
        
    Returns:
        Calendar: The iCalendar object
    """
    if not fixtures:
        raise FixtureDataError("Refusing to create an empty fixtures calendar")

    cal = Calendar()
    
    # Set calendar properties
    cal.add("prodid", f"-//Larkhall Athletic//Fixtures Calendar//EN")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("method", "PUBLISH")
    cal.add("x-wr-calname", CALENDAR_NAME)
    cal.add("x-wr-caldesc", CALENDAR_DESCRIPTION)
    cal.add("x-wr-timezone", "Europe/London")
    
    # Add events for each fixture
    for fixture in fixtures:
        event = create_event(fixture)
        if event:
            cal.add_component(event)
    
    logger.info(f"Created calendar with {len(fixtures)} events")
    return cal


def create_event(fixture: Dict[str, Any]) -> Optional[Event]:
    """
    Create an iCalendar event for a fixture.
    
    Args:
        fixture: The fixture data
        
    Returns:
        Optional[Event]: The event object or None if creation fails
    """
    # Skip fixtures without a date
    if not fixture.get("date"):
        logger.warning(f"Skipping fixture without date: {fixture}")
        return None
    
    event = Event()
    
    # Determine event title based on home/away status
    if fixture["is_home"]:
        summary = f"Larkhall Athletic vs {fixture['opponent']}"
    else:
        summary = f"{fixture['opponent']} vs Larkhall Athletic"
    
    # Add status prefix for non-confirmed fixtures
    if fixture["status"].lower() == "cancelled":
        summary = f"CANCELLED: {summary}"
    elif fixture["status"].lower() == "postponed":
        summary = f"POSTPONED: {summary}"
    elif fixture["status"].lower() == "tentative":
        summary = f"TBD: {summary}"
    
    # Set event properties
    event.add("summary", summary)
    event.add("dtstart", fixture["date"])
    if isinstance(fixture["date"], datetime):
        event.add("dtend", fixture["date"] + MATCH_DURATION)
    else:
        event.add("dtend", fixture["date"] + timedelta(days=1))
    event.add("dtstamp", datetime.now(pytz.utc))
    
    # Create a unique ID for the event
    fixture_date_str = fixture["date"].strftime("%Y%m%d")
    uid = f"{fixture_date_str}-larkhall-{fixture['opponent'].lower().replace(' ', '-')}@larkhall-fixtures.example.com"
    event.add("uid", uid)
    
    event.add("location", fixture["venue"])
    
    # Add description with additional details
    description = f"{fixture['competition']} match between "
    if fixture["is_home"]:
        description += f"Larkhall Athletic and {fixture['opponent']}"
    else:
        description += f"{fixture['opponent']} and Larkhall Athletic"
    if not fixture.get("time_confirmed", True):
        description += ". Kick-off time to be confirmed"
    event.add("description", description)
    
    # Set status
    if fixture["status"].lower() == "cancelled":
        event.add("status", "CANCELLED")
    elif fixture["status"].lower() in ["postponed", "tentative"]:
        event.add("status", "TENTATIVE")
    else:
        event.add("status", "CONFIRMED")
    
    event.add("categories", ["Football", "Fixture"])
    
    return event


def _inspect_existing_events(filename: str, now: datetime) -> tuple[int, int]:
    """Return total and still-future event counts from the existing calendar."""
    if not os.path.exists(filename):
        return 0, 0

    try:
        with open(filename, "rb") as existing_file:
            existing_calendar = Calendar.from_ical(existing_file.read())
    except Exception as error:
        logger.warning(f"Could not inspect existing calendar baseline: {error}")
        return 0, 0

    reference_time = now
    if reference_time.tzinfo is None:
        reference_time = pytz.utc.localize(reference_time)
    reference_date = reference_time.astimezone(UK_TIMEZONE).date()
    total_events = 0
    future_events = 0

    for component in existing_calendar.walk():
        if component.name != "VEVENT":
            continue
        if "dtstart" not in component:
            continue
        try:
            event_start = component.decoded("dtstart")
        except Exception as error:
            logger.warning(f"Could not inspect existing event start: {error}")
            continue
        total_events += 1
        if isinstance(event_start, datetime):
            if event_start.tzinfo is None:
                event_start = UK_TIMEZONE.localize(event_start)
            if event_start >= reference_time:
                future_events += 1
        elif isinstance(event_start, date) and event_start >= reference_date:
            future_events += 1

    return total_events, future_events


def write_calendar(
    cal: Calendar,
    filename: str,
    now: Optional[datetime] = None,
) -> None:
    """
    Write the calendar to a file.
    
    Args:
        cal: The calendar object
        filename: The output filename
    """
    calendar_bytes = cal.to_ical()
    parsed_calendar = Calendar.from_ical(calendar_bytes)
    event_count = sum(
        1 for component in parsed_calendar.walk() if component.name == "VEVENT"
    )
    if event_count == 0:
        raise FixtureDataError("Refusing to replace the calendar with zero events")

    output_path = os.path.abspath(filename)
    reference_time = now or datetime.now(pytz.utc)
    _, existing_future_events = _inspect_existing_events(
        output_path,
        reference_time,
    )
    if (
        existing_future_events == 0
        and event_count < BOOTSTRAP_MIN_UPCOMING_EVENTS
    ):
        raise FixtureDataError(
            f"Refusing bootstrap calendar with {event_count} events; at least "
            f"{BOOTSTRAP_MIN_UPCOMING_EVENTS} are required without a future baseline"
        )
    if (
        existing_future_events > 0
        and event_count < existing_future_events * MIN_RETAINED_FUTURE_RATIO
    ):
        raise FixtureDataError(
            f"Refusing material truncation to {event_count} events; existing calendar "
            f"still has {existing_future_events} future events"
        )

    output_directory = os.path.dirname(output_path)
    temp_fd, temp_path = tempfile.mkstemp(
        dir=output_directory,
        prefix=f".{os.path.basename(filename)}.",
        suffix=".tmp",
    )
    try:
        with os.fdopen(temp_fd, "wb") as f:
            f.write(calendar_bytes)
        if not validate_ics_file(temp_path):
            raise FixtureDataError("Generated calendar failed full validation")
        os.replace(temp_path, output_path)
    except Exception:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise
    logger.info(f"Calendar written to {filename}")


def main() -> None:
    """Main function to update the fixtures calendar."""
    try:
        # Get API key
        api_key = get_api_key()
        
        # Fetch fixture data
        data = fetch_fixtures(api_key)
        
        # Process fixtures
        fixtures = process_fixtures(data)

        if not fixtures:
            fixture_results = data.get("fixtures-results", {})
            raw_fixtures = fixture_results.get("matches", [])
            if not raw_fixtures:
                total_events, future_events = _inspect_existing_events(
                    os.path.abspath(OUTPUT_FILE),
                    datetime.now(pytz.utc),
                )
                if total_events == 0 or future_events > 0:
                    raise FixtureDataError(
                        "Empty source is safe only when the existing non-empty "
                        "calendar is entirely past"
                    )
            logger.info("Calendar update completed as a no-op")
            return
        
        # Create calendar
        cal = create_calendar(fixtures)
        
        # Write to file
        write_calendar(cal, OUTPUT_FILE)
        
        logger.info("Calendar update completed successfully")
        
    except Exception as e:
        logger.error(f"Calendar update failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
