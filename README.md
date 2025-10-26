# XR ECG Twin - Microservices Architecture

A modern, scalable ECG monitoring system built with Django microservices, MQTT, and React. This project replaces MATLAB processing with Python for better performance and flexibility.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                        │
│                      Port 3000                               │
│              Real-time ECG Visualization                     │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/WebSocket
┌────────────────────▼────────────────────────────────────────┐
│                  API Gateway (Django)                        │
│                      Port 8000                               │
│           Routes requests to microservices                   │
└──────────┬─────────────────────────┬────────────────────────┘
           │                         │
    ┌──────▼──────┐           ┌──────▼──────┐
    │ ECG Service │           │ IoT Service │
    │  (Django)   │           │  (Django)   │
    │  Port 8001  │           │  Port 8002  │
    │             │           │             │
    │ - Process   │           │ - Device    │
    │   ECG data  │           │   mgmt      │
    │ - Extract   │           │ - MQTT sub  │
    │   features  │           │ - Data      │
    │ - HRV calc  │           │   ingestion │
    └─────┬───────┘           └──────┬──────┘
          │                          │
    ┌─────▼──────────────────────────▼──────┐
    │         PostgreSQL (TimescaleDB)      │
    │               Port 5432                │
    │         Time-series ECG data           │
    └────────────────────────────────────────┘
          │                          │
    ┌─────▼──────┐           ┌──────▼──────┐
    │   Redis    │           │  Mosquitto  │
    │ Port 6379  │           │  MQTT       │
    │ Cache +    │           │  Port 1883  │
    │ Celery     │           │             │
    └────────────┘           └─────────────┘
```

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend)

### 1. Clone and Setup

```bash
cd ~/Sapienza/XR_ECG_Twin

# Copy environment file
cp .env.example .env

# Edit .env and change passwords/secrets
nano .env
```

### 2. Start All Services

```bash
# Build and start all containers
docker-compose up --build

# Or run in background
docker-compose up -d
```

### 3. Access Services

- **Frontend Dashboard**: http://localhost:3000
- **API Gateway**: http://localhost:8000
- **ECG Service**: http://localhost:8001
- **IoT Service**: http://localhost:8002
- **MQTT Broker**: mqtt://localhost:1883

### 4. Health Check

```bash
curl http://localhost:8000/health/
```

## Services Overview

### API Gateway (Port 8000)
- Central entry point for all API requests
- Routes requests to appropriate microservices
- Handles authentication & rate limiting
- WebSocket support for real-time data

**Endpoints:**
- `GET /health/` - Health check
- `GET /api/status/` - Service status
- `GET /api/ecg/` - Proxy to ECG service
- `GET /api/devices/` - Proxy to IoT service

### ECG Service (Port 8001)
- ECG signal processing (Python-based, NO MATLAB)
- Feature extraction using:
  - Wavelet analysis (PyWavelets)
  - HRV calculations
  - R-peak detection
  - Heart rate zone classification
- Stores processed data in PostgreSQL

**Key Features:**
- Bandpass filtering (0.5-40 Hz)
- Baseline wander removal
- Real-time heart rate calculation
- HRV metrics: RMSSD, SDNN, pNN50
- Wavelet decomposition for feature extraction

**Endpoints:**
- `POST /api/ecg/` - Submit ECG data for processing
- `GET /api/ecg/<id>/` - Get processed ECG reading
- `GET /api/ecg/device/<device_id>/` - Get device history

### IoT Service (Port 8002)
- Manages IoT devices (smartwatches, sensors)
- MQTT subscriber for real-time data ingestion
- Device registration & authentication
- Data forwarding to ECG service

**Endpoints:**
- `POST /api/devices/register/` - Register new device
- `GET /api/devices/` - List devices
- `GET /api/devices/<id>/status/` - Device status

## Development

### Local Development (Without Docker)

#### 1. Setup Gateway
```bash
cd gateway
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8000
```

#### 2. Setup ECG Service
```bash
cd services/ecg_service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8001
```

#### 3. Setup IoT Service
```bash
cd services/iot_service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8002
```

#### 4. Start Supporting Services
```bash
# PostgreSQL
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=ecg_password timescale/timescaledb:latest-pg15

# Redis
docker run -d -p 6379:6379 redis:7-alpine

# Mosquitto MQTT
docker run -d -p 1883:1883 -p 9001:9001 eclipse-mosquitto:2
```

### Frontend Development
```bash
cd frontend
npm install
npm start
```

## Technology Stack

### Backend
- **Django 5.0** - Web framework
- **Django REST Framework** - API development
- **Celery** - Async task processing
- **PostgreSQL + TimescaleDB** - Time-series database
- **Redis** - Cache & message broker
- **MQTT (Mosquitto)** - IoT messaging

### Signal Processing (Python, NO MATLAB)
- **NumPy** - Numerical computing
- **SciPy** - Signal processing & filtering
- **PyWavelets** - Wavelet analysis
- **NeuroKit2** - ECG analysis toolkit

### Frontend
- **React 18** - UI framework
- **Chart.js / Plotly** - Real-time visualization
- **WebSocket** - Real-time data streaming

## MQTT Topics

```
smartwatch/{device_id}/ecg        - Raw ECG data
smartwatch/{device_id}/heartrate  - Heart rate readings
smartwatch/{device_id}/status     - Device status
system/alerts                     - System alerts
```

## Data Flow

1. **Device → MQTT**: Smartwatch publishes ECG data to MQTT broker
2. **MQTT → IoT Service**: IoT service subscribes and receives data
3. **IoT → ECG Service**: Forwards raw data for processing
4. **ECG Processing**: 
   - Bandpass filter
   - R-peak detection
   - HRV calculation
   - Feature extraction
5. **Storage**: Processed data stored in PostgreSQL
6. **Frontend**: Real-time updates via WebSocket

## Testing MQTT

```bash
# Subscribe to all topics
mosquitto_sub -h localhost -t "smartwatch/#"

# Publish test ECG data
mosquitto_pub -h localhost -t "smartwatch/device001/ecg" -m '{"signal": [0.1, 0.2, 0.3], "timestamp": "2025-10-26T10:00:00Z"}'
```

## Docker Commands

```bash
# Start services
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down

# Rebuild after changes
docker compose up --build

# Run migrations
docker compose exec gateway python manage.py migrate
docker compose exec ecg-service python manage.py migrate

# Create superuser
docker compose exec gateway python manage.py createsuperuser
```

## Security Notes

WARNING: Before production:**
1. Change `POSTGRES_PASSWORD` in `.env`
2. Generate new `SECRET_KEY` for Django
3. Set `DEBUG=False`
4. Configure `ALLOWED_HOSTS`
5. Enable MQTT authentication
6. Use HTTPS/WSS

## Monitoring

- **Health endpoints**: Each service has `/health/` endpoint
- **Logs**: `docker compose logs -f <service>`
- **Database**: Connect to PostgreSQL on port 5432
- **Redis**: Use `redis-cli` on port 6379

## Contributing

This is a university project (Sapienza - Software Engineering).

## License

MIT License

## Project Structure

```
XR_ECG_Twin/
├── docker-compose.yml          # Orchestrates all services
├── .env.example                # Environment variables template
├── setup.sh                    # Quick setup script
├── README.md                   # This file
│
├── gateway/                    # API Gateway Service (Port 8000)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── manage.py
│   ├── gateway/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   └── api/
│       ├── views.py
│       └── urls.py
│
├── services/
│   ├── ecg_service/           # ECG Processing Service (Port 8001)
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── manage.py
│   │   ├── ecg_service/
│   │   │   ├── settings.py
│   │   │   └── urls.py
│   │   └── ecg/
│   │       ├── models.py              # ECGReading, ECGFeatures
│   │       ├── views.py               # REST API endpoints
│   │       ├── serializers.py         # DRF serializers
│   │       ├── tasks.py               # Celery async tasks
│   │       └── signal_processing.py   # ECG algorithms (Python, replaces MATLAB)
│   │
│   └── iot_service/           # IoT/MQTT Service (Port 8002)
│       ├── Dockerfile
│       ├── requirements.txt
│       ├── manage.py
│       ├── iot_service/
│       │   ├── settings.py
│       │   └── urls.py
│       └── iot/
│           ├── models.py              # Device models
│           ├── views.py               # Device management API
│           ├── mqtt_client.py         # MQTT subscriber
│           └── tasks.py               # Data processing tasks
│
├── mqtt/                       # MQTT Configuration
│   └── config/
│       └── mosquitto.conf
│
└── frontend/                   # React Frontend (Port 3000) - To be implemented
    └── (Coming soon)
```

## Current Status

**Running Services:**
- Gateway (Port 8000) - HEALTHY
- ECG Service (Port 8001) - OK
- IoT Service (Port 8002) - OK
- PostgreSQL (Port 5432) - HEALTHY
- Redis (Port 6379) - HEALTHY

**Note**: MQTT broker runs outside Docker (existing installation on port 1883)

## Troubleshooting

### Services not responding
```bash
docker compose logs service-name
docker compose restart service-name
```

### Rebuild after code changes
```bash
docker compose down
docker compose up --build
```

### Port conflicts
Edit `docker-compose.yml` and change the port mappings

### Clean Docker images
```bash
# Remove old images
docker image prune -a

# Remove all stopped containers
docker container prune
```

## Credits

Based on original SE_Project with improvements:
- Replaced MATLAB with Python for better performance
- Added microservices architecture for scalability
- Modernized frontend with React
- Added Docker containerization
- Replaced Node-RED with Django services

## Next Steps

1. Implement IoT Service MQTT subscriber
2. Build React frontend dashboard
3. Add authentication & authorization
4. Deploy to cloud (Azure/AWS)
5. Add AR/XR integration
6. Implement machine learning for anomaly detection

---

University Project - Sapienza, Software Engineering


