#!/bin/bash
# =============================================================================
# GPU Portal - Environment Setup Script
# =============================================================================
# This script helps you create a secure .env file with properly generated secrets
#
# Usage: ./setup-env.sh

set -e

echo "==========================================="
echo "GPU Portal - Environment Setup"
echo "==========================================="
echo ""

# Check if .env already exists
if [ -f .env ]; then
    echo "⚠ Warning: .env file already exists"
    read -p "Do you want to overwrite it? (yes/no): " overwrite
    if [ "$overwrite" != "yes" ]; then
        echo "✗ Setup cancelled"
        exit 0
    fi
    echo ""
fi

echo "Generating secure secrets..."
echo ""

# Generate JWT secret key
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
echo "✓ Generated JWT_SECRET_KEY"

# Prompt for admin password
while true; do
    echo ""
    echo "Enter initial admin password (12+ characters, mixed case + numbers + symbols):"
    read -s ADMIN_PASS
    echo ""
    echo "Confirm password:"
    read -s ADMIN_PASS_CONFIRM
    echo ""

    if [ "$ADMIN_PASS" != "$ADMIN_PASS_CONFIRM" ]; then
        echo "✗ Passwords don't match. Try again."
        continue
    fi

    if [ ${#ADMIN_PASS} -lt 12 ]; then
        echo "✗ Password too short (minimum 12 characters). Try again."
        continue
    fi

    echo "✓ Admin password set"
    break
done

# Prompt for GPUFree bearer token
echo ""
echo "Enter your GPUFree bearer token:"
echo "(Get it from https://www.gpufree.cn - check Network tab in browser DevTools)"
read GPUFREE_TOKEN

if [ -z "$GPUFREE_TOKEN" ]; then
    echo "⚠ Warning: No bearer token provided"
    echo "  You can add it later by editing .env file"
    GPUFREE_TOKEN="CHANGE_ME"
fi

# Optional: CORS origins
echo ""
echo "Enter CORS allowed origins (press Enter for default: localhost:5173):"
read CORS_ORIGINS

if [ -z "$CORS_ORIGINS" ]; then
    CORS_ORIGINS="http://localhost:5173,http://127.0.0.1:5173"
fi

# Create .env file
echo ""
echo "Creating .env file..."

cat > .env <<EOF
# ============================================
# GPU Portal - Environment Configuration
# ============================================
# Generated: $(date)
# NEVER commit this file to git

# --------------------------------------------
# JWT Configuration (REQUIRED)
# --------------------------------------------
JWT_SECRET_KEY=$JWT_SECRET

# --------------------------------------------
# Admin Configuration (REQUIRED - First Run Only)
# --------------------------------------------
# IMPORTANT: Remove this line after initial setup!
ADMIN_INITIAL_PASSWORD=$ADMIN_PASS

# --------------------------------------------
# GPUFree API Configuration (REQUIRED)
# --------------------------------------------
GPUFREE_BEARER_TOKEN=$GPUFREE_TOKEN

# --------------------------------------------
# Database Configuration (Optional)
# --------------------------------------------
DATABASE_PATH=/data/portal.db

# --------------------------------------------
# CORS Configuration (Optional)
# --------------------------------------------
CORS_ALLOWED_ORIGINS=$CORS_ORIGINS

# --------------------------------------------
# Logging Configuration (Optional)
# --------------------------------------------
LOG_LEVEL=INFO
EOF

echo "✓ .env file created successfully"
echo ""

# Set restrictive permissions
chmod 600 .env
echo "✓ Set restrictive permissions (600) on .env file"
echo ""

# Verify .gitignore
if grep -q "^\.env$" .gitignore 2>/dev/null; then
    echo "✓ .env is in .gitignore"
else
    echo "⚠ Warning: .env is NOT in .gitignore"
    echo "  Adding it now..."
    echo ".env" >> .gitignore
    echo "✓ Added .env to .gitignore"
fi

echo ""
echo "==========================================="
echo "Setup Complete!"
echo "==========================================="
echo ""
echo "Next steps:"
echo "1. Review the .env file: cat .env"
echo "2. If you have an existing database, run migration:"
echo "   cd backend && python3 migrate_remove_plaintext_passwords.py"
echo "3. Start the application:"
echo "   docker-compose up -d"
echo "4. Test admin login:"
echo "   - URL: http://localhost"
echo "   - Phone: 13800000000"
echo "   - Password: [your admin password]"
echo "5. After successful login, REMOVE ADMIN_INITIAL_PASSWORD from .env"
echo "6. Change admin password via web interface"
echo ""
echo "For detailed instructions, see: SECURITY_FIXES.md"
echo "==========================================="
