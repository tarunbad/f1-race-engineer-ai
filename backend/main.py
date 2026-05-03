from data_pipeline import load_session, get_race_state
from event_detector import detect_events
from strategy_engine import calculate_strategy
from ai_engineer import get_engineer_message
from conflict_detector import detect_conflict

session = load_session(2023, 'Bahrain', 'R')
state = get_race_state(session, '1')

# Simulated engineer messages per lap — this is what the human engineer says
SIMULATED_ENGINEER_MESSAGES = {
    9:  "Pit window is open, stay out for now",
    14: "Lap time dropping, stay out, we'll box next lap",
    34: "Tyre cliff warning, stay out, push for 2 more laps",
    36: "Box this lap, mediums ready",
    41: "VSC deployed, stay out, tyres are fine",
    52: "Five laps to go, push hard",
}

KEY_LAPS = list(SIMULATED_ENGINEER_MESSAGES.keys())

print("=== F1 RACE ENGINEER AI — CONFLICT DETECTOR ===\n")

for i in range(2, len(state['laps']) + 1):
    laps_so_far = state['laps'][:i]
    current_lap = laps_so_far[-1]['lap_number']

    if current_lap not in KEY_LAPS:
        continue

    events = detect_events(laps_so_far, state['total_laps'], session)
    strategy = calculate_strategy(laps_so_far, state['total_laps'], track='Bahrain')
    human_message = SIMULATED_ENGINEER_MESSAGES[current_lap]

    print(f"--- LAP {current_lap} ---")
    print(f"  HUMAN ENGINEER: \"{human_message}\"")

    conflict = detect_conflict(human_message, events, strategy)

    if conflict and conflict["conflict"]:
        print(f"  ⚠️  CONFLICT DETECTED [{conflict['severity']}]")
        print(f"  DATA SAYS: {conflict['data_says']}")
        print(f"  {conflict['recommendation']}")
    else:
        print(f"  OK: No conflict detected")

    print(f"  Calling AI engineer...")
    ai_message = get_engineer_message(events, strategy, current_lap)
    print(f"  AI ENGINEER: \"{ai_message}\"")
    print()