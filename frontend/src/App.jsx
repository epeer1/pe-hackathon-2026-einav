import React, { useState, useEffect, useRef, useCallback } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Activity, Server, Database, Ticket, Cpu, MemoryStick, Zap, Plus } from 'lucide-react';

const API = 'http://127.0.0.1:5001';
const HISTORY_LENGTH = 60;

export default function App() {
  const [data, setData] = useState({
    database: 'offline',
    available_tickets: 0,
    cpu_percent: 0,
    ram_percent: 0,
    be_instances: 1,
    db_instances: 1
  });

  const [history, setHistory] = useState(
    Array.from({ length: HISTORY_LENGTH }, (_, i) => ({ time: i, traffic: 0 }))
  );

  const [activeEventId, setActiveEventId] = useState(null);
  const [isLoadRunning, setIsLoadRunning] = useState(false);
  const [loadStats, setLoadStats] = useState(null);

  const lastTicketsRef = useRef(null);
  const tickRef = useRef(0);

  // ── Telemetry Polling ──────────────────────────────────────
  useEffect(() => {
    const fetchTelemetry = async () => {
      try {
        const response = await fetch(`${API}/api/telemetry`);
        const newData = await response.json();

        let currentTraffic = 0;
        if (lastTicketsRef.current !== null && newData.available_tickets < lastTicketsRef.current) {
          currentTraffic = (lastTicketsRef.current - newData.available_tickets) * 12;
        } else {
          currentTraffic = 2 + Math.sin(tickRef.current * 0.3) * 1.5 + Math.random() * 1.5;
        }
        lastTicketsRef.current = newData.available_tickets;
        tickRef.current += 1;

        setData(newData);
        setHistory(prev => [
          ...prev.slice(1),
          { time: prev[prev.length - 1].time + 1, traffic: Math.round(currentTraffic * 10) / 10 }
        ]);
      } catch {
        setData(prev => ({ ...prev, database: 'offline' }));
        tickRef.current += 1;
        setHistory(prev => [
          ...prev.slice(1),
          { time: prev[prev.length - 1].time + 1, traffic: 0 }
        ]);
      }
    };

    const id = setInterval(fetchTelemetry, 800);
    fetchTelemetry();
    return () => clearInterval(id);
  }, []);

  // ── Launch Flash Sale ──────────────────────────────────────
  const launchSale = useCallback(async () => {
    const name = `FlashSale_${Date.now()}`;
    try {
      const res = await fetch(`${API}/admin/event`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, total_tickets: 100 })
      });
      const event = await res.json();
      if (res.ok) {
        setActiveEventId(event.id);
        setLoadStats(null);
        lastTicketsRef.current = 100;
      }
    } catch (e) {
      console.error('Failed to create event:', e);
    }
  }, []);

  // ── Simulate Load ──────────────────────────────────────────
  const simulateLoad = useCallback(async () => {
    if (!activeEventId || isLoadRunning) return;
    setIsLoadRunning(true);
    setLoadStats(null);

    const TOTAL = 150;
    let successes = 0;
    let failures = 0;

    // Fire requests in batches of 25 for a visible wave effect
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

    // Stagger 6 batches of 25 for dramatic wave buildup
    for (let b = 0; b < 6; b++) {
      await batch(b * 25, 25);
      // Tiny pause between batches so the chart can visualize the surge
      await new Promise(r => setTimeout(r, 200));
    }

    setLoadStats({ successes, failures, oversold: successes > 100 });
    setIsLoadRunning(false);
  }, [activeEventId, isLoadRunning]);

  const isOnline = data.database === 'online';

  return (
    <div className="dashboard-container">
      <header className="header">
        <div className="header-left">
          <h1>SRE Observability Center</h1>
          <p>Live Flash Sale Traffic & Cluster Health</p>
        </div>
        <div className="header-actions">
          <button className="btn btn-secondary" onClick={launchSale}>
            <Plus size={14} /> New Flash Sale
          </button>
          <button
            className={`btn btn-primary ${isLoadRunning ? 'btn-loading' : ''}`}
            onClick={simulateLoad}
            disabled={!activeEventId || isLoadRunning}
          >
            <Zap size={14} /> {isLoadRunning ? 'Simulating...' : 'Simulate Load (150 users)'}
          </button>
        </div>
      </header>

      {/* Load Test Results Banner */}
      {loadStats && (
        <div className={`results-banner ${loadStats.oversold ? 'results-fail' : 'results-pass'}`}>
          {loadStats.oversold
            ? `💥 OVERSOLD — ${loadStats.successes} tickets sold (expected max 100)`
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
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={history} margin={{ top: 5, right: 10, left: 10, bottom: 0 }}>
              <defs>
                <linearGradient id="colorTraffic" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#171717" stopOpacity={0.08} />
                  <stop offset="100%" stopColor="#171717" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid vertical={false} strokeDasharray="4 4" stroke="#eee" />
              <XAxis dataKey="time" hide />
              <YAxis hide domain={[0, 'auto']} />
              <Tooltip
                contentStyle={{
                  borderRadius: '6px',
                  border: '1px solid #e5e5e5',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.06)',
                  fontSize: '13px'
                }}
                labelStyle={{ display: 'none' }}
                itemStyle={{ color: '#171717', fontWeight: 600, fontFamily: 'Fira Code, monospace' }}
              />
              <Area
                type="monotone"
                dataKey="traffic"
                stroke="#171717"
                strokeWidth={1.5}
                fillOpacity={1}
                fill="url(#colorTraffic)"
                animationDuration={600}
                animationEasing="ease-in-out"
              />
            </AreaChart>
          </ResponsiveContainer>
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
    </div>
  );
}
