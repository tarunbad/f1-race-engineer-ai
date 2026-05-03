import fastf1
import pandas as pd
import os

fastf1.Cache.enable_cache('data/cache')

def load_session(year: int, grand_prix: str, session_type: str = 'R'):
    print(f"Loading {year} {grand_prix} {session_type}...")
    session = fastf1.get_session(year, grand_prix, session_type)
    session.load()
    return session

def get_race_state(session, driver_number: str):
    laps = session.laps.pick_drivers(driver_number)

    state = {
        "driver": driver_number,
        "total_laps": int(session.total_laps),
        "laps": []
    }

    for _, lap in laps.iterrows():
        lap_data = {
            "lap_number": int(lap['LapNumber']) if pd.notna(lap['LapNumber']) else None,
            "lap_time": f"{int(lap['LapTime'].total_seconds() // 60)}:{lap['LapTime'].total_seconds() % 60:06.3f}" if pd.notna(lap['LapTime']) else None,
            "compound": lap['Compound'] if pd.notna(lap['Compound']) else None,
            "tyre_life": int(lap['TyreLife']) if pd.notna(lap['TyreLife']) else None,
            "position": int(lap['Position']) if pd.notna(lap['Position']) else None,
            "pit_in": pd.notna(lap['PitInTime']),
            "pit_out": pd.notna(lap['PitOutTime']),
        }
        state["laps"].append(lap_data)

    return state

def get_gap_to_ahead(session, driver_number: str, lap_number: int):
    lap = session.laps.pick_drivers(driver_number)
    lap = lap[lap['LapNumber'] == lap_number]
    if lap.empty:
        return None
    pos = lap.iloc[0]['Position']
    if pd.isna(pos) or pos <= 1:
        return None
    ahead_laps = session.laps[
        (session.laps['LapNumber'] == lap_number) &
        (session.laps['Position'] == pos - 1)
    ]
    if ahead_laps.empty:
        return None
    return {
        "driver_ahead": ahead_laps.iloc[0]['Driver'],
        "position": int(pos)
    }

def get_gaps_for_lap(session, driver_number: str, lap_number: int):
    try:
        all_laps = session.laps
        driver_lap = all_laps[
            (all_laps['Driver'] == session.get_driver(driver_number)['Abbreviation']) &
            (all_laps['LapNumber'] == lap_number)
        ]

        if driver_lap.empty:
            return {"gap_ahead": None, "gap_behind": None, "driver_ahead": None, "driver_behind": None}

        current_pos = driver_lap.iloc[0]['Position']
        if not current_pos or str(current_pos) == 'nan':
            return {"gap_ahead": None, "gap_behind": None, "driver_ahead": None, "driver_behind": None}

        current_pos = int(current_pos)

        lap_group = all_laps[all_laps['LapNumber'] == lap_number].copy()
        lap_group = lap_group.dropna(subset=['Position'])
        lap_group['Position'] = lap_group['Position'].astype(int)

        ahead = lap_group[lap_group['Position'] == current_pos - 1]
        behind = lap_group[lap_group['Position'] == current_pos + 1]

        def calc_gap(row_a, row_b):
            try:
                t_a = row_a.iloc[0]['LapTime']
                t_b = row_b.iloc[0]['LapTime']
                if hasattr(t_a, 'total_seconds') and hasattr(t_b, 'total_seconds'):
                    return round(abs(t_a.total_seconds() - t_b.total_seconds()), 3)
            except:
                pass
            return None

        gap_ahead = calc_gap(ahead, driver_lap) if not ahead.empty else None
        gap_behind = calc_gap(driver_lap, behind) if not behind.empty else None

        driver_ahead = ahead.iloc[0]['Driver'] if not ahead.empty else None
        driver_behind = behind.iloc[0]['Driver'] if not behind.empty else None

        return {
            "gap_ahead": gap_ahead,
            "gap_behind": gap_behind,
            "driver_ahead": driver_ahead,
            "driver_behind": driver_behind,
            "position": current_pos
        }
    except Exception as e:
        return {"gap_ahead": None, "gap_behind": None, "driver_ahead": None, "driver_behind": None}