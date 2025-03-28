# iCalendar Format Specification: Larkhall Athletic Fixtures Calendar

This document details the iCalendar format implementation for the Larkhall Athletic Fixtures Calendar, ensuring compliance with RFC 5545 standards and compatibility with major calendar applications.

## iCalendar Overview

The iCalendar format (RFC 5545) is a standard for calendar data exchange. It allows users to subscribe to calendars and receive automatic updates when the source calendar changes.

### File Format Basics

- **File Extension**: .ics
- **MIME Type**: text/calendar
- **Character Set**: UTF-8
- **Line Endings**: CRLF (Carriage Return + Line Feed)
- **Line Folding**: Lines longer than 75 characters must be folded

## Calendar Components

### Calendar Object (VCALENDAR)

The top-level container for calendar information:

```
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Larkhall Athletic//Fixtures Calendar//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:Larkhall Athletic Fixtures
X-WR-CALDESC:Official fixtures calendar for Larkhall Athletic Football Club
X-WR-TIMEZONE:Europe/London
... events ...
END:VCALENDAR
```

#### Required Properties

- **VERSION**: iCalendar specification version (2.0)
- **PRODID**: Unique identifier for the product that created the calendar

#### Recommended Properties

- **CALSCALE**: Calendar scale (GREGORIAN)
- **METHOD**: Publishing method (PUBLISH)
- **X-WR-CALNAME**: Calendar name (for display in applications)
- **X-WR-CALDESC**: Calendar description
- **X-WR-TIMEZONE**: Default timezone

### Event Objects (VEVENT)

Each fixture is represented as a VEVENT:

```
BEGIN:VEVENT
UID:20250405-larkhall-vs-opponent@larkhall-fixtures.example.com
DTSTAMP:20250328T120000Z
DTSTART:20250405T150000Z
DTEND:20250405T164500Z
SUMMARY:Larkhall Athletic vs Opponent FC
LOCATION:Plain Ham, Bath
DESCRIPTION:League match between Larkhall Athletic and Opponent FC
STATUS:CONFIRMED
CATEGORIES:Football,Fixture
END:VEVENT
```

#### Required Properties

- **UID**: Unique identifier for the event
- **DTSTAMP**: Date/time the event was created or modified
- **DTSTART**: Start date/time of the fixture

#### Recommended Properties

- **DTEND**: End date/time of the fixture (typically 1h45m after start)
- **SUMMARY**: Event title (fixture description)
- **LOCATION**: Venue name
- **DESCRIPTION**: Detailed description
- **STATUS**: Event status (CONFIRMED, TENTATIVE, CANCELLED)
- **CATEGORIES**: Event categories

## Date and Time Handling

### Format

All date/time values follow ISO 8601 format:

- **UTC Times**: `YYYYMMDDTHHMMSSZ` (e.g., `20250405T150000Z`)
- **Local Times with Timezone**: `YYYYMMDDTHHMMSS` with TZID parameter

### Timezone Considerations

- All fixture times should be stored in UTC
- Include timezone information for proper local display
- Consider daylight saving time transitions

## Special Cases

### Cancelled or Postponed Fixtures

For cancelled fixtures:

```
BEGIN:VEVENT
UID:20250405-larkhall-vs-opponent@larkhall-fixtures.example.com
DTSTAMP:20250328T120000Z
DTSTART:20250405T150000Z
DTEND:20250405T164500Z
SUMMARY:CANCELLED: Larkhall Athletic vs Opponent FC
LOCATION:Plain Ham, Bath
DESCRIPTION:This fixture has been cancelled.
STATUS:CANCELLED
CATEGORIES:Football,Fixture
END:VEVENT
```

### TBD Fixtures (Date/Time To Be Determined)

For fixtures with confirmed opponents but unconfirmed date/time:

```
BEGIN:VEVENT
UID:20250400-larkhall-vs-opponent@larkhall-fixtures.example.com
DTSTAMP:20250328T120000Z
SUMMARY:TBD: Larkhall Athletic vs Opponent FC
DESCRIPTION:Date and time to be confirmed.
STATUS:TENTATIVE
CATEGORIES:Football,Fixture
END:VEVENT
```

## Calendar Metadata

### Calendar Properties

- **Name**: "Larkhall Athletic Fixtures"
- **Description**: "Official fixtures calendar for Larkhall Athletic Football Club"
- **Color**: Team colors (implementation varies by calendar application)

### Event Properties

- **Title Format**: "[Home Team] vs [Away Team]"
- **Location Format**: "Venue Name, City"
- **Description Format**: Include competition, ticket information if available

## Compatibility Considerations

### Google Calendar

- Supports most standard iCalendar properties
- Handles timezone conversion well
- May ignore some X- properties

### Apple Calendar

- Strong support for iCalendar standard
- Displays location as a map if properly formatted
- Supports calendar colors

### Microsoft Outlook

- May have issues with certain character encodings
- Limited support for some extended properties
- Requires careful timezone handling

## Implementation with Python icalendar Library

### Basic Calendar Creation

```python
from icalendar import Calendar, Event
from datetime import datetime
import pytz

# Create calendar
cal = Calendar()
cal.add('prodid', '-//Larkhall Athletic//Fixtures Calendar//EN')
cal.add('version', '2.0')
cal.add('calscale', 'GREGORIAN')
cal.add('method', 'PUBLISH')
cal.add('x-wr-calname', 'Larkhall Athletic Fixtures')
cal.add('x-wr-caldesc', 'Official fixtures calendar for Larkhall Athletic Football Club')
cal.add('x-wr-timezone', 'Europe/London')

# Create event
event = Event()
event.add('summary', 'Larkhall Athletic vs Opponent FC')
event.add('dtstart', datetime(2025, 4, 5, 15, 0, 0, tzinfo=pytz.utc))
event.add('dtend', datetime(2025, 4, 5, 16, 45, 0, tzinfo=pytz.utc))
event.add('dtstamp', datetime.now(tz=pytz.utc))
event.add('uid', '20250405-larkhall-vs-opponent@larkhall-fixtures.example.com')
event.add('location', 'Plain Ham, Bath')
event.add('description', 'League match between Larkhall Athletic and Opponent FC')
event.add('status', 'CONFIRMED')
event.add('categories', ['Football', 'Fixture'])

# Add event to calendar
cal.add_component(event)

# Write to file
with open('fixtures.ics', 'wb') as f:
    f.write(cal.to_ical())
```

## Validation

To ensure calendar validity:

1. Use online validators like [iCalendar Validator](https://icalendar.org/validator.html)
2. Test with multiple calendar applications
3. Verify RFC 5545 compliance
4. Check for common formatting issues:
   - Line length > 75 characters without folding
   - Invalid characters in property values
   - Missing required properties
   - Timezone inconsistencies

## References

- [RFC 5545: Internet Calendaring and Scheduling Core Object Specification](https://tools.ietf.org/html/rfc5545)
- [iCalendar.org](https://icalendar.org/)
- [Python icalendar Library Documentation](https://icalendar.readthedocs.io/)
