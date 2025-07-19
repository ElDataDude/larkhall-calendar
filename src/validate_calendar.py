#!/usr/bin/env python3
"""
Validate iCalendar File

This script validates the generated iCalendar file to ensure it's properly
formatted and compatible with calendar applications.

Usage:
    python validate_calendar.py [path_to_ics_file]

Author: ElDataDude
Version: 1.0.0
Last Updated: March 28, 2025
"""

import sys
from icalendar import Calendar
from datetime import datetime
import pytz

def validate_ics_file(file_path):
    """
    Validate an iCalendar file.
    
    Args:
        file_path: Path to the .ics file
        
    Returns:
        bool: True if valid, False otherwise
    """
    print(f"Validating iCalendar file: {file_path}")
    
    try:
        # Read the file
        with open(file_path, 'rb') as f:
            cal_content = f.read()
        
        # Parse the calendar
        cal = Calendar.from_ical(cal_content)
        
        # Check required properties
        required_props = ['prodid', 'version']
        for prop in required_props:
            if prop not in cal:
                print(f"ERROR: Missing required property: {prop}")
                return False
        
        # Count and validate events
        event_count = 0
        valid_events = 0
        
        for component in cal.walk():
            if component.name == 'VEVENT':
                event_count += 1
                
                # Check required event properties
                if 'uid' not in component:
                    print(f"ERROR: Event missing UID")
                    continue
                    
                if 'dtstart' not in component:
                    print(f"ERROR: Event missing DTSTART: {component.get('uid')}")
                    continue
                
                # Check date format
                try:
                    start_time = component.get('dtstart').dt
                    if not hasattr(start_time, 'tzinfo') or start_time.tzinfo is None:
                        print(f"WARNING: Event has naive datetime (no timezone): {component.get('uid')}")
                except Exception as e:
                    print(f"ERROR: Invalid date format: {e}")
                    continue
                
                valid_events += 1
        
        # Report results
        print(f"Calendar contains {event_count} events, {valid_events} valid")
        print(f"Calendar version: {cal.get('version')}")
        print(f"Calendar product ID: {cal.get('prodid')}")
        
        if event_count > 0 and valid_events == event_count:
            print("VALIDATION SUCCESSFUL: Calendar is valid")
            return True
        elif event_count == 0:
            print("WARNING: Calendar contains no events")
            return True  # Still valid, just empty
        else:
            print(f"VALIDATION FAILED: {event_count - valid_events} invalid events")
            return False
            
    except Exception as e:
        print(f"VALIDATION FAILED: {e}")
        return False


if __name__ == "__main__":
    # Get file path from command line or use default
    file_path = sys.argv[1] if len(sys.argv) > 1 else "fixtures.ics"
    
    # Validate the file
    is_valid = validate_ics_file(file_path)
    
    # Exit with appropriate status code
    sys.exit(0 if is_valid else 1)
