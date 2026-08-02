#!/bin/bash

# Configuration
BASE_URL="http://localhost:8000"

echo "=== API Endpoint Tests ==="

# 1. Test root endpoint
echo "--- Testing GET / ---"
curl -s -X GET "$BASE_URL/"
echo -e "\n"

# 2. Test register endpoint
echo "--- Testing POST /auth/register ---"
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/register" \
     -H "Content-Type: application/json" \
     -d '{
       "username": "testuser",
       "email": "test@example.com",
       "password": "securepassword123"
     }')
echo "Response: $REGISTER_RESPONSE"
echo -e "\n"

# 3. Test login endpoint
echo "--- Testing POST /auth/login ---"
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "test@example.com",
       "password": "securepassword123"
     }')
echo "Response: $LOGIN_RESPONSE"
echo -e "\n"

# 4. Test logout endpoint (using a dummy token if login failed, or extracting it)
# For simplicity in this script, we'll try to extract the token
REFRESH_TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"refresh_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$REFRESH_TOKEN" ]; then
    echo "Skipping logout test: Could not extract refresh_token from login response."
else
    echo "--- Testing POST /auth/logout ---"
    curl -s -X POST "$BASE_URL/auth/logout" \
         -H "Content-Type: application/json" \
         -d "{\"refresh_token\": \"$REFRESH_TOKEN\"}"
    echo -e "\n"
fi
