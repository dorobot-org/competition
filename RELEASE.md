# Release Notes

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
