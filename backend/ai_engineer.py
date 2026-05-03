from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are an F1 race engineer AI. Communicate with the driver 
clearly, calmly and concisely — exactly like a real F1 race engineer on the radio.

Rules:
- Keep messages SHORT — max 2-3 sentences
- Be data-driven and specific — use actual numbers
- Stay calm even in urgent situations
- Prioritize the most critical info first
- Sound like a real engineer, not a robot
- Never say "I" — address the driver directly
- Use F1 radio style: "Box this lap", "Push now", "Tyres are gone"
"""

def get_engineer_message(events: list, strategy: dict, lap_number: int) -> str:
    if not events and not strategy:
        return None

    events_text = "\n".join([
        f"- [{e['severity']}] {e['type']}: {e['message']}" 
        for e in events
    ])

    strategy_text = f"""
Current lap: {lap_number}
Compound: {strategy.get('current_compound')}
Tyre life: {strategy.get('tyre_life')} laps
Laps left on tyre: {strategy.get('laps_left_on_tyre')}
Optimal pit lap: {strategy.get('optimal_pit_lap') or 'N/A'}
Recommended next compound: {strategy.get('recommended_next_compound')}
Laps remaining: {strategy.get('laps_remaining')}
Undercut: {strategy.get('undercut', {}).get('reason') or 'Not recommended'}
Overcut: {strategy.get('overcut', {}).get('reason') or 'Not recommended'}
"""

    prompt = f"""Race situation on lap {lap_number}:

EVENTS DETECTED:
{events_text if events_text else 'None'}

STRATEGY DATA:
{strategy_text}

Give a short radio message to the driver. Be calm, specific, and use real F1 engineer language."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        max_tokens=150,
        temperature=0.7
    )

    return response.choices[0].message.content