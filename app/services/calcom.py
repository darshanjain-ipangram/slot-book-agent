"""
Cal.com API v2 service.

Two methods only:
  - check_available_slots()  →  GET  /v2/slots
  - book_slot()              →  POST /v2/bookings

Docs:
  Slots   : https://cal.com/docs/api-reference/v2/slots
  Bookings: https://cal.com/docs/api-reference/v2/bookings/create-a-booking
"""

import requests

from app.config.settings import CALCOM_API_KEY, CALCOM_BASE_URL, CALCOM_EVENT_TYPE_ID


# ── Shared headers ────────────────────────────────────────────────────────────

def _slots_headers() -> dict:
    """
    Headers for the /v2/slots endpoint.
    cal-api-version value is taken from the official v2 slots documentation.
    """
    return {
        "Authorization": f"Bearer {CALCOM_API_KEY}",
        "Content-Type": "application/json",
        "cal-api-version": "2024-09-04",
    }


def _bookings_headers() -> dict:
    """
    Headers for the /v2/bookings endpoint.
    cal-api-version value is taken from the official v2 bookings documentation.
    """
    return {
        "Authorization": f"Bearer {CALCOM_API_KEY}",
        "Content-Type": "application/json",
        "cal-api-version": "2026-02-25",
    }


# ── check_available_slots ─────────────────────────────────────────────────────

def check_available_slots(start_date: str, end_date: str, timezone: str = "UTC") -> list[dict]:
    """
    Fetch available time slots for the configured event type.

    Uses: GET /v2/slots?eventTypeId=X&start=Y&end=Z&timeZone=T&format=range

    Args:
        start_date : ISO 8601 date string for the start of the range (e.g. "2025-07-10").
        end_date   : ISO 8601 date string for the end of the range   (e.g. "2025-07-10").
        timezone   : IANA timezone name. Defaults to "UTC".

    Returns:
        A list of dicts, each with 'start' and 'end' keys (ISO 8601 UTC strings).
        Example: [{"start": "2025-07-10T09:00:00Z", "end": "2025-07-10T09:30:00Z"}, ...]

    Raises:
        RuntimeError: If the Cal.com API returns a non-200 response.
    """
    url = f"{CALCOM_BASE_URL}/slots"

    params = {
        "eventTypeId": CALCOM_EVENT_TYPE_ID,
        "start": start_date,
        "end": end_date,
        "timeZone": timezone,
        "format": "range",   # Returns {start, end} objects instead of plain strings
    }

    response = requests.get(url, headers=_slots_headers(), params=params, timeout=15)

    if response.status_code != 200:
        raise RuntimeError(
            f"Cal.com slots API error {response.status_code}: {response.text}"
        )

    body = response.json()

    slots_by_date = body.get("data", {})

    # Flatten all dates into a single list
    all_slots = []
    for date_str, slot_list in slots_by_date.items():
        if isinstance(slot_list, list):
            for slot in slot_list:
                all_slots.append({
                    "start": slot.get("start", ""),
                    "end": slot.get("end", ""),
                })

    return all_slots


# ── book_slot ─────────────────────────────────────────────────────────────────

def book_slot(
    patient_name: str,
    email: str,
    start_time: str,
    timezone: str = "UTC",
) -> dict:
    """
    Create a booking on Cal.com for the configured event type.

    Uses: POST /v2/bookings

    Args:
        patient_name : Full name of the patient.
        email        : Patient's email address.
        start_time   : ISO 8601 UTC datetime string (e.g. "2025-07-10T09:00:00Z").
        timezone     : IANA timezone for the attendee. Defaults to "UTC".

    Returns:
        A dict with booking details from the Cal.com response:
        {
            "booking_uid" : "...",
            "id"          : 123,
            "status"      : "accepted",
            "start"       : "...",
            "end"         : "...",
            "meeting_url" : "...",
        }

    Raises:
        RuntimeError: If the Cal.com API returns a non-200/201 response.
    """
    url = f"{CALCOM_BASE_URL}/bookings"

    payload = {
        "eventTypeId": CALCOM_EVENT_TYPE_ID,
        "start": start_time,          # Must be ISO 8601 UTC, e.g. "2025-07-10T09:00:00Z"
        "attendee": {
            "name": patient_name,
            "email": email,
            "timeZone": timezone,
            "language": "en",
        },
    }

    response = requests.post(url, headers=_bookings_headers(), json=payload, timeout=15)

    if response.status_code not in (200, 201):
        raise RuntimeError(
            f"Cal.com bookings API error {response.status_code}: {response.text}"
        )

    body = response.json()
    data = body.get("data", {})

    return {
        "booking_uid": data.get("uid", ""),
        "id": data.get("id", ""),
        "status": data.get("status", ""),
        "start": data.get("start", ""),
        "end": data.get("end", ""),
        "meeting_url": data.get("meetingUrl", ""),
    }
