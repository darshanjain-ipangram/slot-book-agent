
from langchain_core.tools import tool

from app.services.calcom import (
    check_available_slots as calcom_check_slots,
    book_slot as calcom_book_slot,
)


@tool
def check_available_slots(date: str, timezone: str = "UTC") -> str:
    """
    Check available appointment slots for a given date at the clinic.

    Calls the real Cal.com API v2 GET /v2/slots endpoint.
    """
    try:
        slots = calcom_check_slots(
            start_date=date,
            end_date=date,
            timezone=timezone,
        )

        if not slots:
            return f"No available slots found for {date}. Please try a different date."

        lines = [f"Available slots for {date}:"]
        for i, slot in enumerate(slots, start=1):
            start = slot["start"]
            end = slot["end"]
            lines.append(f"  {i}. {start}  →  {end}")

        return "\n".join(lines)

    except RuntimeError as e:
        return f"Sorry, I could not fetch available slots right now. Details: {e}"


@tool
def book_slot(
    patient_name: str,
    email: str,
    start_time: str,
    timezone: str = "UTC",
) -> str:
    """
    Book an appointment slot for a patient at the clinic.
    """
    try:
        result = calcom_book_slot(
            patient_name=patient_name,
            email=email,
            start_time=start_time,
            timezone=timezone,
        )

        meeting_info = (
            f"\n  Meeting link   : {result['meeting_url']}"
            if result.get("meeting_url")
            else ""
        )

        return (
            f"Appointment confirmed!\n"
            f"  Booking ID     : {result['booking_uid']}\n"
            f"  Patient        : {patient_name}\n"
            f"  Email          : {email}\n"
            f"  Start time     : {result['start']}\n"
            f"  End time       : {result['end']}\n"
            f"  Status         : {result['status']}"
            f"{meeting_info}"
        )

    except RuntimeError as e:
        return f"Sorry, I could not complete the booking right now. Details: {e}"
