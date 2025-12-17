#!/usr/bin/env python3
"""
Test script for the FootballWebPages API

This script makes a test call to the FootballWebPages API to understand
the response structure and verify that the API key works correctly.

Usage:
    python test_api.py

Environment Variables:
    FOOTBALL_WEB_PAGES_API_KEY: API key for FootballWebPages API (required)
    (RAPIDAPI_KEY is also supported for backward compatibility)

Author: ElDataDude
Version: 1.0.0
Last Updated: March 28, 2025
"""

import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Constants
TEAM_ID = 1169  # Larkhall Athletic
API_ENDPOINT = "https://api.footballwebpages.co.uk/v2/fixtures-results.json"


def get_api_key():
    """Retrieve the API key from environment variables."""
    api_key = os.environ.get("FOOTBALL_WEB_PAGES_API_KEY") or os.environ.get(
        "RAPIDAPI_KEY"
    )
    if not api_key:
        raise EnvironmentError(
            "API key not found. Please set the FOOTBALL_WEB_PAGES_API_KEY environment variable."
        )
    return api_key


def test_api():
    """Make a test call to the API and print the response structure."""
    api_key = get_api_key()

    headers = {
        "FWP-API-Key": api_key
    }
    params = {
        "team": TEAM_ID
    }

    print(f"Making API request to {API_ENDPOINT} for team ID {TEAM_ID}...")

    try:
        response = requests.get(API_ENDPOINT, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Print the response status and headers
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {json.dumps(dict(response.headers), indent=2)}")
        
        # Print the structure of the response
        print("\nResponse Structure:")
        print_structure(data)
        
        # Print the full response (limited to avoid excessive output)
        print("\nSample Response Data (first 2 fixtures if available):")
        if "fixtures" in data and isinstance(data["fixtures"], list):
            fixtures = data["fixtures"][:2]  # Limit to first 2 fixtures
            print(json.dumps(fixtures, indent=2))
            print(f"\nTotal fixtures in response: {len(data['fixtures'])}")
        else:
            print(json.dumps(data, indent=2))
        
    except requests.RequestException as e:
        print(f"API request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response Status: {e.response.status_code}")
            print(f"Response Body: {e.response.text}")


def print_structure(data, prefix="", is_last=True, max_depth=3, current_depth=0):
    """
    Print the structure of a nested dictionary or list.
    
    Args:
        data: The data to print the structure of
        prefix: The prefix to print before each line
        is_last: Whether this is the last item in the current level
        max_depth: Maximum depth to print
        current_depth: Current depth in the nested structure
    """
    if current_depth > max_depth:
        print(f"{prefix}{'└── ' if is_last else '├── '}...")
        return
    
    if isinstance(data, dict):
        for i, (key, value) in enumerate(data.items()):
            is_last_item = i == len(data) - 1
            print(f"{prefix}{'└── ' if is_last else '├── '}{key}: {type(value).__name__}")
            if isinstance(value, (dict, list)) and value:
                print_structure(
                    value,
                    prefix=f"{prefix}{'    ' if is_last else '│   '}",
                    is_last=is_last_item,
                    max_depth=max_depth,
                    current_depth=current_depth + 1
                )
    elif isinstance(data, list) and data:
        print(f"{prefix}{'└── ' if is_last else '├── '}list[{len(data)}]")
        if data:
            # Print structure of first item as example
            print_structure(
                data[0],
                prefix=f"{prefix}{'    ' if is_last else '│   '}",
                is_last=True,
                max_depth=max_depth,
                current_depth=current_depth + 1
            )


if __name__ == "__main__":
    test_api()
