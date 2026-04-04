import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Activity, Server, Database, Ticket, Cpu, MemoryStick, Zap, Plus, AlertTriangle } from 'lucide-react';

const API = 'http://127.0.0.1:5050';
const HISTORY_LENGTH = 200;

export default function App() {
  const [data, setData] = useState({
    database: 'offline',
    available_tickets: 0,
    cpu_percent: 0,
    ram_percent: 0,
    be_instances: 1,
    db_instances: 1
  });

  const [activeEventId, setActiveEventId] = useState(null);
  const [isLoadRunning, setIsLoadRunning] = useState(false);
  const [loadStats, setLoadStats] = useState(null);
  const [ticketCount, setTicketCount] = useState(100);
  const [userCount, setUserCount] = useState(150);

  const [errorLogs, setErrorLogs] = useState([]);

  const smoothRpsRef = useRef(0);
  const historyRef = useRef(new Array(HISTORY_LENGTH).fill(0));
  const canvasRef = useRef(null);
  const animFrameRef = useRef(null);

  // ── Canvas Chart Renderer ──────────────────────────────────
  useEffect(() => {
    const draw = () => {
      const canvas = canvasRef.current;
      if (!canvas) { animFrameRef.current = requestAnimationFrame(draw); return; }
      const ctx = canvas.getContext('2d');
      const dpr = window.devicePixelRatio || 1;
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.scale(dpr, dpr);
      const w = rect.width;
      const h = rect.height;

      ctx.clearRect(0, 0, w, h);

      const pts = historyRef.current;
      const max = Math.max(10, ...pts) * 1.2;
      const step = w / (pts.length - 1);
      const padTop = 24;
      const padBot = 12;
      const plotH = h - padTop - padBot;

      const getY = (val) => padTop + plotH - (val / max) * plotH;

      // Grid lines
      ctx.strokeStyle = '#eee';
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 4]);
      for (let i = 1; i < 4; i++) {
        const y = padTop + (plotH / 4) * i;
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
      }
      ctx.setLineDash([]);

      // Area fill
      ctx.beginPath();
      ctx.moveTo(0, padTop + plotH);
      for (let i = 0; i < pts.length; i++) {
        const x = i * step;
        const y = getY(pts[i]);
        if (i === 0) ctx.lineTo(x, y);
        else {
          const prevX = (i - 1) * step;
          const prevY = getY(pts[i - 1]);
          const cpx = (prevX + x) / 2;
          ctx.bezierCurveTo(cpx, prevY, cpx, y, x, y);
        }
      }
      ctx.lineTo(w, padTop + plotH);
      ctx.closePath();
      const grad = ctx.createLinearGradient(0, padTop, 0, padTop + plotH);
      grad.addColorStop(0, 'rgba(23,23,23,0.08)');
      grad.addColorStop(1, 'rgba(23,23,23,0)');
      ctx.fillStyle = grad;
      ctx.fill();

      // Line
      ctx.beginPath();
      for (let i = 0; i < pts.length; i++) {
        const x = i * step;
        const y = getY(pts[i]);
        if (i === 0) ctx.moveTo(x, y);
        else {
          const prevX = (i - 1) * step;
          const prevY = getY(pts[i - 1]);
          const cpx = (prevX + x) / 2;
          ctx.bezierCurveTo(cpx, prevY, cpx, y, x, y);
        }
      }
      ctx.strokeStyle = '#171717';
      ctx.lineWidth = 1.5;
      ctx.stroke();

      // Current RPS label
      const currentRps = pts[pts.length - 1];
      ctx.fillStyle = '#171717';
      ctx.font = '600 13px "Fira Code", monospace';
      ctx.textAlign = 'right';
      ctx.fillText(`${currentRps.toFixed(1)} req/s`, w - 8, 18);

      animFrameRef.current = requestAnimationFrame(draw);
    };
    animFrameRef.current = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(animFrameRef.current);
  }, []);

  // ── Telemetry Polling ──────────────────────────────────────
  useEffect(() => {
    const fetchTelemetry = async () => {
      try {
        const response = await fetch(`${API}/api/telemetry`);
        const newData = await response.json();

        const raw = newData.rps || 0;
        const alpha = 0.12;
        smoothRpsRef.current = smoothRpsRef.current * (1 - alpha) + raw * alpha;

        historyRef.current = [...historyRef.current.slice(1), Math.round(smoothRpsRef.current * 10) / 10];
        setData(newData);
      } catch {
        smoothRpsRef.current = 0;
        historyRef.current = [...historyRef.current.slice(1), 0];
        setData(prev => ({ ...prev, database: 'offline' }));
      }
    };

    const id = setInterval(fetchTelemetry, 300);
    fetchTelemetry();
    return () => clearInterval(id);
  }, []);

  // ── Error Log Polling ──────────────────────────────────────
  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const res = await fetch(`${API}/api/logs`);
        if (res.ok) {
          const logs = await res.json();
          setErrorLogs(logs);
        }
      } catch { /* ignore */ }
    };
    const logId = setInterval(fetchLogs, 2000);
    fetchLogs();
    return () => clearInterval(logId);
  }, []);

  // ── Launch Flash Sale ──────────────────────────────────────
  const launchSale = useCallback(async () => {
    const name = `FlashSale_${Date.now()}`;
    try {
      const res = await fetch(`${API}/admin/event`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, total_tickets: ticketCount })
      });
      const event = await res.json();
      if (res.ok) {
        setActiveEventId(event.id);
        setLoadStats(null);
      }
    } catch (e) {
      console.error('Failed to create event:', e);
    }
  }, [ticketCount]);

  // ── Simulate Load ──────────────────────────────────────────
  const simulateLoad = useCallback(async () => {
    if (!activeEventId || isLoadRunning) return;
    setIsLoadRunning(true);
    setLoadStats(null);

    const TOTAL = userCount;
    let successes = 0;
    let failures = 0;

    const BATCH_SIZE = Math.min(500, Math.ceil(TOTAL / 4));

    const batch = async (start, count) => {
      const promises = [];
      for (let i = start; i < start + count; i++) {
        promises.push(
          fetch(`${API}/reserve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ event_id: activeEventId, user_email: `user${i}_${Date.now()}@load.test` })
          }).then(r => {
            if (r.status === 201) successes++;
            else failures++;
          }).catch(() => failures++)
        );
      }
      await Promise.all(promises);
    };

    const BATCHES = Math.ceil(TOTAL / BATCH_SIZE);
    for (let b = 0; b < BATCHES; b++) {
      const start = b * BATCH_SIZE;
      const count = Math.min(BATCH_SIZE, TOTAL - start);
      await batch(start, count);
    }

    setLoadStats({ successes, failures, oversold: successes > ticketCount });
    setIsLoadRunning(false);
  }, [activeEventId, isLoadRunning, userCount, ticketCount]);

  const isOnline = data.database === 'online';

  return (
    <div className="dashboard-container">
      <header className="header">
        <div className="header-left">
          <h1>SRE Observability Center</h1>
          <p>Live Flash Sale Traffic & Cluster Health</p>
        </div>
        <div className="header-actions">
          <div className="input-group">
            <label>Tickets</label>
            <input
              type="number"
              className="input-num"
              value={ticketCount}
              onChange={e => setTicketCount(Math.max(1, parseInt(e.target.value) || 1))}
              min="1"
            />
          </div>
          <button className="btn btn-secondary" onClick={launchSale}>
            <Plus size={14} /> New Sale
          </button>
          <div className="input-group">
            <label>Users</label>
            <input
              type="number"
              className="input-num"
              value={userCount}
              onChange={e => setUserCount(Math.max(1, parseInt(e.target.value) || 1))}
              min="1"
            />
          </div>
          <button
            className={`btn btn-primary ${isLoadRunning ? 'btn-loading' : ''}`}
            onClick={simulateLoad}
            disabled={!activeEventId || isLoadRunning}
          >
            <Zap size={14} /> {isLoadRunning ? 'Simulating...' : 'Simulate Load'}
          </button>
        </div>
      </header>

      {/* Load Test Results Banner */}
      {loadStats && (
        <div className={`results-banner ${loadStats.oversold ? 'results-fail' : 'results-pass'}`}>
          {loadStats.oversold
            ? `💥 OVERSOLD — ${loadStats.successes} tickets sold (expected max ${ticketCount})`
            : `✅ INTEGRITY HELD — ${loadStats.successes} sold, ${loadStats.failures} blocked`
          }
        </div>
      )}

      <div className="grid">
        {/* Hero Wave Chart */}
        <div className="card hero-chart">
          <div className="card-title">
            <Activity size={14} /> Live API Traffic (Requests/sec)
          </div>
          <canvas ref={canvasRef} style={{ width: '100%', height: '100%', display: 'block' }} />
        </div>

        {/* Database Health */}
        <div className="card card-health">
          <div className="card-title">
            <Database size={14} /> PostgreSQL
          </div>
          <div className={`status-indicator ${isOnline ? '' : 'status-offline'}`}>
            <div className={`dot ${isOnline ? 'green' : 'red'}`}></div>
            <span>{isOnline ? 'NODE ONLINE' : 'NODE OFFLINE'}</span>
          </div>
        </div>

        {/* Cluster Topology */}
        <div className="card card-cluster">
          <div className="card-title">
            <Server size={14} /> Cluster Topology
          </div>
          <div className="cluster-stats">
            <div className="cluster-stat">
              <label>API Workers</label>
              <span>{data.be_instances}</span>
            </div>
            <div className="cluster-stat">
              <label>Database</label>
              <span>{data.db_instances}</span>
            </div>
          </div>
        </div>

        {/* Flash Sale Pulse */}
        <div className="card card-pulse">
          <div className="card-title">
            <Ticket size={14} /> Flash Sale — Available
          </div>
          <div className="card-value">
            {data.available_tickets}
          </div>
        </div>

        {/* CPU */}
        <div className="card card-vitals">
          <div className="card-title">
            <Cpu size={14} /> CPU Utilization
          </div>
          <div className="vitals-bar-container">
            <div className="vitals-bar" style={{ width: `${Math.min(data.cpu_percent, 100)}%` }}></div>
          </div>
          <div className="vitals-label">{data.cpu_percent.toFixed(1)}%</div>
        </div>

        {/* RAM */}
        <div className="card card-vitals">
          <div className="card-title">
            <MemoryStick size={14} /> Memory Utilization
          </div>
          <div className="vitals-bar-container">
            <div className="vitals-bar" style={{ width: `${Math.min(data.ram_percent, 100)}%` }}></div>
          </div>
          <div className="vitals-label">{data.ram_percent.toFixed(1)}%</div>
        </div>
      </div>

      {/* Error Log Feed */}
      {errorLogs.length > 0 && (
        <div className="card error-log-card">
          <div className="card-title">
            <AlertTriangle size={14} /> Error Log
          </div>
          <div className="error-log-list">
            {errorLogs.map((log, i) => (
              <div key={i} className="error-log-entry">
                <span className="error-log-time">{log.time}</span>
                <span className={`error-log-status status-${log.status}`}>{log.status}</span>
                <span className="error-log-msg">{log.error}</span>
                <span className="error-log-path">{log.method} {log.path}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
