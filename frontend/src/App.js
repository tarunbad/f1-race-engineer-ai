import { useEffect, useState, useRef } from 'react';
import io from 'socket.io-client';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine, AreaChart, Area } from 'recharts';
import './App.css';

const socket = io('http://localhost:8000');

const BahrainCircuit = ({ racing }) => (
  <div style={{width: '100%', height: '160px', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative'}}>
    <img
      src="/bahrain_circuit.png"
      alt="Bahrain Circuit"
      style={{
        height: '100%',
        width: '100%',
        objectFit: 'contain',
        filter: 'drop-shadow(0 0 12px rgba(0,212,255,0.4))',
        opacity: 0.9
      }}
    />
    {racing && (
      <div style={{
        position: 'absolute',
        bottom: '8px',
        right: '8px',
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        fontSize: '9px',
        color: '#00ff88',
        fontFamily: 'monospace',
        letterSpacing: '2px'
      }}>
        <div style={{
          width: '6px', height: '6px',
          borderRadius: '50%',
          background: '#00ff88',
          animation: 'pulse 0.8s infinite'
        }}></div>
        LIVE
      </div>
    )}
  </div>
);

function App() {
  const [connected, setConnected] = useState(false);
  const [racing, setRacing] = useState(false);
  const [lapData, setLapData] = useState(null);
  const [log, setLog] = useState([]);
  const [done, setDone] = useState(false);
  const [lapTimeHistory, setLapTimeHistory] = useState([]);
  const [tyreHistory, setTyreHistory] = useState([]);
  const [deltaHistory, setDeltaHistory] = useState([]);
  const [gapHistory, setGapHistory] = useState([]);
  const logRef = useRef(null);
  const avgRef = useRef(null);

  const playRadioBeep = () => {
    return new Promise((resolve) => {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const beep = (startTime, freq, duration) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.frequency.value = freq;
        osc.type = 'sine';
        gain.gain.setValueAtTime(0, startTime);
        gain.gain.linearRampToValueAtTime(0.3, startTime + 0.01);
        gain.gain.linearRampToValueAtTime(0.3, startTime + duration - 0.01);
        gain.gain.linearRampToValueAtTime(0, startTime + duration);
        osc.start(startTime);
        osc.stop(startTime + duration);
      };
      const now = ctx.currentTime;
      beep(now, 1200, 0.08);
      beep(now + 0.12, 1200, 0.08);
      beep(now + 0.24, 1200, 0.08);
      setTimeout(() => { ctx.close(); resolve(); }, 400);
    });
  };

  const speak = async (text) => {
    if (!text) return;
    await playRadioBeep();
    window.speechSynthesis.cancel();
    const clean = text.replace(/[""]/g, '');
    const utterance = new SpeechSynthesisUtterance(clean);
    utterance.rate = 1.05;
    utterance.pitch = 0.9;
    utterance.volume = 1;
    const voices = window.speechSynthesis.getVoices();
    const preferred = voices.find(v =>
      v.name.includes('Daniel') ||
      v.name.includes('Google UK') ||
      v.name.includes('British') ||
      v.name.includes('Arthur') ||
      v.name.includes('James') ||
      v.name.includes('Alex')
    );
    if (preferred) utterance.voice = preferred;
    window.speechSynthesis.speak(utterance);
  };

  useEffect(() => {
    socket.on('connect', () => setConnected(true));
    socket.on('disconnect', () => setConnected(false));

    socket.on('lap_update', (data) => {
      setLapData(data);
      setLog(prev => [...prev, data]);
      if (data.ai_message) speak(data.ai_message);

      const lapTime = data.strategy?.avg_lap_time_last_5;
      const lapNum = data.lap;
      const tyreLife = data.strategy?.tyre_life;
      const compound = data.strategy?.current_compound;

      if (data.gaps?.gap_ahead !== null && data.gaps?.gap_ahead !== undefined) {
        setGapHistory(prev => [...prev, {
          lap: data.lap,
          ahead: data.gaps.gap_ahead,
          behind: data.gaps.gap_behind || 0
        }]);
      }

      if (lapTime) {
        setLapTimeHistory(prev => {
          const next = [...prev, { lap: lapNum, time: lapTime, compound }];
          if (!avgRef.current && next.length >= 3) avgRef.current = lapTime;
          if (avgRef.current) {
            const delta = parseFloat((lapTime - avgRef.current).toFixed(3));
            setDeltaHistory(d => [...d, { lap: lapNum, delta, compound }]);
          }
          return next;
        });
      }

      if (tyreLife !== undefined) {
        const max = { SOFT: 25, MEDIUM: 35, HARD: 50, INTER: 30, WET: 30 };
        const pct = Math.max(0, Math.min(100, (1 - tyreLife / (max[compound] || 35)) * 100));
        setTyreHistory(prev => [...prev, { lap: lapNum, wear: parseFloat(pct.toFixed(1)), compound }]);
      }
    });

    socket.on('race_complete', () => { setRacing(false); setDone(true); });
    return () => socket.off();
  }, []);

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [log]);

  useEffect(() => {
    window.speechSynthesis.getVoices();
  }, []);

  const startRace = () => {
    setLog([]); setDone(false); setRacing(true);
    setLapTimeHistory([]); setTyreHistory([]); setDeltaHistory([]);
    setGapHistory([]);
    avgRef.current = null;
    socket.emit('start_race', {});
  };

  const getCompoundClass = (c) => c?.toLowerCase() || '';

  const getTyreHealth = (life, compound) => {
    const max = { SOFT: 25, MEDIUM: 35, HARD: 50, INTER: 30, WET: 30 };
    return Math.max(0, Math.min(100, ((max[compound] || 35) - life) / (max[compound] || 35) * 100));
  };

  const getTyreColor = (health) => {
    if (health > 70) return '#ff6b6b';
    if (health > 40) return '#ffd93d';
    return '#00ff88';
  };

  const progress = lapData ? (lapData.lap / lapData.total_laps) * 100 : 0;
  const tyreHealth = lapData ? getTyreHealth(lapData.strategy?.tyre_life, lapData.strategy?.current_compound) : 0;

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div style={{ background: '#0c1018', border: '1px solid #1e2535', padding: '8px 12px', borderRadius: '6px', fontSize: '11px' }}>
          <div style={{ color: '#445', marginBottom: '4px' }}>LAP {label}</div>
          {payload.map((p, i) => (
            <div key={i} style={{ color: p.color }}>{p.name}: {p.value}</div>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="app">
      <div className="header">
      <h1>PitWall AI</h1>
        <div className="header-right">
          <div className="status">
            <span className={`dot ${connected ? 'green' : 'red'}`}></span>
            {connected ? 'Live' : 'Offline'}
          </div>
        </div>
      </div>

      <div className="main-grid">
        <div className="left-panel">

          {/* LAP COUNTER */}
          <div className="lap-counter">
            <div className="lap-number">{lapData?.lap ?? '--'}</div>
            <div className="lap-label">
              <span>Current Lap</span>
              <span>of {lapData?.total_laps ?? '--'}</span>
            </div>
            <div className="lap-progress">
              <div className="lap-progress-bar" style={{ width: `${progress}%` }}></div>
            </div>
          </div>

          {/* CIRCUIT + STATS — always visible */}
          <div className="circuit-row">
            <div className="circuit-card">
              <div className="circuit-title">
                <span>Bahrain International Circuit</span>
                <span className="circuit-sub">Round 1 · 2023 · 57 Laps</span>
              </div>
              <div className="circuit-svg">
                <BahrainCircuit racing={racing} />
              </div>
            </div>
            <div className="circuit-stats">
              <div className="cstat">
                <div className="cstat-label">Circuit Length</div>
                <div className="cstat-value">5.412 <span>km</span></div>
              </div>
              <div className="cstat">
                <div className="cstat-label">Race Distance</div>
                <div className="cstat-value">308.238 <span>km</span></div>
              </div>
              <div className="cstat">
                <div className="cstat-label">DRS Zones</div>
                <div className="cstat-value">3 <span>zones</span></div>
              </div>
              <div className="cstat">
                <div className="cstat-label">Pit Loss</div>
                <div className="cstat-value">22 <span>sec</span></div>
              </div>
              <div className="cstat">
                <div className="cstat-label">Race Winner</div>
                <div className="cstat-value" style={{fontSize: '14px', color: '#ffd93d'}}>VER 🏆</div>
              </div>
              <div className="cstat">
                <div className="cstat-label">Fastest Lap</div>
                <div className="cstat-value" style={{fontSize: '14px', color: '#c084fc'}}>PER 💜</div>
              </div>
            </div>
          </div>

          {/* TELEMETRY CARDS */}
          <div className="telemetry-grid">
            <div className="telem-card">
              <div className="telem-label">Compound</div>
              <div className={`telem-value ${getCompoundClass(lapData?.strategy?.current_compound)}`}>
                {lapData?.strategy?.current_compound ?? '--'}
              </div>
              <div className="telem-sub">Life: {lapData?.strategy?.tyre_life ?? '--'} laps</div>
              <div className="tyre-bar-wrap">
                <div className="tyre-bar" style={{ width: `${tyreHealth}%`, background: getTyreColor(tyreHealth) }}></div>
              </div>
            </div>

            <div className="telem-card">
              <div className="telem-label">Optimal Pit</div>
              <div className="telem-value">
                {lapData?.strategy?.optimal_pit_lap ? `L${lapData.strategy.optimal_pit_lap}` : 'N/A'}
              </div>
              <div className="telem-sub">Next: {lapData?.strategy?.recommended_next_compound ?? '--'}</div>
            </div>

            <div className="telem-card">
              <div className="telem-label">Laps Remaining</div>
              <div className="telem-value">{lapData?.strategy?.laps_remaining ?? '--'}</div>
              <div className="telem-sub">Avg: {lapData?.strategy?.avg_lap_time_last_5 ?? '--'}s</div>
            </div>

            <div className="telem-card">
              <div className="telem-label">Tyre Life Left</div>
              <div className="telem-value" style={{ color: getTyreColor(tyreHealth) }}>
                {lapData?.strategy?.laps_left_on_tyre ?? '--'}
              </div>
              <div className="telem-sub">laps remaining</div>
            </div>

            <div className="telem-card">
              <div className="telem-label">Pit Loss</div>
              <div className="telem-value">{lapData?.strategy?.pit_loss_seconds ?? '--'}</div>
              <div className="telem-sub">seconds in pitlane</div>
            </div>

            <div className="telem-card">
              <div className="telem-label">Tyre Delta</div>
              <div className="telem-value" style={{ fontSize: '13px', paddingTop: '4px', color: '#00d4ff' }}>
                {lapData?.strategy?.tyre_delta ?? '--'}
              </div>
            </div>
          </div>

          {/* GAP TRACKER */}
          {lapData?.gaps && (
            <div className="gap-tracker">
              <div className="gap-card ahead">
                <div className="gap-label">Gap to Ahead</div>
                <div className="gap-driver">{lapData.gaps.driver_ahead || 'N/A'}</div>
                <div className="gap-value" style={{
                  color: lapData.gaps.gap_ahead < 1 ? '#ff6b6b' : lapData.gaps.gap_ahead < 3 ? '#ffd93d' : '#00ff88'
                }}>
                  {lapData.gaps.gap_ahead ? `+${lapData.gaps.gap_ahead}s` : 'N/A'}
                </div>
                <div className="gap-status">
                  {lapData.gaps.gap_ahead < 1 ? 'DRS Range' : lapData.gaps.gap_ahead < 3 ? 'Closing' : 'Safe'}
                </div>
              </div>

              <div className="gap-chart-wrap">
                <div className="chart-title">Gap History <span>seconds</span></div>
                <ResponsiveContainer width="100%" height={100}>
                  <LineChart data={gapHistory} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                    <XAxis dataKey="lap" tick={{ fill: '#445', fontSize: 9 }} tickLine={false} axisLine={false} />
                    <YAxis tick={{ fill: '#445', fontSize: 9 }} tickLine={false} axisLine={false} domain={['auto', 'auto']} />
                    <Tooltip content={<CustomTooltip />} />
                    <Line type="monotone" dataKey="ahead" name="Gap Ahead" stroke="#00d4ff" strokeWidth={1.5} dot={false} />
                    <Line type="monotone" dataKey="behind" name="Gap Behind" stroke="#ffd93d" strokeWidth={1.5} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              <div className="gap-card behind">
                <div className="gap-label">Gap Behind</div>
                <div className="gap-driver">{lapData.gaps.driver_behind || 'N/A'}</div>
                <div className="gap-value" style={{
                  color: lapData.gaps.gap_behind < 1 ? '#ff6b6b' : lapData.gaps.gap_behind < 3 ? '#ffd93d' : '#00ff88'
                }}>
                  {lapData.gaps.gap_behind ? `-${lapData.gaps.gap_behind}s` : 'N/A'}
                </div>
                <div className="gap-status">
                  {lapData.gaps.gap_behind < 1 ? 'Under Threat' : lapData.gaps.gap_behind < 3 ? 'Closing' : 'Safe'}
                </div>
              </div>
            </div>
          )}

          {/* CHARTS ROW */}
          <div className="charts-row">
            <div className="chart-card">
              <div className="chart-title">Lap Time Trend <span>seconds</span></div>
              <ResponsiveContainer width="100%" height={120}>
                <AreaChart data={lapTimeHistory} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="lapGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#00d4ff" stopOpacity={0.2} />
                      <stop offset="95%" stopColor="#00d4ff" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="lap" tick={{ fill: '#445', fontSize: 9 }} tickLine={false} axisLine={false} />
                  <YAxis tick={{ fill: '#445', fontSize: 9 }} tickLine={false} axisLine={false} domain={['auto', 'auto']} />
                  <Tooltip content={<CustomTooltip />} />
                  <Area type="monotone" dataKey="time" name="Lap Time" stroke="#00d4ff" strokeWidth={1.5} fill="url(#lapGrad)" dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-card">
              <div className="chart-title">Tyre Wear <span>% degraded</span></div>
              <ResponsiveContainer width="100%" height={120}>
                <AreaChart data={tyreHistory} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="tyreGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#ffd93d" stopOpacity={0.2} />
                      <stop offset="95%" stopColor="#ffd93d" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="lap" tick={{ fill: '#445', fontSize: 9 }} tickLine={false} axisLine={false} />
                  <YAxis tick={{ fill: '#445', fontSize: 9 }} tickLine={false} axisLine={false} domain={[0, 100]} />
                  <Tooltip content={<CustomTooltip />} />
                  <Area type="monotone" dataKey="wear" name="Wear %" stroke="#ffd93d" strokeWidth={1.5} fill="url(#tyreGrad)" dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-card">
              <div className="chart-title">Pace Delta <span>vs baseline</span></div>
              <ResponsiveContainer width="100%" height={120}>
                <AreaChart data={deltaHistory} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="deltaGradNeg" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#00ff88" stopOpacity={0.2} />
                      <stop offset="95%" stopColor="#00ff88" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="lap" tick={{ fill: '#445', fontSize: 9 }} tickLine={false} axisLine={false} />
                  <YAxis tick={{ fill: '#445', fontSize: 9 }} tickLine={false} axisLine={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <ReferenceLine y={0} stroke="#1e2535" strokeDasharray="3 3" />
                  <Area type="monotone" dataKey="delta" name="Delta" stroke="#00ff88" strokeWidth={1.5} fill="url(#deltaGradNeg)" dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* EVENTS */}
          {lapData?.events?.length > 0 && (
            <div className="events-section">
              {lapData.events.map((e, i) => (
                <div key={i} className="event-row"
                  style={{ borderColor: e.severity === 'HIGH' ? '#ff6b6b' : e.severity === 'MEDIUM' ? '#ffd93d' : '#6bcb77' }}>
                  <span className={`event-severity sev-${e.severity}`}>{e.severity}</span>
                  <span className="event-text">{e.message}</span>
                </div>
              ))}
            </div>
          )}

          {/* RADIO */}
          <div className="radio-section">
            {lapData?.human_message && (
              <div className="radio-msg human">
                <div className="radio-who">Human Engineer</div>
                <div className="radio-text">"{lapData.human_message}"</div>
              </div>
            )}
            {lapData?.conflict?.conflict && (
              <div className="radio-msg conflict">
                <div className="radio-who">⚠ Conflict — {lapData.conflict.severity}</div>
                <div className="radio-text conflict-data">{lapData.conflict.data_says}</div>
                <div className="conflict-rec">{lapData.conflict.recommendation}</div>
              </div>
            )}
            {lapData?.ai_message && (
              <div className="radio-msg ai">
                <div className="radio-who">AI Engineer</div>
                <div className="radio-text">"{lapData.ai_message}"</div>
              </div>
            )}
          </div>

        </div>

        {/* RIGHT PANEL */}
        <div className="right-panel">
          <div className="right-panel-header">Race Log</div>
          <div className="log-scroll" ref={logRef}>
            {log.map((d, i) => (
              <div key={i} className={`log-item ${d.conflict?.conflict ? 'has-conflict' : ''} ${i === log.length - 1 ? 'active' : ''}`}>
                <div className="log-item-top">
                  <span className="log-lap-num">LAP {d.lap}</span>
                  {d.conflict?.conflict && <span className="log-conflict-badge">CONFLICT</span>}
                </div>
                {d.ai_message && <div className="log-ai-text">"{d.ai_message}"</div>}
              </div>
            ))}
          </div>
          <div className="bottom-bar">
            <button onClick={startRace} disabled={racing || !connected} className="start-btn">
              {racing ? '...' : done ? 'Replay' : 'Start'}
            </button>
            {racing ? (
              <div className="racing-indicator"><div className="racing-dot"></div>Race in progress</div>
            ) : (
              <div className="race-status">{done ? 'Race complete' : 'Ready to simulate'}</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;