'use client';

import React, { useState, useEffect } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Battery, BatteryWarning, Wind, Activity, Zap, ShieldAlert, MapPin, Settings2, ArrowRight, ArrowLeft, Fuel, Leaf, Server, ShieldX } from 'lucide-react';

export default function Dashboard() {
  const [currentTime, setCurrentTime] = useState("");
  const [soc, setSoc] = useState(82.4);
  const [batteryTemp, setBatteryTemp] = useState(18.6);
  
  // Telemetry States
  const [windSpeed, setWindSpeed] = useState(9.2); // m/s
  const [solarIrr, setSolarIrr] = useState(410.2); // W/m2
  
  // Scenarios and Controls
  const [scenario, setScenario] = useState('normal'); 
  const [aiEnabled, setAiEnabled] = useState(true);

  // Power SLD States (kW)
  const [windGen, setWindGen] = useState(45.0);
  const [solarGen, setSolarGen] = useState(12.5);
  const [dieselGen, setDieselGen] = useState(0.0);
  const [batteryFlow, setBatteryFlow] = useState(0.0);
  const [stationLoad, setStationLoad] = useState(57.0);
  
  // Economics
  const [dieselSaved, setDieselSaved] = useState(34.8); // Liters
  const [co2Avoided, setCo2Avoided] = useState(92.0); // kg
  
  const [forecastData, setForecastData] = useState<any[]>([]);

  useEffect(() => {
    setCurrentTime(new Date().toLocaleTimeString());
    generateForecast('normal');
  }, []);

  const generateForecast = (scen: string) => {
    if (scen === 'storm') {
      setForecastData([
        { time: 'Now', predictedWind: 35.0, load: 42.0 },
        { time: 'T+1', predictedWind: 38.0, load: 45.0 },
        { time: 'T+2', predictedWind: 33.0, load: 48.0 },
      ]);
    } else if (scen === 'polar_night') {
      setForecastData([
        { time: 'Now', predictedWind: 9.0, load: 42.0 },
        { time: 'T+1', predictedWind: 8.5, load: 45.0 },
        { time: 'T+2', predictedWind: 7.0, load: 48.0 },
      ]);
    } else {
      setForecastData([
        { time: 'Now', predictedWind: 9.0, load: 42.0 },
        { time: 'T+1', predictedWind: 8.5, load: 45.0 },
        { time: 'T+2', predictedWind: 7.0, load: 48.0 },
      ]);
    }
  };

  const handleScenario = (s: string) => {
    setScenario(s);
    generateForecast(s);
    if (s === 'storm') {
      setWindSpeed(35.0);
      setWindGen(0.0); // Auto-brake
      setSolarGen(0.0);
      setBatteryFlow(stationLoad);
      setAiEnabled(true);
    } else if (s === 'polar_night') {
      setWindSpeed(9.2);
      setWindGen(45.0);
      setSolarIrr(0.0);
      setSolarGen(0.0);
      setBatteryFlow(stationLoad - 45.0);
      setAiEnabled(true);
    } else if (s === 'normal') {
      setWindSpeed(9.2);
      setWindGen(45.0);
      setSolarIrr(410.2);
      setSolarGen(12.5);
      setBatteryTemp(18.6);
      setBatteryFlow(stationLoad - (45.0 + 12.5));
      setAiEnabled(true);
    } else if (s === 'heating_fail') {
      setBatteryTemp(-10.4);
      setAiEnabled(true);
    } else if (s === 'failsafe') {
      setAiEnabled(false);
      setWindGen(0.0);
      setSolarGen(0.0);
      setDieselGen(stationLoad);
      setBatteryFlow(0.0); // Diesel takes full load instantly
    }
  };

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date().toLocaleTimeString());
      
      // Jitter
      if (scenario === 'normal' || scenario === 'polar_night') {
        setWindSpeed(prev => +(prev + (Math.random() - 0.5) * 0.5).toFixed(1));
        setWindGen(prev => +(prev + (Math.random() - 0.5) * 1.5).toFixed(1));
      } else if (scenario === 'storm') {
        setWindSpeed(prev => Math.max(30, +(prev + (Math.random() - 0.5) * 2).toFixed(1)));
        setWindGen(0.0);
      }
      
      if (aiEnabled && dieselGen === 0) {
        setDieselSaved(prev => +(prev + 0.01).toFixed(2));
        setCo2Avoided(prev => +(prev + 0.02).toFixed(2));
      }

      if (batteryFlow > 0) {
        setSoc(prev => Math.max(20, +(prev - 0.05).toFixed(1)));
      } else if (batteryFlow < 0) {
        setSoc(prev => Math.min(100, +(prev + 0.05).toFixed(1)));
      }

      if (aiEnabled) {
        if (scenario === 'storm' && soc < 40) {
          setDieselGen(stationLoad);
          setBatteryFlow(-20.0); 
        } else {
          setDieselGen(0);
          setBatteryFlow(stationLoad - windGen - solarGen);
        }
      } else {
        if (scenario === 'failsafe') {
          setDieselGen(stationLoad);
          setBatteryFlow(0.0);
        } else if (soc <= 20) {
          setDieselGen(stationLoad);
          setBatteryFlow(-10.0);
        } else {
          setDieselGen(0);
          setBatteryFlow(stationLoad - windGen - solarGen);
        }
      }
      
    }, 2000);
    return () => clearInterval(timer);
  }, [scenario, aiEnabled, windGen, solarGen, stationLoad, soc, batteryFlow, dieselGen]);

  let xaiRationale = "";
  if (scenario === 'failsafe') {
    xaiRationale = "CRITICAL: AI Heartbeat lost. Watchdog Timeout triggered. Hardware PLC Override engaged. Diesel forced ON for life-safety.";
  } else if (!aiEnabled) {
    xaiRationale = "Legacy Control Active: Operating on naive voltage thresholds. Fails to pre-heat cells or anticipate storms.";
  } else if (scenario === 'storm') {
    if (soc < 40) {
      xaiRationale = `Action: Katabatic Surge (35+ m/s) detected. Turbines auto-braked. SOC dropping. Ramping Diesel early to preserve BESS health.`;
    } else {
      xaiRationale = `Action: Katabatic Surge (35+ m/s). Turbines auto-braked. BESS SOC is healthy (${soc.toFixed(1)}%). Sustaining full station load via battery. Diesel remains on standby.`;
    }
  } else if (scenario === 'polar_night') {
    xaiRationale = `Action: Deep Polar Night (0.0 W/m² solar). Strict cycle management engaged. Prioritizing Wind to preserve BESS longevity.`;
  } else if (scenario === 'heating_fail') {
    xaiRationale = `Action: Shedding non-critical Science Lab loads to redirect 12kW into emergency battery cell heating. Battery life preserved.`;
  } else {
    xaiRationale = `Action: Maintaining 100% Renewable Penetration. Routing excess 14kW to BESS thermal containment.`;
  }

  let renewableFraction = ((windGen + solarGen) / stationLoad * 100);
  if (renewableFraction > 100) renewableFraction = 100;
  if (dieselGen > 0) renewableFraction = 0;

  return (
    <div className="dashboard-container">
      <header className="header">
        <div className="header-left">
          <h1>Microgrid Edge Command</h1>
          <div className="location-badge">
            <MapPin size={14} /> Station: Zhongshan AWS (Telemetry Proxy for Bharati Station)
          </div>
        </div>
        <div className="header-meta">
          <span className="badge online pulse" style={scenario === 'failsafe' ? {background: 'rgba(239, 68, 68, 0.15)', color: 'var(--accent-red)', borderColor: 'var(--accent-red)'} : {}}>
            {scenario === 'failsafe' ? <><ShieldX size={12}/> EDGE AI OFFLINE: PLC OVERRIDE</> : <><ShieldAlert size={12}/> EDGE AIR-GAPPED: LOCAL INFERENCE ACTIVE</>}
          </span>
          <span style={{color: 'var(--text-muted)', fontFamily: 'monospace', fontSize: '1.2rem'}}>{currentTime}</span>
        </div>
      </header>

      <main className="grid-main">
        
        {/* Environment Panel */}
        <div className="glass-card telemetry-panel">
          <h2 className="card-title"><Wind size={18} /> Telemetry (AntAWS)</h2>
          <div className="stat-group">
            <span className="stat-label">Wind Speed</span>
            <span className="stat-value" style={windSpeed > 30 ? {color: 'var(--accent-red)'} : {}}>{windSpeed.toFixed(1)} m/s</span>
          </div>
          <div className="stat-group">
            <span className="stat-label">Solar Irradiance</span>
            <span className="stat-value">
              {solarIrr} W/m²
              {solarIrr === 0 && <span className="badge warning" style={{marginLeft: '8px', fontSize: '0.6rem'}}>Polar Night</span>}
            </span>
          </div>
          <div className="stat-group">
            <span className="stat-label">Air Density (ρ)</span>
            <span className="stat-value">1.42 kg/m³</span>
          </div>
        </div>

        {/* BEMS Panel */}
        <div className="glass-card battery-panel">
          <h2 className="card-title">
            {soc <= 20 ? <BatteryWarning size={18} color="var(--accent-red)"/> : <Battery size={18} />} BEMS State
          </h2>
          <div className="stat-group">
            <span className="stat-label">State of Charge</span>
            <div style={{width: '60%', textAlign: 'right'}}>
              <span className="stat-value">{soc.toFixed(1)}%</span>
              <div className="progress-bg">
                <div className={`progress-fill ${soc < 25 ? 'low' : soc < 50 ? 'medium' : ''}`} style={{width: `${soc}%`}}></div>
              </div>
            </div>
          </div>
          <div className="stat-group" style={{marginTop: '0.75rem'}}>
            <span className="stat-label">Battery Core Temp</span>
            <span className="stat-value" style={batteryTemp < 0 ? {color: 'var(--accent-red)'} : {}}>{batteryTemp} °C</span>
          </div>
        </div>

        {/* Top SLD Flow Panel */}
        <div className="glass-card sld-panel">
          <h2 className="card-title"><Activity size={18} /> Live Power Flow (Single-Line Diagram)</h2>
          <div className="sld-container">
            <div className={`sld-node ${windGen > 0 || solarGen > 0 ? 'active-gen' : ''}`}>
              <Wind size={24} color={windGen > 0 ? "var(--accent-cyan)" : "var(--text-muted)"} />
              <span className="sld-value">{(windGen + solarGen).toFixed(1)} kW</span>
            </div>
            
            <div className="sld-flow">
              <ArrowRight size={24} className={windGen > 0 || solarGen > 0 ? "flow-arrow" : ""} />
            </div>
            
            <div className={`sld-node ${dieselGen > 0 ? 'active-gen' : ''}`} style={dieselGen > 0 ? {borderColor: 'var(--accent-red)'} : {}}>
              <Fuel size={24} color={dieselGen > 0 ? "var(--accent-red)" : "var(--text-muted)"} />
              <span className="sld-value" style={{color: dieselGen > 0 ? "var(--accent-red)" : ""}}>{dieselGen.toFixed(1)} kW</span>
            </div>

            <div className="sld-flow">
              <ArrowRight size={24} className={dieselGen > 0 ? "flow-arrow" : ""} />
            </div>

            <div className={`sld-node ${batteryFlow !== 0 ? 'active-gen' : ''}`} style={{borderColor: 'var(--accent-orange)'}}>
              <Battery size={24} color="var(--accent-orange)" />
              <span className="sld-value" style={{color: "var(--accent-orange)", fontSize: '0.9rem'}}>
                {batteryFlow > 0 ? `-${Math.abs(batteryFlow).toFixed(1)} kW (Dis)` : 
                 batteryFlow < 0 ? `+${Math.abs(batteryFlow).toFixed(1)} kW (Chg)` : `0 kW`}
              </span>
            </div>

            <div className={`sld-flow ${batteryFlow < 0 ? 'reverse' : ''}`}>
              {batteryFlow < 0 ? <ArrowLeft size={24} className="flow-arrow" color="var(--accent-orange)" /> : <ArrowRight size={24} className="flow-arrow" />}
            </div>

            <div className="sld-node active-load">
              <Zap size={24} color="var(--accent-red)" />
              <span className="sld-value load">{stationLoad.toFixed(1)} kW</span>
            </div>
          </div>
        </div>

        {/* Economics Panel */}
        <div className="glass-card economics-panel" style={{display: 'flex', flexDirection: 'column', gap: '0.5rem'}}>
          <h2 className="card-title" style={{marginBottom: '0.2rem'}}><Leaf size={18} /> Impact KPIs</h2>
          <div className="stat-group" style={{border: 'none', display: 'block', paddingBottom: 0}}>
            <span className="stat-label">Diesel Conserved (Liters/Day)</span>
            <span className="hero-value green">{dieselSaved.toFixed(1)}</span>
          </div>
          <div className="stat-group" style={{border: 'none', display: 'block', paddingBottom: 0}}>
            <span className="stat-label">Renewable Penetration</span>
            <span className="hero-value cyan">{renewableFraction.toFixed(1)}%</span>
          </div>
        </div>

        {/* PPO RL AI Panel */}
        <div className="glass-card ai-panel" style={{gridColumn: 'span 4', borderColor: scenario === 'failsafe' ? 'var(--accent-red)' : ''}}>
          <h2 className="card-title"><Activity size={18} /> Deep RL Agent {scenario === 'failsafe' && <span className="badge critical pulse" style={{marginLeft: 'auto'}}>OFFLINE</span>}</h2>
          <div className="stat-group">
            <span className="stat-label">Current Action</span>
            {scenario === 'normal' ? <span className="badge active">Monitoring</span> :
             scenario === 'heating_fail' ? <span className="badge critical">Load Shedding</span> :
             scenario === 'polar_night' ? <span className="badge warning">Cycle Mgt</span> :
             scenario === 'failsafe' ? <span className="badge critical">CRASHED</span> :
             <span className="badge critical pulse">Auto-Brake</span>}
          </div>
          <div className="xai-box" style={scenario === 'failsafe' ? {background: 'rgba(239, 68, 68, 0.1)', borderLeftColor: 'var(--accent-red)'} : {}}>
            <strong style={{color: scenario === 'failsafe' ? 'var(--accent-red)' : 'var(--accent-cyan)'}}>Explainable AI (XAI):</strong><br/>
            {xaiRationale}
          </div>
        </div>

        {/* Controls Panel */}
        <div className="glass-card controls-panel">
          <h2 className="card-title"><Settings2 size={18} /> Interactive Controls</h2>
          
          <div className="toggle-switch">
            <div className={`toggle-btn ${aiEnabled && scenario !== 'failsafe' ? 'active' : ''}`} onClick={() => handleScenario('normal')}>
              PPO AI Mode
            </div>
            <div className={`toggle-btn ${!aiEnabled && scenario !== 'failsafe' ? 'active' : ''}`} onClick={() => setAiEnabled(false)} style={{background: !aiEnabled && scenario !== 'failsafe' ? 'var(--accent-red)' : ''}}>
              Legacy Rule-Based
            </div>
          </div>

          <button className={`control-btn ${scenario === 'normal' ? 'active' : ''}`} onClick={() => handleScenario('normal')}>
            Normal Operations
          </button>
          <button className={`control-btn danger ${scenario === 'storm' ? 'active' : ''}`} onClick={() => handleScenario('storm')}>
            Katabatic Storm (35 m/s Auto-Brake)
          </button>
          <button className={`control-btn danger ${scenario === 'polar_night' ? 'active' : ''}`} onClick={() => handleScenario('polar_night')}>
            Deep Polar Night (Total Solar Loss)
          </button>
          <button className={`control-btn danger ${scenario === 'failsafe' ? 'active' : ''}`} style={{borderColor: scenario === 'failsafe' ? 'var(--accent-red)' : '#f87171'}} onClick={() => handleScenario('failsafe')}>
            Simulate AI Crash (PLC Failsafe)
          </button>
        </div>

        {/* Chart Panel */}
        <div className="glass-card chart-panel">
          <h2 className="card-title"><Zap size={18} /> AI Forecast vs Demand (Next 3 Hours)</h2>
          <div style={{ width: '100%', height: '220px' }}>
            <ResponsiveContainer>
              <AreaChart data={forecastData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorWind" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--accent-cyan)" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="var(--accent-blue)" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-glass)" vertical={false} />
                <XAxis dataKey="time" stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid var(--border-glass)' }} />
                <Area type="monotone" dataKey="predictedWind" name="AI Wind Forecast (m/s)" stroke="var(--accent-cyan)" strokeWidth={3} fillOpacity={1} fill="url(#colorWind)" />
                <Area type="step" dataKey="load" name="Station Load (kW)" stroke="var(--accent-red)" strokeWidth={2} fillOpacity={0.0} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* SCADA Logs */}
        <div className="glass-card log-panel" style={{gridColumn: 'span 4'}}>
          <h2 className="card-title"><Server size={18} /> Live SCADA Logs</h2>
          <div className="log-entry">[DATA] Synced 24h AntAWS weather history</div>
          <div className="log-entry action">[AI] Forecast generated for next 12h</div>
          {scenario === 'storm' && <div className="log-entry alert">[WARN] 35m/s wind detected. Turbines braking.</div>}
          {scenario === 'polar_night' && <div className="log-entry alert">[WARN] Solar zeroed. Engaging deep cycle.</div>}
          {scenario === 'heating_fail' && <div className="log-entry alert">[CRIT] BESS Temp drop. Shedding lab loads.</div>}
          {scenario === 'failsafe' && <div className="log-entry alert" style={{color: 'var(--accent-red)'}}>[FATAL] AI Watchdog Timeout. PLC Override ACTIVE. Hard-starting Diesel.</div>}
          {aiEnabled && batteryFlow < 0 && dieselGen > 0 && <div className="log-entry action">[BEMS] Re-routing diesel excess to BESS</div>}
        </div>

      </main>
    </div>
  );
}
