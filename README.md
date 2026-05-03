# 🏎️ F1 Race Engineer AI

An AI-powered race engineer that monitors live F1 telemetry, detects strategy conflicts, and communicates like a real pit wall engineer — solving the breakdown between drivers and engineers that costs teams race wins.

## 🎯 Problem

In F1, strategy disagreements between drivers and engineers cost race wins:
- **Monaco 2022** — Ferrari told Leclerc to stay out, he lost the win
- **Silverstone 2023** — Hamilton ignored pit call, cost him position  
- **Abu Dhabi 2021** — Entire championship came down to a strategy call

When communication breaks down or human bias creeps in — positions and championships are lost.

## 💡 Solution

A real-time AI system that:
- **Monitors** live telemetry lap by lap
- **Detects** when human engineer calls contradict the data
- **Recommends** data-backed strategy in real time
- **Communicates** via natural radio-style voice messages

## 🏗️ Architecture
FastF1 API → Data Pipeline → Event Detector → Strategy Engine
↓
Conflict Detector
↓
AI Engineer (LLM)
↓
React Dashboard + Voice

## ⚙️ Tech Stack

**Backend**
- Python + FastAPI + WebSockets
- FastF1 — real F1 telemetry data
- Groq API (Llama 3.3 70B) — AI engineer brain
- Custom strategy + conflict detection engine

**Frontend**
- React + Recharts — live telemetry charts
- Web Speech API — voice output
- Web Audio API — F1 radio beep sound

## 🚀 Features

- ✅ Real F1 telemetry data — lap times, tyre compounds, positions
- ✅ Live event detection — tyre cliff, pit windows, safety car, degradation
- ✅ Strategy engine — optimal pit laps, undercut/overcut recommendations
- ✅ Conflict detector — flags when engineer call contradicts data
- ✅ AI engineer — communicates like a real F1 race engineer on radio
- ✅ Voice layer — F1 radio beep + speech synthesis
- ✅ Live dashboard with telemetry cards and charts
- ✅ Gap tracker — live gap to car ahead and behind
- ✅ Lap time trend, tyre wear, pace delta charts
- ✅ Race log with conflict badges

## 📦 Setup

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install fastf1 pandas python-dotenv fastapi uvicorn websockets python-socketio groq
```

Create a `.env` file in the backend folder:
GROQ_API_KEY
Run the backend:
```bash
uvicorn server:socket_app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm start
```

Open http://localhost:3000 and click **Start Race Simulation**!

## 🎙️ How It Works

1. FastF1 loads real Bahrain 2023 race data
2. System replays the race lap by lap via WebSockets
3. Every lap — events detected, strategy calculated, gaps tracked
4. If human engineer message contradicts data — conflict is flagged
5. AI engineer generates a calm, data-backed radio message
6. Dashboard updates live with telemetry, charts, and gap data
7. Voice speaks the AI message with authentic F1 radio beep

## 🔮 Roadmap

- [ ] Live F1 timing stream integration for real race weekends
- [ ] Multi-driver comparison and team strategy view
- [ ] Weather-based strategy adjustments
- [ ] Mobile app for in-car driver use
- [ ] Historical conflict analysis across full seasons

## 👨‍💻 Author

Built by [@tarunbad](https://github.com/tarunbad)
