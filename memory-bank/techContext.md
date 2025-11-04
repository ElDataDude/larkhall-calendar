# Technical Context: Larkhall Athletic Fixtures Calendar

## Technology Stack

### Core Technologies

1. **Python 3.9+**
   - Primary programming language
   - Chosen for simplicity, readability, and extensive library support
   - Strong support for HTTP requests and data processing

2. **GitHub**
   - Version control and code hosting
   - GitHub Actions for automation
   - GitHub Pages for hosting

3. **iCalendar Standard (RFC 5545)**
   - Calendar data interchange format
   - Widely supported across calendar applications
   - Enables subscription functionality

### Key Dependencies

1. **requests (Python Library)**
   - Purpose: HTTP client for API communication
   - Version: Latest stable
   - Features used: GET requests, headers, error handling

2. **icalendar (Python Library)**
   - Purpose: Generate iCalendar (.ics) files
   - Version: Latest stable
   - Features used: Calendar and Event objects, serialization

3. **pytz (Python Library)**
   - Purpose: Timezone handling
   - Version: Latest stable
   - Features used: UTC conversion, timezone-aware datetimes

4. **GitHub Actions**
   - Purpose: Automated workflow execution
   - Features used: Scheduled runs, Python environment, Git operations

## External Services

### FootballWebPages API

- **Endpoint**: `https://www.footballwebpages.co.uk/api/fixtures-results.json`
- **Authentication**: Football Web Pages API key (Query parameter: `key`)
- **Parameters**:
  - `team`: 1169 (Larkhall Athletic ID)
- **Rate Limits**: Unknown (assumed to be sufficient for daily updates)
- **Response Format**: JSON
- **Key Data Points**:
  - Fixture dates and times
  - Opponents
  - Venues
  - Competition information
  - Match status

### GitHub Pages

- **Purpose**: Host the generated .ics file
- **URL Pattern**: `https://[username].github.io/larkhall-calendar/fixtures.ics`
- **Update Mechanism**: Automatic via Git push
- **Limitations**: Static file hosting only

## Development Environment

### Requirements

- Python 3.9+ installed
- Git client
- GitHub account
- Text editor or IDE
- Internet connection for API access

### Setup Steps

1. Clone repository
2. Install Python dependencies: `pip install -r requirements.txt`
3. Set up environment variables for API key
4. Run local tests

### Local Testing

- Execute script manually: `python update_calendar.py`
- Validate .ics output with calendar applications
- Verify API responses with test fixtures

## Deployment Environment

### GitHub Actions Configuration

- **Trigger**: Scheduled (daily) and manual
- **Environment**: Ubuntu latest
- **Python Version**: 3.9
- **Environment Variables**:
  - `FOOTBALL_WEB_PAGES_API_KEY`: Secret API key for FootballWebPages

### GitHub Pages Configuration

- **Source Branch**: `main`
- **Publishing Directory**: Root or `/docs`
- **Custom Domain**: None (default GitHub Pages domain)

## Technical Constraints

### API Limitations

- Dependent on FootballWebPages API availability
- Limited control over data format and content
- Potential for unexpected API changes

### Calendar Format Limitations

- Limited formatting options in iCalendar standard
- No support for rich media (images, videos)
- Subscription update frequency controlled by client applications

### Hosting Limitations

- GitHub Pages limited to static content
- File size limits (not expected to be an issue)
- No server-side processing

## Data Management

### Data Storage

- Primary storage: Git repository
- Calendar file: fixtures.ics
- No database required

### Data Retention

- Only current and future fixtures included
- Historical data not maintained
- Previous versions available through Git history

### Data Privacy

- All data is public information
- No personal user data collected or stored
- No analytics or tracking implemented

## Monitoring and Logging

### GitHub Actions Logs

- Execution history
- Error messages
- Update timestamps

### Manual Verification

- Periodic checks of calendar content
- Validation against official sources

## Backup and Recovery

### Version Control

- All changes tracked in Git
- Easy rollback to previous versions

### Failure Recovery

- Automated retry logic for API failures
- Fallback to previous calendar data if update fails
