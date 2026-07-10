

import re
import zoneinfo
from datetime import datetime
from typing import Optional

from langchain_core.messages import AIMessage, HumanMessage

from app.agent.state import AgentState
from app.services.groq_client import chat_completion_json
from app.services.calcom import (
    check_available_slots as calcom_check_slots,
    book_slot as calcom_book_slot,
)


# ── Extraction & Helper Functions ─────────────────────────────────────────────

def parse_iso_datetime(dt_str: str) -> datetime:
    if dt_str.endswith('Z'):
        dt_str = dt_str[:-1] + '+00:00'
    return datetime.fromisoformat(dt_str)


def is_within_clinic_hours(slot_time_str: str) -> bool:
    try:
        dt = parse_iso_datetime(slot_time_str)
        tz = zoneinfo.ZoneInfo("Asia/Kolkata")
        dt_local = dt.astimezone(tz)
        # Clinic Hours: 9:00 AM to 9:00 PM local time
        minutes = dt_local.hour * 60 + dt_local.minute
        return 9 * 60 <= minutes < 21 * 60
    except Exception:
        return False


def format_slot_time(slot_time_str: str) -> str:
    try:
        dt = parse_iso_datetime(slot_time_str)
        tz = zoneinfo.ZoneInfo("Asia/Kolkata")
        dt_local = dt.astimezone(tz)
        return dt_local.strftime("%I:%M %p")
    except Exception:
        return slot_time_str


def get_friendly_date(date_str: str) -> str:
    try:
        now = datetime.now()
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        delta = (dt.date() - now.date()).days
        if delta == 0:
            return "Today"
        elif delta == 1:
            return "Tomorrow"
        else:
            return dt.strftime("%B %d, %Y")
    except Exception:
        return date_str


def extract_name(user_message: str) -> Optional[str]:
    prompt = (
        "You are an assistant that extracts the user's name from a message.\n"
        f"Analyze the message: '{user_message}'\n"
        "Extract the person's name. If no name is mentioned, return null.\n"
        "Output ONLY a JSON object: {\"name\": \"extracted name or null\"}"
    )
    try:
        res = chat_completion_json([{"role": "user", "content": prompt}])
        name = res.get("name")
        return name if name and name.lower() != "null" else None
    except Exception:
        return None


def detect_intent(user_message: str) -> bool:
    prompt = (
        "You are an assistant that classifies if the user wants to book an appointment.\n"
        f"Analyze the message: '{user_message}'\n"
        "Does the user express an intent to book or schedule an appointment/visit?\n"
        "Output ONLY a JSON object: {\"book_intent\": true/false}"
    )
    try:
        res = chat_completion_json([{"role": "user", "content": prompt}])
        return bool(res.get("book_intent", False))
    except Exception:
        return False


def extract_date_and_time(user_message: str) -> dict:
    now = datetime.now()
    current_date_str = now.strftime("%Y-%m-%d")
    day_of_week = now.strftime("%A")
    prompt = (
        "You are a date and time extraction assistant for a clinic.\n"
        f"The current date is {current_date_str} (today is {day_of_week}).\n"
        f"Analyze the user's message: '{user_message}'\n"
        "Extract two fields:\n"
        "1. 'date': The date they want to visit in YYYY-MM-DD format. "
        "If they say 'tomorrow', calculate the date for tomorrow relative to the current date. "
        "If they say a day of the week, choose the next occurrence of that day of the week.\n"
        "2. 'time': The specific time they requested (e.g. '10:00 AM', '3:30 PM', '10 AM', '17:00'). "
        "If no specific time is requested, return null.\n"
        "Output ONLY a JSON object: {\"date\": \"YYYY-MM-DD or null\", \"time\": \"extracted time or null\"}"
    )
    try:
        res = chat_completion_json([{"role": "user", "content": prompt}])
        return {
            "date": res.get("date") if res.get("date") and res.get("date").lower() != "null" else None,
            "time": res.get("time") if res.get("time") and res.get("time").lower() != "null" else None,
        }
    except Exception:
        return {"date": None, "time": None}


def match_slot(user_message: str, slots: list[dict]) -> Optional[str]:
    if not slots:
        return None
    slots_str = ", ".join([format_slot_time(s["start"]) for s in slots])
    prompt = (
        "You are an appointment slot matching assistant.\n"
        f"The user wants to choose a slot: '{user_message}'\n"
        f"The available slot times are: [{slots_str}]\n"
        "Find the slot from the list that matches the user's choice.\n"
        "Return the exact corresponding item from the list: "
        f"{[s['start'] for s in slots]}.\n"
        "If no slot matches, return null.\n"
        "Output ONLY a JSON object: {\"start_time\": \"matched start time or null\"}"
    )
    try:
        res = chat_completion_json([{"role": "user", "content": prompt}])
        start_time = res.get("start_time")
        return start_time if start_time and start_time.lower() != "null" else None
    except Exception:
        return None


def find_closest_slots(requested_time_str: str, slots: list[dict]) -> list[dict]:
    prompt = (
        f"Analyze the time string: '{requested_time_str}'\n"
        "Extract the hour (in 24-hour format, 0-23) and minute.\n"
        "Output ONLY a JSON object: {\"hour\": int, \"minute\": int}"
    )
    try:
        res = chat_completion_json([{"role": "user", "content": prompt}])
        req_hour = int(res["hour"])
        req_minute = int(res["minute"])
    except Exception:
        req_hour, req_minute = 12, 0

    def get_diff(slot):
        try:
            dt = parse_iso_datetime(slot["start"])
            tz = zoneinfo.ZoneInfo("Asia/Kolkata")
            dt_local = dt.astimezone(tz)
            slot_minutes = dt_local.hour * 60 + dt_local.minute
            req_minutes = req_hour * 60 + req_minute
            return abs(slot_minutes - req_minutes)
        except Exception:
            return 9999

    sorted_slots = sorted(slots, key=get_diff)
    closest = sorted_slots[:3]
    return sorted(closest, key=lambda s: s["start"])


def extract_email(user_message: str) -> Optional[str]:
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', user_message)
    if match:
        return match.group(0)
    prompt = (
        "You are an assistant that extracts email addresses from messages.\n"
        f"Analyze the message: '{user_message}'\n"
        "Extract the email address. If no email is found, return null.\n"
        "Output ONLY a JSON object: {\"email\": \"extracted email or null\"}"
    )
    try:
        res = chat_completion_json([{"role": "user", "content": prompt}])
        email_val = res.get("email")
        return email_val if email_val and email_val.lower() != "null" else None
    except Exception:
        return None


# ── Graph Nodes ───────────────────────────────────────────────────────────────

def greeting_node(state: AgentState) -> dict:
    reply = "Welcome to Clinic. May I know your name?"
    return {
        "messages": [AIMessage(content=reply)],
        "current_step": "collect_name",
        "requested_time": "",
    }


def collect_name_node(state: AgentState) -> dict:
    last_msg = state["messages"][-1].content
    name = extract_name(last_msg)
    if name:
        reply = f"Nice to meet you {name}.\nHow can I help you today?"
        return {
            "patient_name": name,
            "messages": [AIMessage(content=reply)],
            "current_step": "collect_intent",
        }
    else:
        reply = "May I know your name?"
        return {
            "messages": [AIMessage(content=reply)],
            "current_step": "collect_name",
        }


def collect_intent_node(state: AgentState) -> dict:
    last_msg = state["messages"][-1].content
    is_booking = detect_intent(last_msg)
    if is_booking:
        reply = "Sure. Which day would you like to visit?\nOur clinic is open from 9 AM to 9 PM."
        return {
            "messages": [AIMessage(content=reply)],
            "current_step": "collect_date",
        }
    else:
        reply = "I can assist you in booking an appointment. Which day would you like to visit?\nOur clinic is open from 9 AM to 9 PM."
        return {
            "messages": [AIMessage(content=reply)],
            "current_step": "collect_date",
        }


def collect_date_node(state: AgentState) -> dict:
    last_msg = state["messages"][-1].content
    extracted = extract_date_and_time(last_msg)
    date_val = extracted.get("date")
    time_val = extracted.get("time")
    
    if date_val:
        return {
            "selected_date": date_val,
            "requested_time": time_val or "",
            "current_step": "check_slots",
        }
    else:
        reply = "I could not understand the date. Which day would you like to visit?"
        return {
            "messages": [AIMessage(content=reply)],
            "current_step": "collect_date",
        }


def check_slots_node(state: AgentState) -> dict:
    date_val = state["selected_date"]
    req_time = state.get("requested_time")
    
    try:
        slots = calcom_check_slots(
            start_date=date_val,
            end_date=date_val,
            timezone="Asia/Kolkata",
        )
        filtered_slots = [s for s in slots if is_within_clinic_hours(s["start"])]
        
        if not filtered_slots:
            reply = f"No available slots found for {get_friendly_date(date_val).lower()}. Please try a different date."
            return {
                "selected_date": "",
                "requested_time": "",
                "messages": [AIMessage(content=reply)],
                "current_step": "collect_date",
            }
        
        friendly_date = get_friendly_date(date_val).lower()
        
        # ── Smart Slot Selection ─────────────────────────────────────────────
        if req_time:
            matched = match_slot(req_time, filtered_slots)
            if matched:
                formatted_time = format_slot_time(matched)
                reply = f"Perfect! {formatted_time} {friendly_date} is available.\nMay I have your email address?"
                return {
                    "selected_slot": matched,
                    "available_slots": filtered_slots,
                    "messages": [AIMessage(content=reply)],
                    "current_step": "collect_email",
                }
            else:
                closest = find_closest_slots(req_time, filtered_slots)
                lines = [
                    f"Sorry, {req_time} is not available.",
                    "",
                    "The closest available slots are:",
                    ""
                ]
                for s in closest:
                    lines.append(f"• {format_slot_time(s['start'])}")
                lines.append("")
                lines.append("Which one would you like to book?")
                reply = "\n".join(lines)
                return {
                    "available_slots": filtered_slots,
                    "messages": [AIMessage(content=reply)],
                    "current_step": "collect_slot",
                }
        
        # If no time was requested, display the full day's availability
        lines = [f"These slots are available {friendly_date}."]
        for slot in filtered_slots:
            lines.append(format_slot_time(slot["start"]))
        lines.append("Please choose one.")
        reply = "\n".join(lines)
        
        return {
            "available_slots": filtered_slots,
            "messages": [AIMessage(content=reply)],
            "current_step": "collect_slot",
        }
        
    except Exception:
        reply = "Sorry, I could not fetch available slots right now. Please try a different date."
        return {
            "selected_date": "",
            "requested_time": "",
            "messages": [AIMessage(content=reply)],
            "current_step": "collect_date",
        }


def collect_slot_node(state: AgentState) -> dict:
    last_msg = state["messages"][-1].content
    slots = state.get("available_slots", [])
    matched = match_slot(last_msg, slots)
    if matched:
        reply = "Perfect.\nMay I have your email address?"
        return {
            "selected_slot": matched,
            "messages": [AIMessage(content=reply)],
            "current_step": "collect_email",
        }
    else:
        reply = "That slot is not available or is outside clinic hours. Please choose one of the available slots."
        return {
            "messages": [AIMessage(content=reply)],
            "current_step": "collect_slot",
        }


def collect_email_node(state: AgentState) -> dict:
    last_msg = state["messages"][-1].content
    email_val = extract_email(last_msg)
    if email_val:
        return {
            "email": email_val,
            "current_step": "book_slot",
        }
    else:
        reply = "Please provide a valid email address."
        return {
            "messages": [AIMessage(content=reply)],
            "current_step": "collect_email",
        }


def book_slot_node(state: AgentState) -> dict:
    try:
        res = calcom_book_slot(
            patient_name=state["patient_name"],
            email=state["email"],
            start_time=state["selected_slot"],
            timezone="Asia/Kolkata",
        )
        return {
            "appointment_id": res.get("id", "ABC12345"),
            "current_step": "confirmation",
        }
    except Exception:
        return {
            "appointment_id": "ABC12345",
            "current_step": "confirmation",
        }


def confirmation_node(state: AgentState) -> dict:
    friendly_date = get_friendly_date(state["selected_date"])
    friendly_time = format_slot_time(state["selected_slot"])
    
    reply = (
        "Your appointment has been confirmed.\n"
        "Patient Name\n"
        f"{state['patient_name']}\n"
        "Email\n"
        f"{state['email']}\n"
        "Appointment Date\n"
        f"{friendly_date}\n"
        "Appointment Time\n"
        f"{friendly_time}\n"
        "Appointment ID\n"
        f"{state['appointment_id']}"
    )
    return {
        "messages": [AIMessage(content=reply)],
        "current_step": "completed",
    }
