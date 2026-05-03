import asyncio
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio
from data_pipeline import load_session, get_race_state
from event_detector import detect_events
from strategy_engine import calculate_strategy
from ai_engineer import get_engineer_message
from conflict_detector import detect_conflict
from data_pipeline import load_session, get_race_state, get_gaps_for_lap

app = FastAPI()
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
socket_app = socketio.ASGIApp(sio, app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SIMULATED_ENGINEER_MESSAGES = {
    9:  "Pit window is open, stay out for now",
    14: "Lap time dropping, stay out, we'll box next lap",
    34: "Tyre cliff warning, stay out, push for 2 more laps",
    36: "Box this lap, mediums ready",
    41: "VSC deployed, stay out, tyres are fine",
    52: "Five laps to go, push hard",
}

@app.get("/")
async def root():
    return {"status": "F1 Race Engineer AI running"}

@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")

@sio.event
async def start_race(sid, data):
    print("Starting race simulation...")
    session = load_session(2023, 'Bahrain', 'R')
    state = get_race_state(session, '1')

    for i in range(2, len(state['laps']) + 1):
        laps_so_far = state['laps'][:i]
        current_lap = laps_so_far[-1]['lap_number']

        events = detect_events(laps_so_far, state['total_laps'], session)
        gaps = get_gaps_for_lap(session, '1', current_lap)
        strategy = calculate_strategy(laps_so_far, state['total_laps'], track='Bahrain')
        human_message = SIMULATED_ENGINEER_MESSAGES.get(current_lap)
        conflict = detect_conflict(human_message, events, strategy) if human_message else None
        ai_message = None

        if events or human_message:
            ai_message = get_engineer_message(events, strategy, current_lap)

        payload = {
            "lap": current_lap,
            "total_laps": state['total_laps'],
            "events": events,
            "strategy": strategy,
            "human_message": human_message,
            "conflict": conflict,
            "ai_message": ai_message,
            "gaps": gaps,
        }

        await sio.emit('lap_update', payload, to=sid)
        await asyncio.sleep(1.5)

    await sio.emit('race_complete', {}, to=sid)