# Haidian Robot Competition Portal

![Haidian Robot Competition](haidian.jpg)

## Overview

**Haidian Robot Competition Portal** is a secure web-based platform for managing competition participants and providing GPU computing resources for robot programming competitions. This system enables administrators to register users, assign GPU instances, and provide participants with access to cloud-based development environments.

## Features

### 🏆 Competition Management
- **User Registration**: Administrators can register competition participants with unique credentials
- **Multi-Admin Support**: Each admin can manage up to 128 users independently
- **Participant Portal**: Clean, user-friendly interface for competition participants

### 💻 GPU Resource Management
- **GPUFree Integration**: Direct integration with GPUFree cloud GPU platform
- **Instance Assignment**: Assign dedicated GPU instances to individual participants
- **One-Click Control**: Start/stop GPU instances with a single button click
- **Resource Monitoring**: Track instance status and usage in real-time

### 🔐 Security Features (v0.4.2)
- **Environment-Based Configuration**: All sensitive credentials managed via environment variables
- **Secure Password Storage**: Industry-standard bcrypt password hashing
- **JWT Authentication**: Token-based authentication with configurable expiration
- **Role-Based Access Control**: Admin and participant role separation
- **No Hardcoded Secrets**: Zero credentials in source code

### ⚡ Auto-Management
- **Inactivity Detection**: Auto-stop instances after 180 minutes of inactivity
- **Heartbeat Monitoring**: Real-time activity tracking via frontend heartbeat
- **Daily Shutdown**: Automatic shutdown of all instances at 2 AM Beijing time
- **Resource Optimization**: Prevent unnecessary GPU usage and costs

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for migration scripts)
- GPUFree account and API bearer token

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/dorobot-org/competition.git
   cd competition
   ```

2. **Configure environment variables**
   ```bash
   # Use interactive setup script (recommended)
   ./setup-env.sh

   # Or manually create .env from template
   cp .env.example .env
   # Edit .env and set required values
   ```

3. **Deploy with Docker**
   ```bash
   docker-compose up -d
   ```

4. **Access the portal**
   - **Frontend**: http://localhost
   - **Backend API**: http://localhost:8000
   - **Admin Login**: Phone `13800000000` + your admin password

### First-Time Setup

After deployment:

1. Login as admin with the credentials you set in `.env`
2. Add GPU instances from the admin panel
3. Create participant accounts and assign GPU instances
4. Remove `ADMIN_INITIAL_PASSWORD` from `.env` file
5. Restart backend: `docker-compose restart backend`

## User Roles

### 👨‍💼 Administrator
- Register competition participants
- Assign GPU instances to users
- Manage GPU instance inventory
- Monitor participant activity
- View system statistics

### 👨‍🎓 Participant
- Login with phone number and password
- Start/stop assigned GPU instance
- Access cloud development environment
- Automatic session management
- Inactivity auto-shutdown protection

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Frontend (Vue.js)                 │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │ Login Page   │  │ Admin Panel  │  │  Portal   │ │
│  └──────────────┘  └──────────────┘  └───────────┘ │
└─────────────────────────────────────────────────────┘
                           │
                           │ HTTP/REST API
                           ▼
┌─────────────────────────────────────────────────────┐
│                Backend (FastAPI)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │ JWT Auth     │  │ User Mgmt    │  │ GPUFree   │ │
│  └──────────────┘  └──────────────┘  └───────────┘ │
└─────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   SQLite DB  │  │ GPUFree API  │  │ Background   │
│   (Users)    │  │ (GPU Ctrl)   │  │ Tasks        │
└──────────────┘  └──────────────┘  └──────────────┘
```

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user info

### User Management (Admin)
- `GET /api/users` - List users
- `POST /api/users` - Create user
- `PUT /api/users/{id}` - Update user
- `DELETE /api/users/{id}` - Delete user

### GPU Instance Management (Admin)
- `GET /api/instances` - List GPU instances
- `POST /api/instances` - Add GPU instance
- `PUT /api/instances/{id}` - Update instance
- `DELETE /api/instances/{id}` - Remove instance

### Portal Actions (Participant)
- `POST /api/portal/action` - Start/stop GPU instance
- `POST /api/portal/heartbeat` - Send activity heartbeat
- `GET /api/portal/query-instance` - Query instance status
- `GET /api/portal/target-url` - Get instance URL

## Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - SQL toolkit and ORM
- **SQLite** - Lightweight database
- **JWT** - JSON Web Token authentication
- **Bcrypt** - Password hashing
- **Python 3.11** - Core language

### Frontend
- **Vue.js 3** - Progressive JavaScript framework
- **Vite** - Next-generation frontend tooling
- **Pinia** - Vue state management
- **Vue Router** - Official router
- **Axios** - HTTP client

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **Nginx** - Web server and reverse proxy

## Security

This platform implements industry-standard security practices:

- ✅ Environment-based configuration (no hardcoded secrets)
- ✅ Bcrypt password hashing
- ✅ JWT token authentication
- ✅ CORS protection
- ✅ SQL injection prevention (via ORM)
- ✅ Input validation
- ✅ Secure session management

**See [SECURITY_FIXES.md](SECURITY_FIXES.md) for detailed security documentation.**

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `JWT_SECRET_KEY` | Yes | Secret key for JWT token signing |
| `ADMIN_INITIAL_PASSWORD` | Yes* | Initial admin password (first run only) |
| `GPUFREE_BEARER_TOKEN` | Yes | GPUFree API authentication token |
| `DATABASE_PATH` | No | SQLite database file path (default: `/data/portal.db`) |
| `CORS_ALLOWED_ORIGINS` | No | CORS allowed origins (default: localhost) |
| `LOG_LEVEL` | No | Logging level (default: `INFO`) |

*Remove after first successful login

### System Limits

- **Max users per admin**: 128
- **Inactivity timeout**: 180 minutes (3 hours)
- **Heartbeat interval**: 30 seconds
- **Daily shutdown time**: 2:00 AM Beijing time

## Deployment

### Production Deployment

1. **Use HTTPS** - Deploy behind nginx/Caddy with SSL certificate
2. **Set production CORS** - Update `CORS_ALLOWED_ORIGINS` to your domain
3. **Secure secrets** - Use strong, randomly generated secrets
4. **Regular backups** - Backup `/data/portal.db` regularly
5. **Monitor logs** - Check Docker logs for errors
6. **Update regularly** - Keep dependencies up to date

### Docker Compose Production

```yaml
services:
  backend:
    env_file: .env
    restart: always
    volumes:
      - ./data:/data

  frontend:
    restart: always
    depends_on:
      - backend
```

## Migration

If upgrading from a version before v0.4.2:

```bash
# 1. Stop containers
docker-compose down

# 2. Run migration script
cd backend
python3 migrate_remove_plaintext_passwords.py

# 3. Configure environment
cd ..
./setup-env.sh

# 4. Restart
docker-compose up -d
```

## Troubleshooting

### Common Issues

**Backend won't start**
- Check `.env` file exists and contains all required variables
- Verify `JWT_SECRET_KEY` is set
- Check Docker logs: `docker-compose logs backend`

**Can't login**
- Verify admin password in `.env` matches login attempt
- Check user exists in database: `sqlite3 data/portal.db "SELECT * FROM users;"`
- Review backend logs for authentication errors

**GPU instance won't start/stop**
- Verify `GPUFREE_BEARER_TOKEN` is valid
- Check GPUFree account has active instances
- Ensure instance UUID is correct

**Port conflicts**
- Check if port 80 or 8000 are already in use
- Modify `docker-compose.yml` to use different ports

## Contributing

We welcome contributions! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Version History

See [RELEASE.md](RELEASE.md) for detailed release notes.

### Latest Releases

- **v0.4.2** (2026-02-24) - Security hardening release
- **v0.4.1** (2025-12-03) - Daily shutdown timezone fix
- **v0.4.0** (2025-12-03) - User limits, timeouts, daily shutdown
- **v0.3.0** (2025-12-03) - Docker support
- **v0.2.1** (2025-12-03) - Heartbeat-based inactivity detection
- **v0.2.0** (2025-12-03) - GPU instance management
- **v0.1.1** (2024-12-03) - Initial release

## License

[License information to be added]

## Support

For issues and questions:
- Create an issue on GitHub
- Check [SECURITY_FIXES.md](SECURITY_FIXES.md) for deployment help
- Review [RELEASE.md](RELEASE.md) for version-specific information

## Acknowledgments

- Built for Haidian Robot Competition
- Powered by GPUFree cloud GPU platform
- Developed with FastAPI and Vue.js

---

**🤖 Built for Robot Competitions | 🔐 Security-First | ⚡ Cloud-Powered**
