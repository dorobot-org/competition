# User Guide - GPU Portal System

## Overview

This system provides a web portal for managing GPU instances for competition users. Admins can create users and assign GPU instances, while users can start/stop their assigned instances.

---

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

Access at: http://localhost

### Option 2: Docker Offline Installation

1. Build and export images:
```bash
./docker-build.sh
```

2. Copy `docker-export/` folder to target machine

3. On target machine:
```bash
cd docker-export
./install.sh
```

### Option 3: Development Mode

#### Start Backend
```bash
./run_backend.sh
```
Backend runs at: http://localhost:8000

#### Start Frontend
```bash
./run_frontend.sh
```
Frontend runs at: http://localhost:5173

---

## Default Admin Account

| Field | Value |
|-------|-------|
| Phone | `13800000000` |
| Password | `DongSheng2025#` |

---

## Admin Guide

### 1. Login as Admin

1. Open http://localhost:5173
2. Enter phone: `13800000000`
3. Enter password: `DongSheng2025#`
4. Click "Login"

### 2. Add GPU Instances

Before creating users, you need to add GPU instances to the system.

1. Click "Manage" button in the header
2. Go to "GPU Instances" tab
3. Click "Add Instance"
4. Fill in:
   - **Instance UUID**: The UUID from GPUFree (e.g., `abc123-def456-...`)
   - **Nickname**: Display name (e.g., `GPU-01`)
   - **VNC URL**: The target URL for this instance (optional)
5. Click "Save"

The system will automatically fetch the instance ID from GPUFree API.

### 3. Create Users

1. In the Admin panel, go to "Users" tab
2. Click "Add User"
3. Fill in:
   - **Username**: User's display name
   - **Phone**: User's phone number (used for login)
   - **Password**: Initial password
   - **GPU Instance**: Select from available instances dropdown
   - **Target URL**: Will be auto-filled from instance's VNC URL
4. Click "Save"

**Note**: Each admin can create up to 15 users.

### 4. Manage Users

- **View**: See all users you created
- **Edit**: Click edit icon to modify user details
- **Delete**: Click delete icon to remove user (releases their GPU instance)
- **Password**: You can see plaintext passwords in the edit dialog

---

## User Guide

### 1. Login

1. Open http://localhost:5173
2. Enter your phone number
3. Enter your password
4. Click "Login"

### 2. Start Your Instance

1. After login, you'll see the portal page
2. If you have a GPU instance assigned, click the green "Start" button
3. Wait for the instance to start (status will show "Starting...")
4. Once ready, the workspace will appear in the iframe

### 3. Use Your Workspace

- Your GPU workspace is displayed in the main area
- The current time is shown in the header
- Your session is being monitored for activity

### 4. Stop Your Instance

- Click the red "Stop" button to stop your instance
- This releases GPU resources

### 5. Logout

- Click "Logout" button to exit

---

## Automatic Inactivity Detection

The system monitors user activity:

- Frontend sends a heartbeat every 30 seconds while active
- If no heartbeat is received for 5 minutes, the instance is automatically stopped
- This happens when:
  - User closes the browser
  - User's computer goes to sleep
  - Network disconnection

This helps conserve GPU resources when users forget to stop their instances.

---

## Troubleshooting

### "No GPU Instance Assigned"
- Contact your admin to assign a GPU instance to your account

### Cannot Login
- Verify phone number and password with your admin
- Admin can check/reset your password in the user edit dialog

### Instance Won't Start
- Check if the GPU instance is properly configured
- Verify the bearer token is valid (admin setting)

### Instance Stops Unexpectedly
- The auto-stop feature stops instances after 5 minutes of inactivity
- Keep the browser tab open and active to maintain the session

---

## Technical Details

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/login` | POST | User login |
| `/api/portal/action` | POST | Start/stop instance |
| `/api/portal/heartbeat` | POST | Activity heartbeat |
| `/api/portal/query-instance` | GET | Check instance status |
| `/api/users` | GET/POST | User management (admin) |
| `/api/instances` | GET/POST | Instance management (admin) |

### Database

- SQLite database: `backend/portal.db`
- Tables: `users`, `gpu_instances`

### Configuration

| Setting | Value | Location |
|---------|-------|----------|
| Heartbeat Interval | 30 seconds | Frontend |
| Inactivity Timeout | 5 minutes | Backend |
| Inactivity Check | 60 seconds | Backend |
| Max Users per Admin | 15 | Backend |

---

## Docker Deployment

### File Structure

```
haidianrobot/
├── docker-compose.yml      # Service orchestration
├── docker-build.sh         # Build and export script
├── backend/
│   ├── Dockerfile
│   └── .dockerignore
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── .dockerignore
└── data/                   # Database volume (created on first run)
    └── portal.db
```

### Data Persistence

Database is stored in `./data/portal.db` (mapped as Docker volume).

To backup:
```bash
cp ./data/portal.db ./backup/portal.db.bak
```

To restore:
```bash
cp ./backup/portal.db.bak ./data/portal.db
docker-compose restart backend
```

### Offline Export

The `docker-build.sh` script creates a portable package:

```bash
./docker-build.sh
```

Output in `docker-export/`:
- `gpu-portal-docker.tar` - Docker images (~500MB)
- `docker-compose.yml` - Service configuration
- `install.sh` - Installation script
- `README.txt` - Instructions

### Docker Commands

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop services
docker-compose down

# Restart
docker-compose restart

# Check status
docker-compose ps
```
