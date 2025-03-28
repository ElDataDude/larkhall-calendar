# Larkhall Athletic Fixtures Calendar

An automatically updating iCalendar (.ics) file containing Larkhall Athletic football fixtures that supporters can subscribe to in their personal calendar applications.

## Overview

This project creates and maintains a subscribable calendar of Larkhall Athletic fixtures, pulling data from the FootballWebPages API and updating at least daily to ensure fixtures are always current.

## Features

- **Automatic Updates**: Calendar refreshes daily via GitHub Actions
- **Complete Fixture Information**: Includes opponent, venue, date/time, and competition
- **Easy Subscription**: Compatible with all major calendar applications
- **Always Current**: Reflects the latest fixture changes and updates

## How to Subscribe

### Google Calendar

1. Open Google Calendar
2. Click the "+" next to "Other calendars"
3. Select "From URL"
4. Enter the calendar URL: `https://[username].github.io/larkhall-calendar/fixtures.ics`
5. Click "Add calendar"

### Apple Calendar

1. Open Calendar app
2. Select File > New Calendar Subscription
3. Enter the calendar URL: `https://[username].github.io/larkhall-calendar/fixtures.ics`
4. Click "Subscribe"
5. Configure options and click "OK"

### Microsoft Outlook

1. Open Outlook
2. Go to Calendar view
3. Select "Add Calendar" > "From Internet"
4. Enter the calendar URL: `https://[username].github.io/larkhall-calendar/fixtures.ics`
5. Click "OK"

## Technical Details

- Data Source: FootballWebPages API
- Update Frequency: Daily (4:00 AM UTC)
- Calendar Format: iCalendar (RFC 5545)
- Hosting: GitHub Pages

## Development

### Prerequisites

- Python 3.9+
- Git

### Setup

1. Clone the repository
   ```bash
   git clone https://github.com/[username]/larkhall-calendar.git
   cd larkhall-calendar
   ```

2. Create a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables
   ```bash
   # Create .env file (add to .gitignore)
   echo "RAPIDAPI_KEY=your_api_key" > .env
   ```

### Manual Update

To manually update the calendar:

```bash
python src/update_calendar.py
```

## License

MIT

## Acknowledgements

- FootballWebPages for providing the API
- Larkhall Athletic Football Club
