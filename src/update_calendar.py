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
    RAPIDAPI_KEY: API key for FootballWebPages API (required)

Author: ElDataDude
Version: 1.0.0
Last Updated: March 28, 2025
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import requests
from icalendar import Calendar, Event
import pytz
from dotenv import load_dotenv

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
API_ENDPOINT = "https://football-web-pages1.p.rapidapi.com/fixtures-results.json"
OUTPUT_FILE = "fixtures.ics"
CALENDAR_NAME = "Larkhall Athletic Fixtures"
CALENDAR_DESCRIPTION = "Official fixtures calendar for Larkhall Athletic Football Club"
HOME_VENUE = "Plain Ham, Bath"  # Default venue for home matches
MATCH_DURATION = timedelta(hours=1, minutes=45)  # Typical football match duration

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
    api_key = os.environ.get("RAPIDAPI_KEY")
    if not api_key:
        raise EnvironmentError(
            "API key not found. Please set the RAPIDAPI_KEY environment variable."
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
        "X-RapidAPI-Key": api_key
    }
    params = {
        "team": TEAM_ID
    }
    
    try:
        logger.info(f"Fetching fixtures for team ID {TEAM_ID}")
        response = requests.get(API_ENDPOINT, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"API request failed: {e}")
        raise


def process_fixtures(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Process the raw API response into a structured format.
    
    Args:
        data: The raw API response
        
    Returns:
        List[Dict[str, Any]]: A list of processed fixture data
    """
    fixtures = []
    
    # Get matches from the fixtures-results structure
    raw_fixtures = data.get("fixtures-results", {}).get("matches", [])
    
    for fixture in raw_fixtures:
        # Combine date and time fields
        date_str = fixture.get("date", "")
        time_str = fixture.get("time", "")
        combined_datetime = f"{date_str}T{time_str}:00" if date_str and time_str else ""
        
        # Parse the combined datetime
        fixture_date = parse_date(combined_datetime)
        
        # Skip past fixtures
        if fixture_date and fixture_date < datetime.now(pytz.utc):
            continue
            
        # Get status from the status object
        status_obj = fixture.get("status", {})
        status = status_obj.get("full", "scheduled")
        
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
            "venue": fixture.get("venue", "")
        }
        fixtures.append(processed)
    
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
    
    # Use the team info mapping if available, otherwise use the name from the API
    return TEAM_INFO.get(opponent_id, opponent_name or "Unknown Opponent")


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
    event.add("dtend", fixture["date"] + MATCH_DURATION)
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


def write_calendar(cal: Calendar, filename: str) -> None:
    """
    Write the calendar to a file.
    
    Args:
        cal: The calendar object
        filename: The output filename
    """
    with open(filename, "wb") as f:
        f.write(cal.to_ical())
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
