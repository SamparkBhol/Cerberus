import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  logout, 
  getAlerts, 
  getStats, 
  startTraining, 
  getModelStatus,
  getAuthHeaders 
} from '../services/api';
import { 
  ResponsiveContainer, 
  PieChart, 
  Pie, 
  Cell, 
  Tooltip, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid 
} from 'recharts';

const MAX_LOGS = 200;
const MAX_SYSTEM_LOGS = 50;
const PIE_COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];
const WS_URL = 'ws://127.0.0.1:8000/ws/traffic/';

function formatBytes(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function DashboardPage() {
  const navigate = useNavigate();
  const [trafficLogs, setTrafficLogs] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [systemLog, setSystemLog] = useState([]);
  const [pieData, setPieData] = useState([]);
  const [barData, setBarData] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [modelStatus, setModelStatus] = useState({ is_trained: false, is_training: false });

  const [packetCount, setPacketCount] = useState(0);
  const [totalData, setTotalData] = useState(0);
  const [alertCount, setAlertCount] = useState(0);
  
  const ws = useRef(null);
  const logListRef = useRef(null);
  const alertListRef = useRef(null);
  const systemLogRef = useRef(null);

  const addSystemLog = (message, type = 'system') => {
    const timestamp = new Date().toLocaleString();
    const logEntry = { message, timestamp, type };
    setSystemLog(prevLogs => [logEntry, ...prevLogs.slice(0, MAX_SYSTEM_LOGS - 1)]);
  };

  const fetchDashboardData = async () => {
    try {
      const [alertsData, statsData, modelData] = await Promise.all([
        getAlerts(),
        getStats(),
        getModelStatus()
      ]);
      
      setAlerts(alertsData);
      setAlertCount(alertsData.length);
      
      const formattedPieData = statsData.protocol_breakdown.map(item => ({
        name: item.protocol,
        value: item.count
      }));
      setPieData(formattedPieData);

      const formattedBarData = statsData.top_sources.map(item => ({
        name: item.source_ip,
        count: item.count
      }));
      setBarData(formattedBarData);

      setModelStatus(modelData);
      
    } catch (error) {
      console.error("Failed to fetch dashboard data:", error);
      addSystemLog("Failed to fetch dashboard data.", "error");
    }
  };

  useEffect(() => {
    fetchDashboardData();

    function connect() {
      const { Authorization } = getAuthHeaders();
      const token = Authorization ? Authorization.split(' ')[1] : null;
      
      if (!token) {
        console.log("No auth token, WebSocket not connecting.");
        addSystemLog("Authentication token not found. WebSocket failed.", "error");
        return; 
      }

      ws.current = new WebSocket(`${WS_URL}?token=${token}`);

      ws.current.onopen = () => {
        console.log("WebSocket connected");
        setIsConnected(true);
        addSystemLog("Real-time connection active.");
      };

      ws.current.onclose = () => {
        console.log("WebSocket disconnected");
        setIsConnected(false);
        if (!ws.current.wasClean) {
          addSystemLog("Real-time connection lost. Reconnecting...", "error");
          setTimeout(connect, 3000); 
        }
      };

      ws.current.onerror = (err) => {
        console.error("WebSocket error:", err);
        addSystemLog("WebSocket error. Closing connection.", "error");
        ws.current.close();
      };

      ws.current.onmessage = (e) => {
        const { type, data } = JSON.parse(e.data);
        
        if (type === 'traffic') {
          setTrafficLogs(prevLogs => [data, ...prevLogs.slice(0, MAX_LOGS - 1)]);
          setPacketCount(prev => prev + 1);
          setTotalData(prev => prev + (data.packet_size || 0));
        } else if (type === 'alert') {
          setAlerts(prevAlerts => [data, ...prevAlerts]);
          setAlertCount(prev => prev + 1);
          addSystemLog(`New Alert: ${data.message}`, "alert");
        } else if (type === 'system') {
          addSystemLog(data, "system");
          if (data.includes("Model training complete")) {
            fetchDashboardData(); 
          }
        }
      };
    }

    connect();

    return () => {
      if (ws.current) {
        ws.current.wasClean = true;
        ws.current.close();
      }
    };
  }, []);

  useEffect(() => {
    if (logListRef.current) {
      logListRef.current.scrollTop = 0;
    }
  }, [trafficLogs]);

  useEffect(() => {
    if (alertListRef.current) {
      alertListRef.current.scrollTop = 0;
    }
  }, [alerts]);

  useEffect(() => {
    if (systemLogRef.current) {
      systemLogRef.current.scrollTop = 0;
    }
  }, [systemLog]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleTrainModel = async () => {
    try {
      const data = await startTraining();
      addSystemLog(data.message);
      setModelStatus(prev => ({ ...prev, is_training: true }));
    } catch (error) {
      console.error("Failed to start training:", error);
      addSystemLog("Failed to start training.", "error");
    }
  };

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>Cerberus Dashboard</h1>
        <button onClick={handleLogout}>Logout</button>
      </header>

      <main className="dashboard-main">
        <div className="dashboard-card status-bar">
          <div className="status-light">
            <span className={`status-indicator ${isConnected ? 'connected' : ''}`}></span>
            <span>{isConnected ? 'Real-time connection active' : 'Connecting...'}</span>
          </div>
          <div className="model-status">
            Model Status: 
            <strong>
              {modelStatus.is_training ? " Training..." : (modelStatus.is_trained ? " Active" : " Not Trained")}
            </strong>
          </div>
          <button 
            className="train-button"
            onClick={handleTrainModel}
            disabled={modelStatus.is_training}
          >
            {modelStatus.is_training ? "Training in progress..." : "Start Model Training"}
          </button>
        </div>

        <div className="dashboard-card live-stats">
          <h2>Live Stats</h2>
          <div className="stats-grid">
            <div className="stat-item">
              <h3>Total Packets</h3>
              <span>{packetCount}</span>
            </div>
            <div className="stat-item">
              <h3>Total Alerts</h3>
              <span>{alertCount}</span>
            </div>
            <div className="stat-item">
              <h3>Data Transferred</h3>
              <span>{formatBytes(totalData)}</span>
            </div>
          </div>
        </div>

        <div className="dashboard-card log-panel">
          <div className="log-header">
            <h2>Live Traffic Log</h2>
            <button onClick={() => setTrafficLogs([])} className="clear-log-btn">Clear Log</button>
          </div>
          <ul className="log-list" ref={logListRef}>
            {trafficLogs.map(log => (
              <li key={log.id}>
                [{new Date(log.timestamp).toLocaleTimeString()}] {log.source_ip}:{log.source_port} -&gt; {log.dest_ip}:{log.dest_port} ({log.protocol})
              </li>
            ))}
          </ul>
        </div>

        <div className="dashboard-card alert-panel">
          <h2>Alerts</h2>
          <ul className="alert-list" ref={alertListRef}>
            {alerts.map(alert => (
              <li key={alert.id}>
                [{new Date(alert.timestamp).toLocaleString()}] {alert.message}
              </li>
            ))}
          </ul>
        </div>

        <div className="dashboard-card charts-container">
          <div className="chart-wrapper">
            <h3>Protocol Breakdown</h3>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} fill="#8884d8" label>
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="chart-wrapper">
            <h3>Top Sources</h3>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barData} layout="vertical" margin={{ left: 60 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="name" type="category" width={100} />
                <Tooltip />
                <Bar dataKey="count" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="dashboard-card system-log-panel">
          <h2>System &amp; Event Log</h2>
          <ul className="log-list" ref={systemLogRef}>
            {systemLog.map((log, index) => (
              <li key={index} className={`log-type-${log.type}`}>
                [{log.timestamp}] {log.message}
              </li>
            ))}
          </ul>
        </div>

      </main>
    </div>
  );
}

export default DashboardPage;

