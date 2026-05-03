CONFLICT_RULES = {
    "stay out": {
        "check": lambda events, strategy: any(
            e["type"] in ["TYRE_CLIFF_WARNING"] for e in events
        ),
        "conflict_message": "Data says tyres are at cliff — staying out risks losing significant time.",
        "severity": "HIGH"
    },
    "push": {
        "check": lambda events, strategy: any(
            e["type"] == "TYRE_CLIFF_WARNING" for e in events
        ),
        "conflict_message": "Tyres are degrading fast — pushing will accelerate cliff drop.",
        "severity": "MEDIUM"
    },
    "box next lap": {
        "check": lambda events, strategy: (
            strategy.get("optimal_pit_lap") is not None and
            strategy.get("lap_number", 0) < strategy.get("optimal_pit_lap", 0) - 2
        ),
        "conflict_message": lambda events, strategy: (
            f"Data suggests optimal pit is lap {strategy.get('optimal_pit_lap')} — boxing early loses track position."
        ),
        "severity": "MEDIUM"
    },
    "box this lap": {
        "check": lambda events, strategy: (
            strategy.get("laps_left_on_tyre", 99) > 8 and
            not any(e["type"] == "SAFETY_CAR" for e in events)
        ),
        "conflict_message": lambda events, strategy: (
            f"Tyres still have {strategy.get('laps_left_on_tyre')} laps left — boxing now loses track position unnecessarily."
        ),
        "severity": "LOW"
    },
}

def detect_conflict(engineer_message: str, events: list, strategy: dict) -> dict:
    if not engineer_message:
        return None

    msg_lower = engineer_message.lower().strip()

    for trigger, rule in CONFLICT_RULES.items():
        if trigger in msg_lower:
            has_conflict = rule["check"](events, strategy)
            if has_conflict:
                conflict_msg = rule["conflict_message"]
                if callable(conflict_msg):
                    conflict_msg = conflict_msg(events, strategy)
                return {
                    "conflict": True,
                    "trigger": trigger,
                    "severity": rule["severity"],
                    "engineer_said": engineer_message,
                    "data_says": conflict_msg,
                    "recommendation": f"AI recommends: {get_ai_recommendation(events, strategy)}"
                }

    return {"conflict": False, "engineer_said": engineer_message}


def get_ai_recommendation(events: list, strategy: dict) -> str:
    high_events = [e for e in events if e["severity"] == "HIGH"]
    
    if any(e["type"] == "SAFETY_CAR" for e in events):
        return "Box this lap — free pit stop under safety car"
    
    if any(e["type"] == "TYRE_CLIFF_WARNING" for e in events):
        opt = strategy.get("optimal_pit_lap")
        compound = strategy.get("recommended_next_compound", "MEDIUM")
        return f"Box on lap {opt} for {compound} — tyre cliff imminent"
    
    if any(e["type"] == "PIT_WINDOW_OPEN" for e in events):
        opt = strategy.get("optimal_pit_lap")
        compound = strategy.get("recommended_next_compound", "MEDIUM")
        return f"Pit window open — optimal stop lap {opt} on {compound}"

    return "Maintain current strategy"