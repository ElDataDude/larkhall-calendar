# Larkhall Athletic Fixtures Calendar

An automatically updating iCalendar (.ics) file containing Larkhall Athletic football fixtures that supporters can subscribe to in their personal calendar applications.

## Overview

This project creates and maintains a subscribable calendar of Larkhall Athletic fixtures, pulling data from the FootballWebPages API and updating daily to ensure fixtures are always current.

## Features

- **Automatic Updates**: Calendar refreshes daily via GitHub Actions
- **Complete Fixture Information**: Includes opponent, venue, date/time, and competition
- **Easy Subscription**: Compatible with all major calendar applications
- **Always Current**: Reflects the latest fixture changes and updates

## How to Subscribe

### Google Calendar

**Option 1: One-Click Subscription (Recommended)**

1. Visit our [calendar page](https://eldatadude.github.io/larkhall-calendar/)
2. Click the "Add to Google Calendar (One Click)" button
3. In the Google Calendar page that opens, click "Add calendar"

**Option 2: Manual Subscription**

1. Open Google Calendar
2. Click the "+" next to "Other calendars"
3. Select "From URL"
4. Enter the calendar URL: `https://eldatadude.github.io/larkhall-calendar/fixtures.ics`
5. Click "Add calendar"

**Mobile Users**: Scan the QR code on our [QR code page](https://eldatadude.github.io/larkhall-calendar/qr-code.html) for easy subscription.

### Apple Calendar

1. Open Calendar app
2. Select File > New Calendar Subscription
3. Enter the calendar URL: `https://eldatadude.github.io/larkhall-calendar/fixtures.ics`
4. Click "Subscribe"
5. Configure options and click "OK"

### Microsoft Outlook

1. Open Outlook
2. Go to Calendar view
3. Select "Add Calendar" > "From Internet"
4. Enter the calendar URL: `https://eldatadude.github.io/larkhall-calendar/fixtures.ics`
5. Click "OK"

For more detailed instructions, see our [Simple Subscription Guide](simple-subscription-guide.md).

## Technical Details

### System Architecture

The system follows a simple, robust architecture designed for reliability and minimal maintenance:

1. **Data Fetcher**: Retrieves fixture data from the FootballWebPages API
2. **Data Processor**: Transforms raw API data into structured fixture information
3. **iCalendar Generator**: Converts structured data into standard iCalendar format
4. **File Storage**: Persists the generated calendar file
5. **Public Hosting**: Makes the calendar publicly accessible via GitHub Pages
6. **Scheduler**: Triggers regular updates via GitHub Actions

### Technology Stack

- **Python 3.9+**: Primary programming language
- **GitHub**: Version control, GitHub Actions for automation, GitHub Pages for hosting
- **iCalendar Standard (RFC 5545)**: Calendar data interchange format

### Key Dependencies

- **requests**: HTTP client for API communication
- **icalendar**: Generate iCalendar (.ics) files
- **pytz**: Timezone handling
- **python-dotenv**: Environment variable management for local development

### Update Mechanism

The calendar update process follows these steps:

1. **Scheduled Trigger**: Daily execution via GitHub Actions (4:00 AM UTC)
2. **Data Refresh**: Fetch latest fixture data from the FootballWebPages API
3. **File Regeneration**: Create new .ics file with updated information
4. **Validation**: Verify the calendar format is valid
5. **Publication**: Commit and push to GitHub repository

## Development

### Prerequisites

- Python 3.9+
- Git

### Setup

1. Clone the repository
   ```bash
   git clone https://github.com/ElDataDude/larkhall-calendar.git
   cd larkhall-calendar
   ```

2. Run the setup script
   ```bash
   ./setup.sh
   ```
   
   This will:
   - Create a Python virtual environment
   - Install dependencies
   - Create a template .env file

3. Configure your environment
   ```bash
   # Edit .env file with your API key
   echo "RAPIDAPI_KEY=your_api_key_here" > .env
   ```

### Manual Update

To manually update the calendar:

```bash
# Activate virtual environment
source venv/bin/activate

# Run the update script
python src/update_calendar.py

# Validate the calendar
python src/validate_calendar.py
```

### Testing

To test the API connection:

```bash
python src/test_api.py
```

## Deployment

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

## Maintenance

The calendar is designed to require minimal maintenance. The GitHub Actions workflow automatically updates the calendar daily.

### Monitoring

- Check GitHub Actions logs for any workflow failures
- Verify that the calendar is updating correctly
- Test subscription periodically to ensure compatibility

### Troubleshooting

If you encounter issues:

1. **API Connection Problems**:
   - Verify API key is valid
   - Check API endpoint status
   - Review logs for error messages

2. **Calendar Format Issues**:
   - Validate the .ics file against RFC 5545 standards
   - Test with multiple calendar applications

3. **GitHub Actions Failures**:
   - Check workflow logs for error messages
   - Verify that all required secrets are configured

## License

MIT

## Acknowledgements

- FootballWebPages for providing the API
- Larkhall Athletic Football Club
