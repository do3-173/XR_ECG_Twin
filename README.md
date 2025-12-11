# XR ECG Twin - Real-Time Cardiac Monitoring System

A comprehensive, scalable ECG monitoring and analysis platform built with microservices architecture, featuring real-time visualization, advanced signal processing, 3D cardiac activation mapping, and dual frontend interfaces (Web + HoloLens VR).

## Architecture Overview

The system consists of 12 interconnected services orchestrated with Docker Compose, forming a complete ECG monitoring and analysis pipeline:

```mermaid
graph TB
    subgraph Frontend["Dual Frontend Architecture"]
        FC["Frontend Classic<br/>React 18 + TypeScript<br/>Port 3001<br/>Interactive Dashboard<br/>Canvas ECG + History"]
        FV["Frontend VR<br/>React 18 + TypeScript + THREE.js<br/>Port 3002<br/>HoloLens AR Optimized<br/>3D PointCloud Visualization"]
    end

    subgraph Gateway["API Aggregation Layer"]
        GW["API Gateway<br/>Django 4.2 REST<br/>Port 8000<br/>/api/heartrate<br/>/api/ecg/latest<br/>CORS Enabled"]
    end

    subgraph Services["Microservices Layer"]
        ECG["ECG Service<br/>Django 4.2<br/>Port 8001<br/>Pan-Tompkins Algorithm<br/>R-peak Detection<br/>Zone Classification"]
        IOT["IoT Service<br/>Django 4.2 + paho-mqtt<br/>Port 8002<br/>MQTT → PostgreSQL<br/>Device Management<br/>Historical Queries"]
        ANL["Analysis Service<br/>Django 4.2 + SciPy<br/>Port 8003<br/>Autocorrelation<br/>Wavelet Decomposition<br/>Graph Theory Features"]
        PC["PointCloud Service<br/>Django 4.2 + OpenCV<br/>Port 8004<br/>3D Cardiac Activation<br/>8 Anatomical Regions<br/>Video Generation"]
    end

    subgraph DataLayer["Data & Messaging Infrastructure"]
        PG[("PostgreSQL 15<br/>+ TimescaleDB<br/>Port 5433<br/>Time-Series Optimized<br/>JSONB ECG Storage")]
        RD[("Redis 7<br/>Port 6379<br/>5 DB Namespaces<br/>Cache + Sessions<br/>3600s TTL")]
        MQ["MQTT Broker<br/>Mosquitto 2<br/>Port 1884<br/>smartwatch/data<br/>QoS 0"]
        NR["Node-RED 3.x<br/>Port 1880<br/>Visual Flows<br/>60-Point Buffer<br/>Statistics Engine"]
    end

    subgraph Source["Data Generation"]
        SIM["ECG Simulator<br/>Python 3.10<br/>128 Hz Sampling<br/>6 Heart Rate Zones<br/>Participant 1, Session 1<br/>~37s Loop"]
    end

    FC -->|"HTTP GET<br/>1s polling"| GW
    FV -->|"HTTP GET<br/>1s polling"| GW
    GW -->|"Proxy /api/ecg/*"| ECG
    GW -->|"Proxy /api/iot/*"| IOT
    GW -->|"Proxy /api/analysis/*"| ANL
    GW -->|"Proxy /api/activation/*"| PC
    GW -->|"Poll /heartrate"| NR
    ECG -->|"Read/Write<br/>ECGReading"| PG
    IOT -->|"Write<br/>SensorData"| PG
    ANL -->|"Read/Write<br/>AnalysisResult"| PG
    PC -->|"Read/Write<br/>PointCloud<br/>ActivationAnalysis"| PG
    IOT -->|"Subscribe<br/>smartwatch/data"| MQ
    ECG -->|"Cache<br/>DB 1"| RD
    IOT -->|"Cache<br/>DB 2"| RD
    ANL -->|"Cache<br/>DB 3"| RD
    PC -->|"Cache<br/>DB 4"| RD
    GW -->|"Cache<br/>DB 0"| RD
    SIM -->|"Publish 1/s<br/>JSON payload<br/>128 samples"| MQ
    MQ -->|"Stream<br/>Real-time"| NR

    style FC fill:#4CAF50,stroke:#2E7D32,color:#fff,stroke-width:2px
    style FV fill:#00BCD4,stroke:#0097A7,color:#fff,stroke-width:2px
    style GW fill:#FF9800,stroke:#F57C00,color:#fff,stroke-width:2px
    style ECG fill:#2196F3,stroke:#1976D2,color:#fff,stroke-width:2px
    style IOT fill:#9C27B0,stroke:#7B1FA2,color:#fff,stroke-width:2px
    style ANL fill:#FFC107,stroke:#FFA000,color:#000,stroke-width:2px
    style PC fill:#E91E63,stroke:#C2185B,color:#fff,stroke-width:2px
    style PG fill:#607D8B,stroke:#455A64,color:#fff,stroke-width:3px
    style RD fill:#F44336,stroke:#D32F2F,color:#fff,stroke-width:3px
    style MQ fill:#795548,stroke:#5D4037,color:#fff,stroke-width:3px
    style NR fill:#FF5722,stroke:#E64A19,color:#fff,stroke-width:2px
    style SIM fill:#009688,stroke:#00796B,color:#fff,stroke-width:2px
```

### Core Components

**Data & Messaging Infrastructure** (4 services):
- **PostgreSQL 15 + TimescaleDB** - Time-series optimized storage with JSONB for ECG samples
- **Redis 7** - High-performance caching (5 DB namespaces) and session management
- **MQTT Broker (Mosquitto 2)** - Real-time message brokering for IoT data streams
- **Node-RED 3.x** - Visual dataflow programming with 60-point rolling buffer

**Data Generation** (1 service):
- **ECG Simulator** - Python-based realistic ECG data from research dataset (128 Hz, 6 zones)

**Microservices Layer** (4 services):
- **ECG Service** - R-peak detection (Pan-Tompkins), zone classification, signal quality
- **IoT Service** - MQTT-to-PostgreSQL persistence, device management, historical queries
- **Analysis Service** - Advanced signal processing (autocorrelation, wavelets, graph theory)
- **PointCloud Service** - 3D cardiac activation mapping, 8 anatomical regions, video generation

**API & Frontend Layer** (3 services):
- **API Gateway** - Unified REST API aggregation, CORS-enabled, service proxy
- **Frontend Classic** - Interactive web dashboard with Canvas-based ECG visualization
- **Frontend VR** - HoloLens AR-optimized interface with THREE.js 3D pointcloud

---

## Quick Start

### Prerequisites

- **Docker Desktop**: [Download](https://www.docker.com/products/docker-desktop/)
- **Git**: [Download](https://git-scm.com/downloads)
- **8GB RAM** minimum, 16GB recommended
- **10GB free disk space**

### Installation

1. **Clone Repository**
```bash
git clone https://github.com/do3-173/XR_ECG_Twin.git
cd XR_ECG_Twin
```

2. **Start Docker Desktop**
   - Wait for "Docker Desktop is running" status

3. **Build and Launch All Services**
```bash
docker-compose up --build
```

First build takes 5-10 minutes. Subsequent starts take ~30 seconds.

4. **Access Applications**

| Interface | URL | Purpose |
|-----------|-----|---------|
| Classic Web | http://localhost:3001 | Interactive dashboard with history |
| VR Interface | http://localhost:3002 | HoloLens AR-optimized view |
| Node-RED Editor | http://localhost:1880 | Visual flow programming |
| API Gateway | http://localhost:8000/api | REST API endpoints |
| ECG Service | http://localhost:8001/api | ECG processing API |
| IoT Service | http://localhost:8002/api | Device data API |
| Analysis Service | http://localhost:8003/api | Signal analysis API |
| PointCloud Service | http://localhost:8004/api | 3D visualization API |

---

## Detailed Service Documentation

### 1. PostgreSQL + TimescaleDB (Port 5433)

**Purpose**: Primary data persistence layer with time-series optimization

**Technology**:
- PostgreSQL 15
- TimescaleDB extension for time-series data
- Supports hypertables for efficient time-based queries

**Schema**:
- Device registration and metadata
- Sensor data with JSONB ECG samples
- Analysis results and job tracking
- Point cloud and activation data
- Video generation metadata

**Configuration**:
```yaml
Database: ecg_db
User: ecg_user
Password: ecg_password (CHANGE IN PRODUCTION)
Internal Port: 5432
External Port: 5433
```

**Data Retention**: Infinite (configure compression/retention policies as needed)

**Access**:
```bash
docker exec -it ecg_postgres psql -U ecg_user -d ecg_db
```

**Health Check**: `pg_isready` every 10s

---

### 2. Redis (Port 6379)

**Purpose**: High-performance caching and session storage

**Technology**: Redis 7 Alpine (minimal Docker image)

**Usage**:
- Cache for analysis results (3600s TTL)
- Session management for API services
- Temporary job status storage
- Rate limiting data

**Configuration**:
- Persistence: RDB snapshots to `/data` volume
- Max memory: System dependent
- Eviction policy: allkeys-lru (default)

**Namespaces** (by database index):
- DB 0: Gateway cache
- DB 1: ECG Service cache
- DB 2: IoT Service cache
- DB 3: Analysis Service cache
- DB 4: PointCloud Service cache

**Access**:
```bash
docker exec -it ecg_redis redis-cli
```

**Health Check**: `redis-cli ping` every 10s

---

### 3. MQTT Broker - Eclipse Mosquitto (Port 1884)

**Purpose**: Real-time message brokering for IoT data streams

**Technology**: Eclipse Mosquitto 2 (MQTT 3.1.1/5.0 compatible)

**Topics**:
- `smartwatch/data` - Real-time ECG data from simulator
- `smartwatch/status` - Device status updates

**Message Format** (smartwatch/data):
```json
{
  "timestamp": 1699012345.678,
  "heart_rate": 75,
  "zone": 2,
  "ecg_samples": [128 float values],
  "source": "ECGdata_s1p1v1.dat",
  "participant": 1
}
```

**Configuration**:
- QoS: 0 (fire and forget) - configurable
- Persistence: Enabled in `/mosquitto/data`
- Max connections: Unlimited (default)
- Port mapping: 1884:1883 (external:internal)
- WebSocket: 9002:9001 (for browser clients)

**Subscribers**:
- Node-RED flow for buffering and processing
- IoT Service for database persistence

**Access**:
```bash
mosquitto_sub -h localhost -p 1884 -t "smartwatch/data"
mosquitto_pub -h localhost -p 1884 -t "test" -m "hello"
```

**Health Check**: `mosquitto_sub -t "$SYS/#"` every 10s

---

### 4. Node-RED (Port 1880)

**Purpose**: Visual dataflow programming for real-time ECG processing

**Technology**: Node-RED 3.x with custom nodes

**Flows**:
1. **MQTT Input** - Subscribe to `smartwatch/data`
2. **Buffer Management** - Maintain rolling 60-point history
3. **Statistics Calculation** - Min/max/average heart rate
4. **HTTP Endpoints** - Expose data via REST API

**Exposed Endpoints**:
- `GET /heartrate` - Returns latest reading + 60-point history

**Response Format**:
```json
{
  "heart_rate": 75,
  "zone": 2,
  "timestamp": 1699012345.678,
  "ecg_samples": [128 floats],
  "history": [
    {"hr": 74, "ts": 1699012344.678, "zone": 2},
    ...59 more points
  ],
  "stats": {
    "min": 68,
    "max": 82,
    "avg": 75.3
  }
}
```

**Buffer Size**: 60 data points (60 seconds at 1Hz)

**Flow Configuration**: Persistent in `/data/flows.json` volume

**UI Access**: http://localhost:1880 (flow editor)

**Dependencies**:
- Requires MQTT broker connection
- Used by API Gateway for real-time data

---

### 5. ECG Simulator

**Purpose**: Generate realistic ECG data from research dataset

**Technology**: Python 3.10 with custom ECG processor

**Dataset Source**: Research ECG recordings (not included in repo for privacy)
- 12 participants
- 3 sessions each
- 7 video recordings per session
- 128 Hz sampling rate

**Configuration** (environment variables):
```yaml
MQTT_BROKER: mqtt            # Internal hostname
MQTT_PORT: 1883              # Internal port
PARTICIPANT: 1               # Which participant data to use (1-12)
SESSION: 1                   # Session number (1-3)
MAX_VIDEOS: 1                # Number of videos to concatenate (1-7)
RANDOM_PARTICIPANTS: false   # Random participant selection when looping
```

**Current Setup**: Participant 1, Session 1, Video 1 (~37 seconds of data, loops continuously)

**Data Processing**:
1. Load `.dat` files from dataset
2. Calculate heart rate using R-peak detection
3. Classify into 6 heart rate zones
4. Publish to MQTT every 1 second

**Heart Rate Zones**:
| Zone | Range (BPM) | Description | Color |
|------|-------------|-------------|-------|
| 0 | < 40 | Below normal | Dark gray |
| 1 | 40-60 | Rest | Blue |
| 2 | 61-90 | Light activity | Green |
| 3 | 91-110 | Moderate activity | Yellow |
| 4 | 111-130 | Intense activity | Orange |
| 5 | 131+ | Maximum effort | Red |

**Restart**: `docker-compose restart simulator`

**Logs**: `docker-compose logs -f simulator`

---

### 6. API Gateway (Port 8000)

**Purpose**: Unified REST API aggregation and routing

**Technology**: Django 4.2 + Django REST Framework

**Architecture**:
- Aggregates data from Node-RED and IoT Service
- Provides CORS-enabled endpoints for frontends
- No authentication (add for production)
- Proxy to microservices

**Endpoints**:

**GET /api/heartrate/**
- Returns latest ECG data with history
- Aggregates Node-RED buffer + IoT Service metadata
- Response time: < 50ms (cached)

**GET /api/ecg/latest/**
- Latest ECG reading from ECG Service
- Includes R-peak detection results

**GET /api/status/**
- System health status
- Service availability checks

**Proxy Endpoints**:
- `/api/ecg/*` → ECG Service (8001)
- `/api/iot/*` → IoT Service (8002)
- `/api/analysis/*` → Analysis Service (8003)
- `/api/activation/*` → PointCloud Service (8004)

**Configuration**:
```python
DEBUG = True  # DISABLE IN PRODUCTION
ALLOWED_HOSTS = ['*']  # RESTRICT IN PRODUCTION
CORS_ALLOW_ALL_ORIGINS = True  # CONFIGURE IN PRODUCTION
```

**Database**: SQLite (development) - Migrate to PostgreSQL for production

**Cache**: Redis DB 0

---

### 7. ECG Service (Port 8001)

**Purpose**: ECG signal processing and feature extraction

**Technology**: Django 4.2 + NumPy + SciPy

**Capabilities**:
- R-peak detection (Pan-Tompkins algorithm)
- Heart rate calculation
- Zone classification
- QRS complex detection
- Signal quality assessment

**Algorithms**:
1. **Bandpass filtering** (0.5-50 Hz) to remove baseline wander and noise
2. **Differentiation** to enhance QRS slopes
3. **Squaring** to emphasize higher frequencies
4. **Moving window integration** to smooth
5. **Adaptive thresholding** for peak detection

**Models**:
- `ECGReading` - Stores processed ECG data
- `HeartRateZone` - Zone classification rules

**Endpoints**:

**GET /api/ecg/latest/**
```json
{
  "id": 123,
  "timestamp": "2024-01-15T10:30:00Z",
  "heart_rate": 75,
  "zone": 2,
  "r_peaks": [128, 256, 384, ...],
  "signal_quality": 0.95
}
```

**POST /api/ecg/process/**
```json
{
  "ecg_samples": [128 float values],
  "sampling_rate": 128
}
```

**Database**: PostgreSQL (shared with IoT Service)

**Cache**: Redis DB 1 (60s TTL for latest readings)

**Performance**: < 100ms for 128 samples

---

### 8. IoT Service (Port 8002)

**Purpose**: MQTT-to-database persistence layer

**Technology**: Django 4.2 + paho-mqtt + PostgreSQL

**Architecture**:
- Background MQTT subscriber (separate process)
- Django ORM for data persistence
- REST API for querying historical data

**MQTT Subscriber**:
- Subscribes to `smartwatch/data` topic
- Converts MQTT messages to Django models
- Stores ECG samples as JSONB in PostgreSQL
- Automatically creates device records

**Models**:

**Device**:
```python
device_id: str (unique identifier)
device_type: str (e.g., "smartwatch")
name: str (display name)
is_active: bool
last_seen: datetime
created_at: datetime
```

**SensorData**:
```python
device: ForeignKey(Device)
timestamp: datetime (indexed)
heart_rate: int
zone: int (0-5)
ecg_samples: JSONB (array of 128 floats)
source_file: str (dataset filename)
participant_id: int
created_at: datetime
```

**Endpoints**:

**GET /api/devices/**
- List all registered devices
- Auto-registration on first data

**GET /api/sensor-data/**
- Query parameters: `device_id`, `start_time`, `end_time`, `limit`
- Returns paginated sensor readings

**POST /api/sensor-data/**
- Manual data ingestion (for testing)

**Storage Statistics**:
- Average record size: ~2KB (128 float samples)
- 1 hour of data: ~3600 records = ~7.2 MB
- 24 hours: ~86,400 records = ~173 MB

**Database**: PostgreSQL with TimescaleDB extension

**MQTT Process**: Runs as Django management command in Docker entrypoint

---

### 9. Analysis Service (Port 8003)

**Purpose**: Advanced ECG signal processing and feature extraction

**Technology**: Django 4.2 + NumPy + SciPy + PyWavelets + NetworkX

**Algorithms** (Python translations of MATLAB code):

**1. Autocorrelation Analysis** (`signal_autocorr.py`):
- FFT-based autocorrelation for O(N log N) complexity
- Periodicity detection and cycle length estimation
- Exponential decay rate calculation
- First minimum/peak lag detection

**2. Wavelet Decomposition** (`modwt.py`, `wavelet_features.py`):
- Stationary Wavelet Transform (approximates MATLAB MODWT)
- Multi-scale decomposition (6 levels default)
- Wavelet families: sym4, db4
- Energy distribution across scales
- Entropy calculation per level
- Cross-correlation matrix (6x6) between scales

**3. Graph-Theoretic Features** (`graph_features.py`):
- Adjacency matrix construction from wavelet coefficients
- Threshold-based graph creation
- Network topology metrics:
  - Graph density
  - Average clustering coefficient
  - Average node degree
  - Degree centrality distribution
  - Network diameter

**4. Visualization** (`visualization.py`):
- Multi-panel ECG analysis plots
- Autocorrelation function plots
- Wavelet coefficient heatmaps
- Network graphs with centrality coloring

**Models**:
- `AnalysisJob` - Job tracking with UUID
- `AnalysisResult` - Stores computed features as JSONB

**Endpoints**:

**POST /api/analysis/process/**
```json
{
  "ecg_signal": [128-100000 float values],
  "sampling_rate": 128,
  "device_id": "smartwatch_001",
  "participant_id": 1
}
```

Response:
```json
{
  "job_id": "a1b2c3d4-e5f6-7g8h-9i0j-k1l2m3n4o5p6",
  "status": "completed",
  "processing_time": 1.234
}
```

**GET /api/analysis/result/<job_id>/**
```json
{
  "job_id": "...",
  "status": "completed",
  "features": {
    "autocorr": {
      "first_min_lag": 0.5,
      "first_peak_lag": 0.75,
      "decay_rate": 0.123
    },
    "wavelet": {
      "energy_distribution": [0.4, 0.3, 0.15, ...],
      "entropy": [1.2, 1.5, 1.8, ...],
      "cross_correlation": [[1.0, 0.8, ...], ...]
    },
    "graph": {
      "density": 0.45,
      "avg_clustering": 0.67,
      "avg_degree": 12.3,
      "diameter": 5
    }
  },
  "processing_time": 1.234
}
```

**GET /api/analysis/latest/**
- Query parameters: `device_id`, `participant_id`
- Returns most recent analysis result

**Performance**:
- 1000 samples (7.8s ECG): ~10-50ms
- 5000 samples (39s ECG): ~100ms - 2s
- 10000 samples (78s ECG): ~500ms - 5s

**Caching**: Redis DB 3 (3600s TTL)

**Use Cases**:
- Arrhythmia detection preprocessing
- Heart rate variability analysis
- Signal quality metrics
- Research feature extraction

---

### 10. PointCloud Service (Port 8004)

**Purpose**: 3D cardiac activation visualization and video generation

**Technology**: Django 4.2 + NumPy + OpenCV + Matplotlib

**Data Model**:

**PointCloud**:
- 3D coordinates of cardiac surface points
- Typically 3000-20000 points
- JSONB storage for flexibility

**ECGData**:
- ECG signal with annotated landmarks
- P wave, QRS complex, T wave markers
- Time alignment data

**ActivationAnalysis**:
- Point cloud + ECG data association
- Computed activation patterns
- 8 anatomical regions:
  1. SA Node (Sinoatrial - natural pacemaker)
  2. Right Atrium
  3. Left Atrium
  4. AV Node (Atrioventricular - conduction delay)
  5. His Bundle
  6. Bundle Branches
  7. Apex (Purkinje start)
  8. Purkinje Fibers (extended network)

**ActivationSpace** (N x 8 matrix):
- Maps each point to cardiac regions
- Binary membership (1 if point belongs to region, 0 otherwise)

**ActivationTime** (8 x T matrix):
- Temporal activation per region
- 4 states: Inactive (0), Trigger (1), Depolarization (2), Repolarization (3)

**ActivationVideo**:
- MP4 video generation
- Two modes:
  - **Ideal**: Discrete activation states (0, 1, 2, 3)
  - **Eigen**: Continuous amplitude values
- Configurable frame rate (15-60 fps)

**Endpoints**:

**POST /api/pointclouds/**
- Upload 3D heart model

**POST /api/ecg-data/**
- Upload ECG with landmarks

**POST /api/activation-analysis/compute/**
- Compute activation patterns
- Links point cloud + ECG data

**POST /api/activation-video/generate/**
- Generate visualization video
- Async processing with job tracking

**Visualization**:
- Color-coded activation states
- 3D rotation animations
- Time-synchronized with ECG waveform

**Media Storage**: Persistent volume `/app/media`

---

### 11. Frontend (Classic Web Interface - Port 3001)

**Purpose**: Interactive web dashboard for real-time ECG monitoring

**Technology**: React 18 + TypeScript + Canvas API

**Features**:

**Real-Time ECG Visualization** (1200x300px):
- High-performance Canvas rendering
- Scrolling waveform (last 5 seconds)
- Red ECG grid background
- Automatic scaling
- 60 FPS rendering

**Heart Rate History** (1200x400px):
- 60-second rolling history
- Zone-colored backgrounds (6 zones)
- Interactive points (click for exact BPM tooltip)
- Hover effects (orange highlight)
- Grid lines at key BPM thresholds (40, 60, 90, 110, 130, 150)
- Time labels (-60s, -45s, -30s, -15s, now)

**Stats Panel**:
- Current heart rate (large display)
- Current zone with color indicator
- Last update timestamp
- Min/Max/Average from 60-point history

**Responsive Design**:
- Works on desktop and tablet
- Minimum width: 1200px for optimal experience

**Update Frequency**: Polls API Gateway every 1 second

**Build**:
```bash
cd frontend
npm install
npm run build
```

**Development**:
```bash
npm start  # Runs on localhost:3000
```

**Docker**: Nginx serves static build from port 3001

---

### 12. Frontend VR (HoloLens Interface - Port 3002)

**Purpose**: AR-optimized interface for HoloLens and mixed reality headsets

**Technology**: React 18 + TypeScript + Canvas API + THREE.js

**Design Philosophy**:
- Dark theme (#001020 background) for AR overlay visibility
- Cyan accents (#00d4ff) for high contrast in mixed reality
- Large touch targets (60px minimum) for hand gesture control
- Glow effects and backdrop blur for depth perception

**Views**:

**1. Overview** (Default):
- 3-card grid layout:
  - Heart Rate (large display)
  - Zone indicator (color-coded)
  - Timestamp
- Mini ECG preview (800x200px)
- Quick stats footer

**2. ECG View**:
- Full-screen ECG visualization (1000x500px)
- Optimized for AR viewing distance
- Persistent footer with current HR

**3. History View**:
- Full-screen history chart (1000x500px)
- Zone-colored background regions
- Interactive time selection

**4. PointCloud Heart** (NEW):
- 3D cardiac activation visualization
- MATLAB-derived activation data (3162 points, 152 time samples)
- Interactive THREE.js rendering:
  - OrbitControls with optimized zoom/pan/rotate
  - Mouse controls: Left-drag (rotate), Wheel (zoom), Right-drag (pan)
  - Manual control buttons for precise adjustment
- Real-time activation state visualization:
  - Gray: Inactive
  - Green: Trigger
  - Red: Depolarization
  - Blue: Repolarization
- Synchronized ECG waveform display
- Animation controls (play/pause/speed/time scrubber)
- Legend overlay
- Reset to default view

**View Navigation**:
- Bottom tab buttons with active state styling
- Smooth transitions between views
- Gesture-friendly spacing

**HoloLens Metadata** (index.html):
```html
<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
```

**Performance**:
- 60 FPS target for smooth AR rendering
- Optimized Canvas operations
- Efficient state management

**Build**:
```bash
cd frontend-vr
npm install
npm run build
```

**Docker**: Nginx serves static build from port 3002

**THREE.js PointCloud Configuration**:
```typescript
// Optimized control settings
dampingFactor: 0.25
zoomSpeed: 1.5
minDistance: 2
maxDistance: 100
rotateSpeed: 1.0
panSpeed: 1.0
```

---

## Data Flow Diagram

```
1. Simulator reads dataset
   ↓
2. Publishes to MQTT (smartwatch/data)
   ↓
3a. Node-RED buffers (60 points) → Gateway → Frontends
3b. IoT Service persists → PostgreSQL
   ↓
4. User triggers analysis (optional)
   ↓
5. Analysis Service processes signal
   ↓
6. Results cached in Redis + stored in PostgreSQL
   ↓
7. Frontend displays results
```

---

## Technology Stack

### Backend
- **Django 4.2** - Web framework
- **Django REST Framework 3.14** - API development
- **PostgreSQL 15 + TimescaleDB** - Time-series database
- **Redis 7** - Caching layer
- **paho-mqtt 1.6** - MQTT client
- **Python 3.10** - Core language

### Signal Processing
- **NumPy 1.24** - Numerical computing
- **SciPy 1.10** - Signal processing
- **PyWavelets 1.4** - Wavelet transforms
- **NetworkX 3.1** - Graph analysis
- **OpenCV 4.8** - Video generation
- **Matplotlib 3.7** - Visualization

### Frontend
- **React 18** - UI framework
- **TypeScript 5** - Type safety
- **THREE.js** - 3D graphics (VR only)
- **Canvas API** - High-performance rendering
- **CSS3** - Styling with animations

### Infrastructure
- **Docker 24** - Containerization
- **Docker Compose 2.x** - Orchestration
- **Nginx 1.25** - Reverse proxy
- **Node-RED 3.x** - Flow-based programming
- **Eclipse Mosquitto 2** - MQTT broker

---

## Environment Variables

### Simulator
```bash
MQTT_BROKER=mqtt          # Broker hostname
MQTT_PORT=1883            # Broker port
PARTICIPANT=1             # Participant ID (1-12)
SESSION=1                 # Session number (1-3)
MAX_VIDEOS=1              # Videos to concatenate (1-7)
RANDOM_PARTICIPANTS=0     # Random selection (0 or 1)
```

### Services (Common)
```bash
DATABASE_URL=postgresql://ecg_user:ecg_password@postgres:5432/ecg_db
REDIS_URL=redis://redis:6379/0
DEBUG=True                # DISABLE IN PRODUCTION
ALLOWED_HOSTS=*           # RESTRICT IN PRODUCTION
```

### Gateway
```bash
ECG_SERVICE_URL=http://ecg-service:8001
IOT_SERVICE_URL=http://iot-service:8002
NODE_RED_URL=http://nodered:1880
```

---

## API Reference

### Gateway Endpoints

**GET /api/heartrate/**
```bash
curl http://localhost:8000/api/heartrate
```

Response:
```json
{
  "heart_rate": 75,
  "zone": 2,
  "timestamp": 1699012345.678,
  "ecg_samples": [128 floats],
  "history": [60 data points],
  "stats": {"min": 68, "max": 82, "avg": 75.3}
}
```

**GET /api/ecg/latest/**
```bash
curl http://localhost:8001/api/ecg/latest/
```

**POST /api/analysis/process/**
```bash
curl -X POST http://localhost:8003/api/analysis/process/ \
  -H "Content-Type: application/json" \
  -d '{
    "ecg_signal": [1000 samples...],
    "sampling_rate": 128,
    "device_id": "smartwatch_001"
  }'
```

**GET /api/analysis/result/{job_id}/**
```bash
curl http://localhost:8003/api/analysis/result/a1b2c3d4.../
```

---

## Development

### Running Services Locally (Without Docker)

**1. Start Infrastructure**
```bash
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=ecg_password timescale/timescaledb:latest-pg15
docker run -d -p 6379:6379 redis:7-alpine
docker run -d -p 1883:1883 eclipse-mosquitto:2
```

**2. Setup Python Services**
```bash
# Gateway
cd gateway
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8000

# ECG Service (new terminal)
cd services/ecg_service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8001

# IoT Service (new terminal)
cd services/iot_service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8002

# Analysis Service (new terminal)
cd services/ecg_analysis_service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8003

# PointCloud Service (new terminal)
cd services/pointcloud_service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8004
```

**3. Start Simulator**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python smartwatch_simulator.py --broker localhost --port 1883
```

**4. Run Frontend**
```bash
cd frontend
npm install
npm start  # Opens on localhost:3000

# VR Frontend (new terminal)
cd frontend-vr
npm install
npm start  # Opens on localhost:3000
```

### Code Style Guidelines

**Python**:
- Use docstrings for all functions/classes (not inline comments)
- Follow PEP 8
- Type hints where applicable
- Comprehensive docstrings with Args, Returns, Raises sections

**TypeScript/React**:
- Use JSDoc comments for complex functions
- Props interfaces for all components
- Descriptive variable names (avoid abbreviations)
- Component-level comments explaining purpose

**General**:
- Prefer docstrings over inline comments
- Comments should explain "why", not "what"
- Self-documenting code where possible

---

## Docker Commands

### Basic Operations
```bash
docker-compose up -d                    # Start all services
docker-compose up --build               # Rebuild and start
docker-compose down                     # Stop and remove containers
docker-compose restart <service>        # Restart specific service
docker-compose logs -f <service>        # Follow service logs
docker-compose ps                       # List running services
docker-compose exec <service> bash      # Shell into container
```

### Service-Specific Commands
```bash
# Rebuild frontend after code changes
docker-compose build frontend-vr
docker-compose stop frontend-vr
docker-compose rm -f frontend-vr
docker-compose up -d frontend-vr

# Run Django migrations
docker-compose exec gateway python manage.py migrate
docker-compose exec ecg-service python manage.py migrate
docker-compose exec iot-service python manage.py migrate
docker-compose exec analysis-service python manage.py migrate
docker-compose exec pointcloud-service python manage.py migrate

# Database access
docker exec -it ecg_postgres psql -U ecg_user -d ecg_db

# Redis access
docker exec -it ecg_redis redis-cli

# View MQTT messages
docker exec -it ecg_mqtt mosquitto_sub -t "smartwatch/data"
```

### Cleanup
```bash
docker-compose down -v                  # Remove volumes
docker system prune -a -f               # Clean all unused resources
docker volume prune -f                  # Remove unused volumes
```

---

## Monitoring & Debugging

### Health Checks

Each service has health monitoring:
- PostgreSQL: `pg_isready` every 10s
- Redis: `redis-cli ping` every 10s
- MQTT: `mosquitto_sub -t "$SYS/#"` every 10s

### Service Logs
```bash
docker-compose logs -f simulator        # Simulator output
docker-compose logs -f iot-service      # MQTT subscriber logs
docker-compose logs -f gateway          # API requests
docker-compose logs -f analysis-service # Processing jobs
```

### Database Queries
```bash
# Count sensor data records
docker exec -it ecg_postgres psql -U ecg_user -d ecg_db \
  -c "SELECT COUNT(*) FROM iot_sensordata;"

# Latest 10 readings
docker exec -it ecg_postgres psql -U ecg_user -d ecg_db \
  -c "SELECT heart_rate, zone, timestamp FROM iot_sensordata ORDER BY timestamp DESC LIMIT 10;"

# Analysis job status
docker exec -it ecg_postgres psql -U ecg_user -d ecg_db \
  -c "SELECT job_id, status, processing_time FROM analysis_analysisresult ORDER BY created_at DESC LIMIT 10;"
```

### Redis Inspection
```bash
# View cached keys
docker exec -it ecg_redis redis-cli KEYS '*'

# Get cached analysis result
docker exec -it ecg_redis redis-cli GET 'analysis:latest:smartwatch_001'
```

### MQTT Testing
```bash
# Subscribe to all topics
docker exec -it ecg_mqtt mosquitto_sub -v -t "#"

# Publish test message
docker exec -it ecg_mqtt mosquitto_pub -t "test" -m "hello"
```

---

## Performance Benchmarks

### Simulator
- Data publishing rate: 1 message/second
- ECG samples per message: 128 (1 second @ 128 Hz)
- Loop time (Participant 1, Video 1): ~37 seconds

### IoT Service
- MQTT message processing: < 10ms
- Database write: < 50ms
- Total latency: < 100ms

### Analysis Service
- 1000 samples (7.8s ECG): 10-50ms
- 5000 samples (39s ECG): 100ms-2s
- 10000 samples (78s ECG): 500ms-5s

### Frontend
- API polling interval: 1 second
- Canvas render rate: 60 FPS
- Network latency: < 50ms (localhost)
- Total update latency: ~1.1 seconds

### Database
- Sensor data insert: < 50ms
- Query latest 60 records: < 100ms
- Analysis result retrieval: < 10ms (cached)

---

## Security Considerations

### Current State (Development)
- No authentication on any endpoint
- Default PostgreSQL password
- CORS allows all origins
- DEBUG mode enabled
- No HTTPS

### Production Checklist
- [ ] Enable Django authentication (JWT recommended)
- [ ] Change all default passwords (PostgreSQL, Redis if auth enabled)
- [ ] Restrict CORS to specific domains
- [ ] Set `DEBUG=False` in all Django services
- [ ] Configure `ALLOWED_HOSTS` properly
- [ ] Enable MQTT authentication
- [ ] Use HTTPS/TLS for all web traffic
- [ ] Use MQTTS (MQTT over TLS)
- [ ] Implement rate limiting
- [ ] Add input validation on all endpoints
- [ ] Use environment variables for secrets (not hardcoded)
- [ ] Regular security updates for dependencies
- [ ] Database connection encryption
- [ ] API key authentication for service-to-service calls

---

## Troubleshooting

### Frontend Not Updating
1. Hard refresh: `Ctrl+Shift+R` (Linux/Windows) or `Cmd+Shift+R` (Mac)
2. Check browser console for errors
3. Verify API Gateway is responding: `curl http://localhost:8000/api/heartrate`
4. Rebuild frontend:
```bash
docker-compose build frontend-vr
docker-compose restart frontend-vr
```

### Simulator Not Generating Data
1. Check logs: `docker-compose logs -f simulator`
2. Verify MQTT broker: `docker-compose logs mqtt`
3. Test MQTT subscription: `docker exec -it ecg_mqtt mosquitto_sub -t "smartwatch/data"`
4. Restart simulator: `docker-compose restart simulator`

### IoT Service Not Storing Data
1. Check logs: `docker-compose logs -f iot-service`
2. Verify PostgreSQL connection:
```bash
docker exec -it ecg_postgres psql -U ecg_user -d ecg_db -c "SELECT 1;"
```
3. Check sensor data count:
```bash
docker exec -it ecg_postgres psql -U ecg_user -d ecg_db -c "SELECT COUNT(*) FROM iot_sensordata;"
```

### Analysis Service Failing
1. Check memory usage (wavelet transforms are memory-intensive)
2. Verify Redis connection: `docker exec -it ecg_redis redis-cli ping`
3. Review logs: `docker-compose logs -f analysis-service`
4. Reduce signal length if processing large datasets

### Port Conflicts
```bash
# Check what's using a port
sudo lsof -i :3001
sudo lsof -i :8000

# Change ports in docker-compose.yml
# Example: "3011:80" instead of "3001:80"
```

### Database Migration Issues
```bash
# Reset migrations (DESTRUCTIVE)
docker-compose down -v
docker-compose up -d postgres redis mqtt
docker-compose exec gateway python manage.py migrate
docker-compose exec ecg-service python manage.py migrate
docker-compose exec iot-service python manage.py migrate
docker-compose exec analysis-service python manage.py migrate
docker-compose exec pointcloud-service python manage.py migrate
```

---

## Project Structure

```
XR_ECG_Twin/
├── docker-compose.yml              # Orchestrates all 12 services
├── .dockerignore                   # Excludes files from builds
├── README.md                       # This documentation
│
├── config.py                       # Shared configuration constants
├── ecg_processor.py                # ECG processing utilities
├── smartwatch_simulator.py         # Main simulator script
│
├── simulator/                      # Simulator Docker configuration
│   ├── Dockerfile
│   ├── entrypoint.sh
│   └── requirements.txt
│
├── gateway/                        # API Gateway (Port 8000)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── manage.py
│   ├── gateway/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   └── api/
│       ├── views.py                # Aggregation logic
│       └── urls.py
│
├── services/
│   ├── ecg_service/               # ECG Processing (Port 8001)
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── manage.py
│   │   ├── ecg_service/settings.py
│   │   └── ecg/
│   │       ├── models.py
│   │       ├── views.py
│   │       ├── serializers.py
│   │       └── signal_processing.py
│   │
│   ├── iot_service/               # IoT/MQTT (Port 8002)
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── manage.py
│   │   ├── iot_service/settings.py
│   │   └── iot/
│   │       ├── models.py           # Device, SensorData
│   │       ├── views.py
│   │       ├── mqtt_client.py      # MQTT subscriber
│   │       └── management/commands/
│   │           └── start_mqtt_subscriber.py
│   │
│   ├── ecg_analysis_service/      # Analysis (Port 8003)
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── manage.py
│   │   ├── ecg_analysis_service/settings.py
│   │   └── analysis/
│   │       ├── models.py
│   │       ├── views.py
│   │       ├── serializers.py
│   │       ├── algorithms/
│   │       │   ├── signal_autocorr.py
│   │       │   ├── modwt.py
│   │       │   ├── wavelet_features.py
│   │       │   └── graph_features.py
│   │       └── visualization.py
│   │
│   └── pointcloud_service/        # PointCloud (Port 8004)
│       ├── Dockerfile
│       ├── requirements.txt
│       ├── manage.py
│       ├── pointcloud_service/settings.py
│       └── activation/
│           ├── models.py           # PointCloud, ECGData, etc.
│           ├── views.py
│           ├── serializers.py
│           ├── compute_activation_space.py
│           ├── compute_activation_time.py
│           └── video_generator.py
│
├── nodered/                        # Node-RED Configuration
│   ├── Dockerfile
│   ├── flows.json                  # Flow definitions
│   └── settings.js
│
├── mqtt/                           # MQTT Broker Config
│   ├── config/mosquitto.conf
│   ├── data/                       # Persistent storage
│   └── log/                        # Broker logs
│
├── frontend/                       # Classic Web (Port 3001)
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   ├── tsconfig.json
│   ├── public/
│   └── src/
│       ├── App.tsx                 # Main dashboard
│       ├── App.css
│       ├── index.tsx
│       └── components/
│           └── ECGDisplay.tsx
│
└── frontend-vr/                    # HoloLens VR (Port 3002)
    ├── Dockerfile
    ├── nginx.conf
    ├── package.json
    ├── tsconfig.json
    ├── public/
    │   ├── index.html              # HoloLens metadata
    │   └── matlab_data/            # PointCloud activation data
    │       ├── activation_data.json
    │       └── activation_data_reduced.json
    └── src/
        ├── App.tsx                 # Legacy dashboard
        ├── App-VR.tsx              # Multi-view VR interface
        ├── App-VR.css
        ├── index.tsx
        └── components/
            ├── ECGDisplay.tsx
            ├── PointCloudHeart.tsx        # NEW: 3D visualization
            └── PointCloudActivation.tsx   # Backend integration
```

---

## Contributing

This project was developed as part of a Software Engineering course at Sapienza University of Rome.

---

## License

MIT License

---

## Acknowledgments

- Sapienza University of Rome for the ECG dataset
- Research participants for data contribution
- Open-source communities for libraries and tools
