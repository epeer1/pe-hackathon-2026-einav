import React, { useState, useEffect } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Activity, Server, Database, Ticket } from 'lucide-react';

export default function App() {
  const [data, setData] = useState({
    database: 'offline',
    available_tickets: 100,
    cpu_percent: 0,
    ram_percent: 0,
    be_instances: 4,
    db_instances: 1
  });
  
  // Historical data for the wave chart
  const [history, setHistory] = useState(Array.from({ length: 20 }, (_, i) => ({ time: i, traffic: 0 })));

  useEffect(() => {
    let lastTickets = null;
    
    const fetchTelemetry = async () => {
      try {
        const response = await fetch('http://127.0.0.1:5001/api/telemetry');
        const newData = await response.json();
        
        // Calculate simulated "API Traffic" based on tickets dropping
        let currentTraffic = 0;
        if (lastTickets !== null && newData.available_tickets < lastTickets) {
           // We map ticket consumption events to high RPS spikes
           currentTraffic = (lastTickets - newData.available_tickets) * 15; 
        } else {
           // Base heartbeat traffic
           currentTraffic = Math.floor(Math.random() * 5);
        }
        lastTickets = newData.available_tickets;

        setData(newData);
        
        setHistory(prev => {
          const newHistory = [...prev.slice(1), { time: prev[prev.length - 1].time + 1, traffic: currentTraffic }];
          return newHistory;
        });

      } catch (err) {
        console.error("Failed to fetch telemetry:", err);
        // If the backend completely drops, reflect frontend state
        setData(prev => ({ ...prev, database: 'offline' }));
      }
    };

    const intervalId = setInterval(fetchTelemetry, 500);
    return () => clearInterval(intervalId);
  }, []);

  return (
    <div className="dashboard-container">
      <header className="header">
        <h1>SRE Observability Center</h1>
        <p>Live Flash Sale Traffic & Cluster Health</p>
      </header>

      <div className="grid">
        {/* The Hero Wave Chart */}
        <div className="card hero-chart">
          <div className="card-title">
            <Activity size={16} /> Live API Traffic (Requests/sec)
          </div>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={history} margin={{ top: 10, right: 0, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="colorTraffic" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#171717" stopOpacity={0.1}/>
                  <stop offset="95%" stopColor="#171717" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid vertical={false} />
              <XAxis dataKey="time" hide />
              <YAxis hide domain={[0, 150]} />
              <Tooltip 
                contentStyle={{ borderRadius: '8px', border: '1px solid #e5e5e5', boxShadow: '0 4px 6px rgba(0,0,0,0.05)' }}
                itemStyle={{ color: '#171717', fontWeight: 600, fontFamily: 'Fira Code' }}
              />
              <Area 
                type="monotone" 
                dataKey="traffic" 
                stroke="#171717" 
                strokeWidth={2}
                fillOpacity={1} 
                fill="url(#colorTraffic)" 
                isAnimationActive={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Database Health Card */}
        <div className="card card-health">
          <div className="card-title">
            <Database size={16} /> PostgreSQL Connectivity
          </div>
          <div className="status-indicator">
            <div className={`dot ${data.database === 'online' ? 'green' : 'red'}`}></div>
            {data.database === 'online' ? 'NODE ONLINE' : 'NODE OFFLINE'}
          </div>
        </div>

        {/* Cluster Topology Card */}
        <div className="card card-cluster">
          <div className="card-title">
            <Server size={16} /> Cluster Topology (Instances)
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

        {/* Flash Sale Pulse Card */}
        <div className="card card-pulse">
          <div className="card-title">
            <Ticket size={16} /> Flash Sale (Available)
          </div>
          <div className="card-value">
            {data.available_tickets}
          </div>
        </div>
      </div>
    </div>
  );
}
