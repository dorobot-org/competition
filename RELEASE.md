# Release Notes

## v0.4.1 (2025-12-03)

### Fixes
- Fix daily 2AM shutdown to stop ALL assigned instances regardless of user state
- Fix daily shutdown to use Beijing timezone (Asia/Shanghai) explicitly

### Changes
- Daily shutdown now queries all users with `instance_id` assigned, not just `state == "active"`
- Uses `zoneinfo.ZoneInfo("Asia/Shanghai")` for reliable Beijing time calculation

---

## v0.4.0 (2025-12-03)

### Features
- **Increased User Limit**: Admin can now create up to 128 users (was 15)
- **Extended Inactivity Timeout**: Auto-stop after 180 minutes (was 5 minutes)
- **Daily Scheduled Shutdown**: All instances automatically stop at 2AM Beijing time

### Background Tasks
- Inactivity check runs every 60 seconds
- Daily shutdown task calculates next 2AM and sleeps until then

---

## v0.3.0 (2025-12-03)

### Features
- **Docker Support**: Full Docker containerization with docker-compose
- **Offline Export**: `docker-build.sh` creates portable tar file for offline installation
- **Data Persistence**: Database mapped as external volume (`./data/portal.db`)

### Docker Files
- `backend/Dockerfile` - Python 3.11 slim image
- `frontend/Dockerfile` - Multi-stage build with nginx
- `frontend/nginx.conf` - Reverse proxy to backend API
- `docker-compose.yml` - Service orchestration
- `docker-build.sh` - Build and export script

### Changes
- Centralized API URL config in `frontend/src/config.js`
- Database path configurable via `DATABASE_PATH` environment variable

---

## v0.2.1 (2025-12-03)

### Features
- **Heartbeat-based Inactivity Detection**: Auto-stop GPU instances after inactivity
- Frontend sends heartbeat every 30 seconds when instance is active
- Backend checks every 60 seconds for inactive users (>5 min without heartbeat)

### Backend Changes
- Added `last_heartbeat` field to User model
- Added `/api/portal/heartbeat` endpoint
- Added `check_inactive_users()` background task

### Frontend Changes
- Added heartbeat functions in Portal.vue
- Heartbeat starts when instance becomes active
- Heartbeat stops on logout, stop, or page unload

---

## v0.2.0 (2025-12-03)

### Features
- **Plain Password Display**: Admin can see user passwords in edit dialog
- **GPU Instance Management**: Assign GPU instances to users
- **GPUFree API Integration**: Start/stop instances via GPUFree API

### Changes
- Login changed from username to phone number
- Default admin: Phone `13800000000`, Password `DongSheng2025#`
- Removed demo user

---

## v0.1.1 (2024-12-03)

### Features
- **User Portal**: Full-screen iframe wrapper for viewing target websites
- **Authentication System**: JWT-based login with admin and normal user roles
- **Admin Console**: Complete user management (add/edit/delete users)
- **Session Control**: Start/Stop buttons to activate/deactivate user sessions
- **5-second Countdown**: Smooth transition before loading target URL

### UI/UX Improvements
- Streamlined header bar with Start/Stop buttons alongside Logout
- Maximized content area for website viewing
- Clean welcome screen with "Ready to Start" prompt
- Countdown indicator in header during session start
- Professional dark theme design

### Default Users
- Admin: `admin` / `admin`
- Demo: `demo` / `demo1234`
- Target URL: https://docs.swanlab.cn/guide_cloud/general/quick-start.html

### Tech Stack
- **Backend**: FastAPI + SQLite + SQLAlchemy + JWT Auth
- **Frontend**: Vue.js 3 + Vite + Pinia + Vue Router
- **Styling**: Custom CSS with gradient themes

### Files Structure
```
haidianrobot/
├── backend/
│   ├── main.py           # FastAPI application
│   ├── database.py       # SQLite configuration
│   ├── models.py         # User database model
│   ├── schemas.py        # Pydantic schemas
│   ├── auth.py           # JWT authentication
│   ├── init_db.py        # Database initialization
│   └── requirements.txt  # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── main.js
│   │   ├── App.vue
│   │   ├── style.css
│   │   ├── router/
│   │   ├── stores/
│   │   └── views/
│   │       ├── Login.vue
│   │       ├── Portal.vue
│   │       └── Admin.vue
│   └── index.html
├── run_backend.sh
├── run_frontend.sh
├── .gitignore
└── RELEASE.md
```

### Running the Application
1. Start backend: `./run_backend.sh`
2. Start frontend: `./run_frontend.sh`
3. Open http://localhost:5173
