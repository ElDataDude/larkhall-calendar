# FootballWebPages API Documentation

## API Overview

The FootballWebPages API provides access to football-related data, including fixtures, results, league tables, and team information. For the Larkhall Athletic Fixtures Calendar project, we primarily use the fixtures-results endpoint to retrieve upcoming matches.

## Authentication

The API is accessed through RapidAPI and requires an API key for authentication:

- **API Key**: `6d626c9a04msh0f4f53d3232ec82p1b9746jsn7c06d25015f0`
- **Header**: `X-RapidAPI-Key`

## Endpoints

### Fixtures and Results

```
GET https://football-web-pages1.p.rapidapi.com/fixtures-results.json
```

#### Parameters

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| team | Yes | Team ID | 1169 (Larkhall Athletic) |

#### Headers

| Header | Value |
|--------|-------|
| X-RapidAPI-Key | 6d626c9a04msh0f4f53d3232ec82p1b9746jsn7c06d25015f0 |

#### Example Request

```python
import requests

url = "https://football-web-pages1.p.rapidapi.com/fixtures-results.json"
querystring = {"team": "1169"}
headers = {
    "X-RapidAPI-Key": "6d626c9a04msh0f4f53d3232ec82p1b9746jsn7c06d25015f0"
}

response = requests.get(url, headers=headers, params=querystring)
```

#### Response Structure

The API returns a JSON object containing fixture information. The exact structure needs to be confirmed through testing, but based on the provided information, it likely includes:

```json
{
  "fixtures": [
    {
      "id": "12345",
      "date": "2025-04-05T15:00:00Z",
      "competition": "League",
      "home_team": {
        "id": "1169",
        "name": "Larkhall Athletic"
      },
      "away_team": {
        "id": "789",
        "name": "Opponent FC"
      },
      "venue": "Plain Ham",
      "status": "scheduled"
    },
    // Additional fixtures...
  ]
}
```

### League Table

```
GET https://football-web-pages1.p.rapidapi.com/league-table.json
```

#### Parameters

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| team | Yes | Team ID | 1169 (Larkhall Athletic) |

#### Headers

| Header | Value |
|--------|-------|
| X-RapidAPI-Key | 6d626c9a04msh0f4f53d3232ec82p1b9746jsn7c06d25015f0 |

#### Example Request

```python
import requests

url = "https://football-web-pages1.p.rapidapi.com/league-table.json"
querystring = {"team": "1169"}
headers = {
    "X-RapidAPI-Key": "6d626c9a04msh0f4f53d3232ec82p1b9746jsn7c06d25015f0"
}

response = requests.get(url, headers=headers, params=querystring)
```

## Team Information

Based on the provided information, the following teams are in Larkhall Athletic's league:

| Team ID | Full Name | Short Name |
|---------|-----------|------------|
| 250 | Bashley | Bashley |
| 677 | Bemerton Heath Harlequins | BH Harlequins |
| 412 | Bideford | Bideford |
| 387 | Bishops Cleeve | Bishops C |
| 835 | Bristol Manor Farm | Bristol Manor Farm |
| 1509 | Cribbs | Cribbs |
| 213 | Evesham United | Evesham |
| 1866 | Exmouth Town | Exmouth Town |
| 851 | Frome Town | Frome |
| 1431 | Hamworthy United | Hamworthy Utd |
| 1169 | Larkhall Athletic | Larkhall Athletic |
| 388 | Malvern Town | Malvern |
| 863 | Melksham Town | Melksham Town |
| 2522 | Mousehole AFC | Mousehole AFC |
| 217 | Paulton Rovers | Paulton |
| 795 | Tavistock | Tavistock |
| 912 | Westbury United | Westbury United |
| 471 | Willand Rovers | Willand R |
| 914 | Wimborne Town | Wimborne |
| 224 | Yate Town | Yate Town |

## Error Handling

The API may return various HTTP status codes:

- **200**: Successful request
- **401**: Unauthorized (invalid API key)
- **404**: Resource not found
- **500**: Internal server error

## Rate Limits

The specific rate limits for the FootballWebPages API through RapidAPI are not explicitly stated in the provided information. However, for our daily update use case, we should be well within typical API rate limits.

## API Testing Notes

Initial API testing is required to:

1. Confirm the exact response structure
2. Identify all available data fields
3. Understand how fixture statuses are represented
4. Determine how postponed/cancelled matches are handled
5. Verify the format of dates and times

## Implementation Considerations

1. **Error Handling**: Implement robust error handling for API failures
2. **Caching**: Consider caching responses to reduce API calls
3. **Data Validation**: Validate all data received from the API
4. **Date Handling**: Ensure proper timezone handling for fixture dates
5. **Status Monitoring**: Track API reliability over time
