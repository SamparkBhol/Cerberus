# 🧠 Cerberus: Network Security Visualizer  

**Cerberus** is a full-stack, real-time **network flow analysis** and **anomaly detection** tool that captures live network traffic, trains an ML model to detect anomalies, and visualizes the data in a modern, interactive dashboard. It merges **scapy** (for packet interception), **Django** (for backend and ML model management), and **React** (for frontend visualization).  

---

## 🔐 Key Features  

- 🛡️ **Real-Time Packet Sniffing:** A scapy-based interceptor captures live network packets and streams them to the backend.  
- 🧠 **ML-Powered Anomaly Detection:** An Isolation Forest model (scikit-learn) learns normal behavior and identifies unusual traffic patterns.  
- 📊 **Dynamic React Dashboard:** Built with Recharts and WebSockets, offering:  
  - Live traffic logs  
  - Real-time anomaly alerts  
  - Protocol breakdowns (Pie Chart)  
  - Top source IPs (Bar Chart)  
- 🚀 **Asynchronous Django Backend:** Powered by Django REST Framework and Django Channels for real-time data handling and WebSocket communication.  

---

## ⚙️ Tech Stack  

| Area | Technology |
|------|-------------|
| **Frontend** | React, React Router, Recharts, Axios |
| **Backend** | Python, Django, Django REST Framework, Django Channels |
| **Network & ML** | scapy (Packet Sniffing), scikit-learn (Isolation Forest) |
| **Database** | SQLite (for development) |

---

## 🏗️ Project Structure  

Cerberus/  
├── backend/  
│ ├── api/ — Main Django app (models, views, serializers)  
│ ├── engine/ — Project settings and URLs  
│ ├── venv/ — Virtual environment  
│ ├── db.sqlite3 — Local development database  
│ ├── manage.py — Django management script  
│ └── *.joblib — Saved ML model files  
│  
├── frontend/  
│ └── dashboard/ — React application  
│ ├── node_modules/  
│ ├── public/  
│ └── src/ — React components, pages, and services  
│  
├── interceptor/  
│ └── interceptor.py — Standalone scapy-based packet sniffer  
│  
├── .gitignore  
└── README.md  

---

## 🧩 How to Run  

This application requires **three separate terminals** to function simultaneously.  

### 🖥️ 1. Terminal 1: Run the Backend (Django)  

cd backend  
.\venv\Scripts\activate  
python manage.py makemigrations api  
python manage.py migrate  
python manage.py createsuperuser  
python manage.py runserver  

---

### 🌐 2. Terminal 2: Run the Frontend (React)  

cd frontend/dashboard  
npm install  
npm start  

This will open the dashboard at **http://localhost:3000**.  

---

### ⚡ 3. Terminal 3: Run the Interceptor (Admin)  

⚠️ Run this terminal as Administrator to allow packet capture.  

cd backend  
.\venv\Scripts\activate  
cd ../interceptor  
python interceptor.py  

---

## 🔄 Application Workflow  

1. Open **http://localhost:3000** in your browser.  
2. Log in using the Django superuser credentials.  
3. The dashboard connects automatically; live traffic logs begin populating.  
4. The “Model Status” initially shows **Not Trained**.  
5. Click **Start Model Training** — it collects 100 packets to learn normal behavior.  
6. Status updates to **Training...**, then **Active** once the model is ready.  
7. Any anomalies detected are instantly logged in the **Alerts** panel.  

---

## 🧠 Summary  

**Cerberus** provides a real-time, intelligent view of your network by combining **packet-level visibility**, **machine learning-driven anomaly detection**, and **interactive visualization**. It demonstrates the power of **full-stack development**, **ML integration**, and **cybersecurity awareness** in one cohesive project.
