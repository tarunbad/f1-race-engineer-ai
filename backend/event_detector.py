TYRE_MAX_LAPS = {
    "SOFT": 25,
    "MEDIUM": 35,
    "HARD": 50,
    "INTER": 30,
    "WET": 30,
}

TYRE_CLIFF_WARNING = 0.80

def detect_events(laps: list, total_laps: int, session=None) -> list:
    events = []

    if len(laps) < 2:
        return events

    current = laps[-1]
    previous = laps[-2]

    # --- TYRE CLIFF WARNING ---
    compound = current.get("compound")
    tyre_life = current.get("tyre_life")
    if compound and tyre_life:
        max_life = TYRE_MAX_LAPS.get(compound, 35)
        if tyre_life >= int(max_life * TYRE_CLIFF_WARNING):
            events.append({
                "type": "TYRE_CLIFF_WARNING",
                "message": f"Tyre cliff approaching — {compound} on lap {tyre_life} of ~{max_life}",
                "severity": "HIGH"
            })

    # --- PIT WINDOW OPEN ---
    lap_number = current.get("lap_number")
    if compound and tyre_life and lap_number:
        max_life = TYRE_MAX_LAPS.get(compound, 35)
        window_open = tyre_life >= int(max_life * 0.5)
        window_close = tyre_life < int(max_life * TYRE_CLIFF_WARNING)
        if window_open and window_close:
            events.append({
                "type": "PIT_WINDOW_OPEN",
                "message": f"Pit window is open — {compound} tyre on life {tyre_life}",
                "severity": "MEDIUM"
            })

    # --- LAP TIME DEGRADATION ---
    current_time = current.get("lap_time")
    previous_time = previous.get("lap_time")
    if current_time and previous_time:
        try:
            def parse_time(t):
                parts = t.split(":")
                return float(parts[0]) * 60 + float(parts[1])
            curr_sec = parse_time(current_time)
            prev_sec = parse_time(previous_time)
            delta = curr_sec - prev_sec
            if delta > 1.5:
                events.append({
                    "type": "LAP_TIME_DEGRADATION",
                    "message": f"Lap time dropped by {delta:.2f}s — possible tyre deg or traffic",
                    "severity": "MEDIUM"
                })
        except Exception:
            pass

    # --- SAFETY CAR ---
    if session:
        try:
            messages = session.race_control_messages
            if messages is not None and not messages.empty:
                sc_messages = messages[messages['Message'].str.contains(
                    'SAFETY CAR DEPLOYED|VIRTUAL SAFETY CAR DEPLOYED', case=False, na=False
                )]
                if not sc_messages.empty and lap_number:
                    for _, msg in sc_messages.iterrows():
                        msg_lap = getattr(msg, 'Lap', None)
                        if msg_lap is not None and int(msg_lap) == lap_number:
                            events.append({
                                "type": "SAFETY_CAR",
                                "message": f"Race control: {msg['Message']}",
                                "severity": "HIGH"
                            })
        except Exception:
            pass

    # --- FINAL LAPS ---
    if lap_number and total_laps:
        laps_remaining = total_laps - lap_number
        if 1 <= laps_remaining <= 5:
            events.append({
                "type": "FINAL_LAPS",
                "message": f"Only {laps_remaining} laps remaining — manage the gap",
                "severity": "LOW"
            })

    return events