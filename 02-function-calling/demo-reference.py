"""
================================================================================
WanderBot — DEMO: Function Calling
================================================================================
"""
import json
from pathlib import Path

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import current_time  # ← built-in: no code needed

# ---------------------------------------------------------------------------
# App and model setup
# ---------------------------------------------------------------------------
app = BedrockAgentCoreApp()

MODEL_ID = "us.amazon.nova-2-lite-v1:0"
model = BedrockModel(model_id=MODEL_ID)

SYSTEM_PROMPT = """You are WanderBot, the AI travel assistant for Horizon Travel.

You have access to real-time tools:
- current_time: find out the current date and time
- search_flights: search available Horizon Travel flights by route and date
- search_hotels: find hotels in a specific city with optional price filtering

Use these tools to give customers accurate, up-to-date information.
When a customer asks about flights or hotels, always use the appropriate
search tool rather than guessing. State clearly when you're searching.

Keep responses friendly, well-structured, and actionable."""

# ---------------------------------------------------------------------------
# Resolve dataset paths relative to this file
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "datasets"


# ===========================================================================
# CUSTOM TOOLS (using the @tool decorator)
# ===========================================================================

@tool
def search_flights(origin: str, destination: str, date: str) -> str:
    """
    Search for available Horizon Travel flights between two airports on a given date.

    Use this tool whenever a customer asks about flight availability,
    departure times, prices, or seat availability between two cities.

    Args:
        origin      : IATA airport code for the departure airport (e.g. 'LHR', 'JFK', 'BCN')
        destination : IATA airport code for the arrival airport (e.g. 'CDG', 'MIA', 'FCO')
        date        : Travel date in YYYY-MM-DD format (e.g. '2026-03-15')

    Returns:
        A formatted summary of matching flights, or a message if none found.
    """

    with open(DATA_DIR / "flights.json") as f:
        all_flights = json.load(f)
  

    # Filter by route and date (case-insensitive)
    origin_upper = origin.upper().strip()
    dest_upper = destination.upper().strip()

    matching = [
        fl for fl in all_flights
        if fl["origin"].upper() == origin_upper
        and fl["destination"].upper() == dest_upper
        and fl["date"] == date
    ]

    if not matching:
        return (
            f"No Horizon Travel flights found from {origin_upper} to {dest_upper} "
            f"on {date}. Try an adjacent date or a different route."
        )

    lines = [f"✈️  Flights from {origin_upper} → {dest_upper} on {date}:\n"]
    for fl in matching:
        status_icon = {"SCHEDULED": "🟢", "DELAYED": "🟡", "CANCELLED": "🔴"}.get(fl["status"], "⚪")
        gate_info = f"Gate {fl['gate']}" if fl.get("gate") else "Gate TBA"
        seats = f"{fl['available_seats']} seats left" if fl["available_seats"] > 0 else "SOLD OUT"
        lines.append(
            f"  {status_icon} {fl['flight_number']}  |  {fl['departure_time']} → {fl['arrival_time']}  "
            f"|  {fl['cabin_class']}  |  ${fl['price_usd']:.2f}  |  {seats}  |  {gate_info}  |  {fl['aircraft']}"
        )

    return "\n".join(lines)


@tool
def search_hotels(city: str, max_price_usd: float = 999.0) -> str:
    """
    Search for available hotels in a city, with an optional maximum nightly price.

    Use this tool when a customer asks about accommodation options,
    hotel prices, amenities, room types, or check-in/check-out policies.

    Args:
        city          : Destination city name (e.g. 'Barcelona', 'Tokyo', 'Dubai', 'Rome')
        max_price_usd : Optional maximum price per night in USD. Defaults to no limit (999).

    Returns:
        A formatted list of matching hotels with prices, ratings, and amenities.
    """

    try:
        with open(DATA_DIR / "hotels.json") as f:
            all_hotels = json.load(f)
    except FileNotFoundError:
        return "Error: Hotel database is temporarily unavailable. Please try again."

    # Filter by city (case-insensitive) and price
    city_lower = city.lower().strip()
    matching = [
        h for h in all_hotels
        if h["city"].lower() == city_lower
        and h["available"]
        and h["price_per_night_usd"] <= max_price_usd
    ]

    if not matching:
        return (
            f"No available hotels found in {city} under ${max_price_usd:.0f}/night. "
            f"Try increasing your budget or check a nearby city."
        )

    stars_map = {5: "⭐⭐⭐⭐⭐", 4: "⭐⭐⭐⭐", 3: "⭐⭐⭐", 2: "⭐⭐", 1: "⭐"}
    lines = [f"🏨  Available hotels in {city.title()} (max ${max_price_usd:.0f}/night):\n"]

    for h in sorted(matching, key=lambda x: x["price_per_night_usd"]):
        amenity_summary = ", ".join(h["amenities"][:3])  # show first 3 amenities
        lines.append(
            f"  {stars_map.get(h['star_rating'], '')} {h['name']}\n"
            f"     ${h['price_per_night_usd']:.0f}/night  |  Rooms: {', '.join(h['room_types'])}\n"
            f"     Amenities: {amenity_summary}  |  Check-in: {h['check_in_time']}\n"
            f"     Cancellation: {h['cancellation_policy']}\n"
        )

    return "\n".join(lines)


# ===========================================================================
# ENTRY POINT
# ===========================================================================

@app.entrypoint
async def invoke(payload, context=None):
    
    user_message = payload.get("message", "Hello!")

    agent = Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[
            current_time,       # ← built-in: no implementation needed
            search_flights,     # ← custom: reads flights.json
            search_hotels,      # ← custom: reads hotels.json
        ],
    )

    response = agent(user_message)

    return response


if __name__ == "__main__":
    app.run()
