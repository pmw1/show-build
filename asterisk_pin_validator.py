#!/usr/bin/env python3
"""
Asterisk PIN Validator for Show-Build Conferences

This script validates conference PINs by checking the Show-Build backend API.
Called from Asterisk dialplan to verify if a conference with the given PIN exists.

Usage from Asterisk dialplan:
    Set(CONF_EXISTS=${SHELL(python3 /app/asterisk_pin_validator.py ${CONFERENCE_PIN})})
"""

import sys
import requests

SHOW_BUILD_API = "http://192.168.51.210:8888"
API_KEY = "FDT5WyO7S2DbBifbDUEsd1H8cmZTT3_qpJXtb3c7qaY"


def validate_pin(pin):
    """
    Validate conference PIN against Show-Build backend

    Args:
        pin: 6-digit conference PIN

    Returns:
        "valid" if conference exists, "invalid" otherwise
    """
    try:
        # Query active conferences
        response = requests.get(
            f"{SHOW_BUILD_API}/api/voice/conference/",
            headers={"X-API-Key": API_KEY},
            timeout=2
        )

        if response.status_code == 200:
            data = response.json()
            conferences = data.get('conferences', [])

            # Check if any conference has this PIN
            for conf in conferences:
                if conf.get('pin') == pin:
                    return "valid"

        return "invalid"

    except Exception as e:
        # Log error but return invalid to prevent access
        sys.stderr.write(f"PIN validation error: {e}\n")
        return "invalid"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("invalid")
        sys.exit(1)

    pin = sys.argv[1]
    result = validate_pin(pin)
    print(result)
