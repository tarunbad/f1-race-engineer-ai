PIT_LOSS_TIME = {
    "Bahrain": 22,
    "Monaco": 28,
    "Monza": 24,
    "default": 23,
}

TYRE_MAX_LAPS = {
    "SOFT": 25,
    "MEDIUM": 35,
    "HARD": 50,
    "INTER": 30,
    "WET": 30,
}

NEXT_COMPOUND = {
    "SOFT": "MEDIUM",
    "MEDIUM": "HARD",
    "HARD": "MEDIUM",
    "INTER": "WET",
    "WET": "INTER",
}

def parse_time(t: str) -> float:
    parts = t.split(":")
    return float(parts[0]) * 60 + float(parts[1])

def calculate_strategy(laps: list, total_laps: int, track: str = "default") -> dict:
    if not laps:
        return {}

    current = laps[-1]
    if not current:
        return {}

    lap_number = current.get("lap_number", 0)
    compound = current.get("compound")
    tyre_life = current.get("tyre_life", 0)
    position = current.get("position", 0)
    laps_remaining = total_laps - lap_number
    pit_loss = PIT_LOSS_TIME.get(track, PIT_LOSS_TIME["default"])
    max_tyre_life = TYRE_MAX_LAPS.get(compound, 35)
    laps_left_on_tyre = max_tyre_life - tyre_life

    # --- UNDERCUT WINDOW ---
    undercut_recommended = False
    undercut_reason = None
    if position > 1 and laps_left_on_tyre <= 8 and laps_remaining > 10:
        undercut_recommended = True
        undercut_reason = (
            f"Only {laps_left_on_tyre} laps left on {compound}. "
            f"Pit now to undercut P{position - 1} before they react."
        )

    # --- OVERCUT WINDOW ---
    overcut_recommended = False
    overcut_reason = None
    if position > 1 and laps_left_on_tyre >= 10 and laps_remaining > 15:
        overcut_recommended = True
        overcut_reason = (
            f"Tyres still have {laps_left_on_tyre} laps. "
            f"Stay out and overcut P{position - 1} if they pit first."
        )

    # --- OPTIMAL PIT LAP ---
    optimal_pit_lap = lap_number + max(1, laps_left_on_tyre - 3)
    if optimal_pit_lap > total_laps - 5:
        optimal_pit_lap = None

    # --- AVERAGE LAP TIME ---
    race_laps = [l for l in laps if l.get("lap_time") and not l.get("pit_in") and not l.get("pit_out")]
    avg_lap_time = None
    if len(race_laps) >= 3:
        times = [parse_time(l["lap_time"]) for l in race_laps[-5:]]
        avg_lap_time = round(sum(times) / len(times), 3)

    # --- TYRE DELTA ---
    next_compound = NEXT_COMPOUND.get(compound, "MEDIUM")
    tyre_delta_estimate = None
    if compound == "SOFT":
        tyre_delta_estimate = "+0.3s on MEDIUM but lasts 10 more laps"
    elif compound == "MEDIUM":
        tyre_delta_estimate = "+0.5s on HARD but lasts 15 more laps"
    elif compound == "HARD":
        tyre_delta_estimate = "-0.5s on MEDIUM but 15 fewer laps"

    return {
        "lap_number": lap_number,
        "laps_remaining": laps_remaining,
        "current_compound": compound,
        "tyre_life": tyre_life,
        "laps_left_on_tyre": laps_left_on_tyre,
        "optimal_pit_lap": optimal_pit_lap,
        "recommended_next_compound": next_compound,
        "tyre_delta": tyre_delta_estimate,
        "avg_lap_time_last_5": avg_lap_time,
        "pit_loss_seconds": pit_loss,
        "undercut": {
            "recommended": undercut_recommended,
            "reason": undercut_reason
        },
        "overcut": {
            "recommended": overcut_recommended,
            "reason": overcut_reason
        }
    }