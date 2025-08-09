# FastAPI Authentication Guide

This guide explains how to use both JWT token and API key authentication in your FastAPI application.

## Table of Contents
1. [Authentication Overview](#authentication-overview)
2. [JWT Token Authentication](#jwt-token-authentication)
3. [API Key Authentication](#api-key-authentication)
4. [Securing Endpoints](#securing-endpoints)
5. [Testing Examples](#testing-examples)
6. [Troubleshooting](#troubleshooting)

## Authentication Overview

Your FastAPI application supports two authentication methods:

1. **JWT Tokens** - For user sessions (48-hour expiry)
2. **API Keys** - For automated systems (permanent until revoked)

Both methods can be used on the same endpoints interchangeably.

## JWT Token Authentication

### 1. Login to Get Token

**Endpoint:** `POST /auth/login`

```bash
curl -X POST "http://localhost:8888/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin&password=password123"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "username": "admin",
    "access_level": "admin"
  }
}
```

### 2. Use Token in Requests

Include the token in the `Authorization` header with `Bearer` prefix:

```bash
curl -X POST "http://localhost:8888/secured-route" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
     -d '{"test": "data"}'
```

## API Key Authentication

### 1. Create API Key (Admin Required)

First, get a JWT token as admin, then create an API key:

```bash
# Step 1: Login as admin
TOKEN=$(curl -s -X POST "http://localhost:8888/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin&password=password123" | jq -r '.access_token')

# Step 2: Create API key
curl -X POST "http://localhost:8888/auth/apikey?client_name=my-service" \
     -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "key": "Ec2_7C-YiD_zMTkjfX-I9PesRIxIA9jK2MDhnAIF84I",
  "client_name": "my-service",
  "access_level": "service",
  "created_by": "admin",
  "created_at": "2025-06-14T02:10:09.262631"
}
```

### 2. Use API Key in Requests

Include the API key in the `X-API-Key` header:

```bash
curl -X POST "http://localhost:8888/secured-route" \
     -H "Content-Type: application/json" \
     -H "X-API-Key: Ec2_7C-YiD_zMTkjfX-I9PesRIxIA9jK2MDhnAIF84I" \
     -d '{"test": "data"}'
```

### 3. List Existing API Keys

```bash
curl -X GET "http://localhost:8888/auth/apikeys" \
     -H "Authorization: Bearer $TOKEN"
```

### 4. Debug API Keys

```bash
curl -X GET "http://localhost:8888/auth/debug/apikeys" \
     -H "Authorization: Bearer $TOKEN"
```

## Securing Endpoints

### Method 1: JWT Only
For user-only endpoints, use `get_current_user`:

```python
from auth.utils import get_current_user

@app.post("/user-only-endpoint")
async def user_endpoint(current_user: dict = Depends(get_current_user)):
    return {"message": "User authenticated", "user": current_user}
```

### Method 2: API Key OR JWT (Recommended)
For endpoints that should accept both authentication methods:

```python
from auth.utils import get_current_user_or_key

@app.post("/flexible-endpoint")
async def flexible_endpoint(current_user: dict = Depends(get_current_user_or_key)):
    return {"message": "Authenticated", "user": current_user}
```

### Method 3: Admin Only
For admin-only endpoints, check the access level:

```python
@app.post("/admin-endpoint")
async def admin_endpoint(current_user: dict = Depends(get_current_user_or_key)):
    if current_user["access_level"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return {"message": "Admin endpoint", "user": current_user}
```

## Testing Examples

### Complete PowerShell Test Script

```powershell
# Test both authentication methods

$baseUrl = "http://localhost:8888"

Write-Host "=== Testing JWT Authentication ===" -ForegroundColor Green

# 1. Login to get token
$loginResponse = Invoke-RestMethod -Uri "$baseUrl/auth/login" `
                                  -Method POST `
                                  -ContentType "application/x-www-form-urlencoded" `
                                  -Body "username=admin&password=password123"

$token = $loginResponse.access_token
Write-Host "Got JWT token: $($token.Substring(0,20))..."

# 2. Test secured endpoint with JWT
$jwtHeaders = @{ 
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

$jwtResponse = Invoke-RestMethod -Uri "$baseUrl/secured-route" `
                                -Method POST `
                                -Headers $jwtHeaders `
                                -Body '{"test": "jwt data"}'

Write-Host "JWT Response: $($jwtResponse | ConvertTo-Json)"

Write-Host "`n=== Testing API Key Authentication ===" -ForegroundColor Green

# 3. Use existing API key (replace with your actual key)
$apiKey = "Ec2_7C-YiD_zMTkjfX-I9PesRIxIA9jK2MDhnAIF84I"

$apiHeaders = @{
    "X-API-Key" = $apiKey
    "Content-Type" = "application/json"
}

$apiResponse = Invoke-RestMethod -Uri "$baseUrl/secured-route" `
                                -Method POST `
                                -Headers $apiHeaders `
                                -Body '{"test": "api key data"}'

Write-Host "API Key Response: $($apiResponse | ConvertTo-Json)"
```

### Complete Bash Test Script

```bash
#!/bin/bash

BASE_URL="http://localhost:8888"

echo "=== Testing JWT Authentication ==="

# 1. Login to get token
TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin&password=password123" | jq -r '.access_token')

echo "Got JWT token: ${TOKEN:0:20}..."

# 2. Test secured endpoint with JWT
echo "Testing with JWT token:"
curl -X POST "$BASE_URL/secured-route" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"test": "jwt data"}'

echo -e "\n\n=== Testing API Key Authentication ==="

# 3. Use existing API key
API_KEY="Ec2_7C-YiD_zMTkjfX-I9PesRIxIA9jK2MDhnAIF84I"

echo "Testing with API key:"
curl -X POST "$BASE_URL/secured-route" \
     -H "Content-Type: application/json" \
     -H "X-API-Key: $API_KEY" \
     -d '{"test": "api key data"}'

echo -e "\n\n=== Creating New API Key ==="

curl -X POST "$BASE_URL/auth/apikey?client_name=test-client" \
     -H "Authorization: Bearer $TOKEN"

echo -e "\n\n=== Listing All API Keys ==="

curl -X GET "$BASE_URL/auth/apikeys" \
     -H "Authorization: Bearer $TOKEN"
```

## Authentication Configuration

### Key Files to Understand

1. **`app/auth/utils.py`** - Core authentication logic
2. **`app/auth/router.py`** - Authentication endpoints
3. **`app/auth/models.py`** - User and API key models
4. **`app/storage/api_keys.json`** - Persistent API key storage

### Environment Variables

Set these in your `docker-compose.yml`:

```yaml
environment:
  - JWT_SECRET_KEY=ea7GZD3mQy3EZYD4YZsFmr/9JwBgZFCaWyznnjhOyow=
  - JWT_ALGORITHM=HS256
  - ACCESS_TOKEN_EXPIRE_MINUTES=2880  # 48 hours
```

## Troubleshooting

### Common Issues

1. **401 Unauthorized**
   - Check if API key exists: `GET /auth/debug/apikeys`
   - Verify header name is exactly `X-API-Key`
   - Ensure JWT token isn't expired

2. **403 Forbidden**
   - User doesn't have required access level
   - Check `current_user["access_level"]` in your endpoint

3. **API Key Not Found**
   - Verify key is in `app/storage/api_keys.json`
   - Check Docker volume mount: `./app/storage:/app/storage`

### Debug Endpoints

- `GET /auth/debug/apikeys` - Show stored API keys
- `GET /auth/test` - Test auth module loading
- `GET /health` - Basic health check

### Default Credentials

- **Username:** `admin`
- **Password:** `password123`
- **Access Level:** `admin`

## Security Best Practices

1. **Change default admin password** in production
2. **Use HTTPS** in production
3. **Rotate API keys** regularly
4. **Monitor authentication logs**
5. **Set appropriate token expiry times**
6. **Use environment variables** for secrets

---

*This guide covers the complete authentication system. Keep it handy for reference when working with secured endpoints!*
