# Security Fixes - GPU Portal

## 🚨 Critical Security Vulnerabilities Fixed

This document describes the security vulnerabilities that were identified and fixed in the GPU Portal application.

### Summary of Fixes

| Issue | Severity | Status | Files Changed |
|-------|----------|--------|---------------|
| Hardcoded JWT Secret Key | CRITICAL | ✅ Fixed | `backend/auth.py` |
| Hardcoded Admin Password | CRITICAL | ✅ Fixed | `backend/main.py` |
| Hardcoded API Bearer Token | CRITICAL | ✅ Fixed | `backend/control_gpufree.py` |
| Plaintext Password Storage | CRITICAL | ✅ Fixed | `backend/models.py`, `backend/schemas.py`, `backend/main.py` |
| Passwords Logged to Console | HIGH | ✅ Fixed | `backend/main.py` |

---

## 🔧 Changes Made

### 1. JWT Secret Key (CRITICAL)

**Before:**
```python
SECRET_KEY = "your-secret-key-change-in-production-use-env-variable"
```

**After:**
```python
SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY environment variable is required")
```

**Impact:** Prevents authentication bypass attacks. All JWT tokens are now signed with a unique, secure secret key.

### 2. Admin Password (CRITICAL)

**Before:**
```python
default_password = "DongSheng2025#"
admin.hashed_password = get_password_hash(default_password)
admin.plain_password = default_password  # Stored in plaintext!
print(f"Admin password: {default_password}")  # Logged!
```

**After:**
```python
admin_password = os.environ.get("ADMIN_INITIAL_PASSWORD")
if not admin_password:
    logger.warning("ADMIN_INITIAL_PASSWORD not set. Skipping admin creation.")
    return

# Only create admin if it doesn't exist - NEVER reset existing password
if not admin:
    admin.hashed_password = get_password_hash(admin_password)
    logger.info("Admin user created")  # Password NOT logged
```

**Impact:**
- No hardcoded credentials
- Admin password never reset after creation
- No passwords logged to console/files

### 3. API Bearer Token (CRITICAL)

**Before:**
```python
BEARER_TOKEN = "token"

def __init__(self, bearer_token: str = BEARER_TOKEN):
    clean_token = bearer_token or BEARER_TOKEN
```

**After:**
```python
def __init__(self, bearer_token: Optional[str] = None):
    if bearer_token is None:
        bearer_token = os.environ.get("GPUFREE_BEARER_TOKEN")
        if not bearer_token:
            raise RuntimeError("GPUFREE_BEARER_TOKEN environment variable is required")
```

**Impact:** API credentials must be provided via environment variables, preventing accidental exposure in code.

### 4. Plaintext Password Storage (CRITICAL)

**Before:**
```python
# models.py
plain_password = Column(String, nullable=True)  # NEVER DO THIS!

# main.py
new_user.plain_password = user.password  # Stored in plaintext

# schemas.py
plain_password: Optional[str] = None  # Exposed via API
```

**After:**
```python
# models.py - Column removed entirely

# main.py - No plaintext storage
new_user = User(
    hashed_password=get_password_hash(user.password),
    # plain_password removed
)

# schemas.py - Field removed from response
class UserResponse(UserBase):
    # plain_password removed
```

**Impact:**
- No plaintext passwords stored in database
- Compliance with security best practices (GDPR, PCI-DSS)
- Database breach no longer exposes passwords

---

## 🚀 Deployment Guide

### Step 1: Generate Secure Secrets

```bash
# Generate JWT secret key
python3 -c "import secrets; print(secrets.token_urlsafe(64))"

# Copy the output - you'll need it for .env file
```

### Step 2: Create .env File

```bash
# Copy the example file
cp .env.example .env

# Edit with your values
nano .env
```

Required values in `.env`:
```bash
# CRITICAL: Use the secret you generated above
JWT_SECRET_KEY=your-generated-secret-here

# Set a strong admin password (only used for initial setup)
ADMIN_INITIAL_PASSWORD=YourSecurePassword123!

# Get your bearer token from gpufree.cn (browser network tab when logged in)
GPUFREE_BEARER_TOKEN=your-real-bearer-token
```

### Step 3: Migrate Existing Database (if applicable)

If you have an existing database with plaintext passwords:

```bash
# Navigate to backend directory
cd backend

# Run migration script
python3 migrate_remove_plaintext_passwords.py
```

The script will:
- Create a backup of your database
- Remove the `plain_password` column
- Verify the migration succeeded
- Preserve all hashed passwords (users can still log in)

### Step 4: Deploy with Docker Compose

```bash
# Make sure .env file exists in project root
ls -la .env

# Build and start containers
docker-compose down
docker-compose build
docker-compose up -d

# Check logs for errors
docker-compose logs -f backend
```

### Step 5: Verify Deployment

1. **Check Backend Health:**
   ```bash
   curl http://localhost:8000/api/health
   ```

2. **Test Admin Login:**
   - Navigate to http://localhost
   - Login with:
     - Phone: `13800000000`
     - Password: `[your ADMIN_INITIAL_PASSWORD]`

3. **Verify Environment Variables:**
   ```bash
   docker exec gpu-portal-backend env | grep -E "JWT_SECRET_KEY|GPUFREE"
   ```
   Should show `JWT_SECRET_KEY=...` (but value hidden)

### Step 6: Security Hardening (Post-Deployment)

After successful deployment:

1. **Remove ADMIN_INITIAL_PASSWORD** from `.env`:
   ```bash
   # Edit .env and comment out or remove this line:
   # ADMIN_INITIAL_PASSWORD=...
   ```

2. **Change Admin Password** via web interface:
   - Login as admin
   - Go to user management
   - Update admin password

3. **Restart Backend** (to clear password from memory):
   ```bash
   docker-compose restart backend
   ```

4. **Delete Database Backups** (after verification):
   ```bash
   cd data
   ls -la portal.db.backup_*
   # After verifying everything works:
   rm portal.db.backup_*
   ```

---

## 🔒 Security Checklist

Before deploying to production:

- [ ] Generated new `JWT_SECRET_KEY` with cryptographically secure random value
- [ ] Set strong `ADMIN_INITIAL_PASSWORD` (12+ characters, mixed case, numbers, symbols)
- [ ] Obtained real `GPUFREE_BEARER_TOKEN` from gpufree.cn
- [ ] Verified `.env` file is in `.gitignore`
- [ ] Ran database migration script (if upgrading from old version)
- [ ] Tested admin login functionality
- [ ] Verified users can still log in (after migration)
- [ ] Removed `ADMIN_INITIAL_PASSWORD` from `.env` after initial setup
- [ ] Changed admin password via web interface
- [ ] Updated `CORS_ALLOWED_ORIGINS` to production domain (not localhost)
- [ ] Enabled HTTPS in production (use nginx/caddy reverse proxy)
- [ ] Set up regular database backups
- [ ] Deleted old database backup files after verification

---

## 📋 Files Changed

| File | Changes |
|------|---------|
| `backend/auth.py` | Use `JWT_SECRET_KEY` from environment |
| `backend/main.py` | Use `ADMIN_INITIAL_PASSWORD` from environment, remove plaintext password storage, remove password logging |
| `backend/control_gpufree.py` | Use `GPUFREE_BEARER_TOKEN` from environment |
| `backend/models.py` | Remove `plain_password` column |
| `backend/schemas.py` | Remove `plain_password` from `UserResponse` |
| `.env.example` | New file with environment variable template |
| `docker-compose.yml` | Pass environment variables to backend container |
| `backend/migrate_remove_plaintext_passwords.py` | New migration script |
| `.gitignore` | Already includes `.env` (verified) |

---

## 🆘 Troubleshooting

### Error: "JWT_SECRET_KEY environment variable is required"

**Solution:** Make sure `.env` file exists and contains `JWT_SECRET_KEY=...`

```bash
# Check if .env exists
ls -la .env

# Verify docker-compose is loading it
docker-compose config | grep JWT_SECRET_KEY
```

### Error: "GPUFREE_BEARER_TOKEN environment variable is required"

**Solution:** Add your bearer token to `.env` file:

1. Visit https://www.gpufree.cn and log in
2. Open browser Developer Tools (F12)
3. Go to Network tab
4. Refresh page
5. Click on any API request
6. Look for `Authorization: Bearer ...` header
7. Copy the token part and add to `.env`:
   ```bash
   GPUFREE_BEARER_TOKEN=your-actual-token-here
   ```

### Users Can't Log In After Migration

**Solution:** Migration should preserve hashed passwords. Check:

```bash
# Verify migration completed
cd backend
python3 -c "import sqlite3; conn = sqlite3.connect('../data/portal.db'); \
cursor = conn.cursor(); cursor.execute('PRAGMA table_info(users)'); \
print([col[1] for col in cursor.fetchall()])"
```

Should NOT include `plain_password`.

If users still can't log in:
```bash
# Restore from backup
cd data
cp portal.db.backup_YYYYMMDD_HHMMSS portal.db

# Try migration again
cd ../backend
python3 migrate_remove_plaintext_passwords.py
```

### Admin Password Reset on Every Restart

This was the old behavior (now fixed). If it still happens:

1. Check `.env` file - make sure `ADMIN_INITIAL_PASSWORD` is removed or commented out
2. Restart backend: `docker-compose restart backend`
3. Verify logs don't show "Admin user created"

---

## 📚 Additional Resources

- [OWASP Top 10 Security Risks](https://owasp.org/www-project-top-ten/)
- [Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- [Environment Variable Best Practices](https://12factor.net/config)

---

## 📞 Support

If you encounter issues during deployment:

1. Check Docker logs: `docker-compose logs -f backend`
2. Verify environment variables: `docker exec gpu-portal-backend env`
3. Test database connection: `docker exec gpu-portal-backend ls -la /data/`

---

**Last Updated:** 2026-02-24
**Version:** 0.4.2 (Security Hardening Release)
