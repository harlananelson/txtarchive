#!/bin/bash

# Load the Sage email and password from the environment variables
EMAIL=$SAGE_EMAIL
PASSWORD=$SAGE_PASSWORD

# Authenticate and get the access token
RAW_RESPONSE=$(curl -s -X POST https://api.asksage.ai/user/get-token \
-H "Content-Type: application/json" \
-d "{
  \"email\": \"$EMAIL\",
  \"password\": \"$PASSWORD\"
}")

# Check if the response is valid JSON
if ! echo "$RAW_RESPONSE" | jq empty 2>/dev/null; then
  echo "Error: API response is not valid JSON."
  echo "Raw response: $RAW_RESPONSE"
  exit 1
fi

# Extract the access token using jq
ACCESS_TOKEN=$(echo "$RAW_RESPONSE" | jq -r '.response.access_token')

# Check if the access token was retrieved successfully
if [ -z "$ACCESS_TOKEN" ] || [ "$ACCESS_TOKEN" == "null" ]; then
  echo "Failed to retrieve access token. Check your credentials."
  exit 1
fi

# Export the access token to the parent shell
echo "Access token retrieved successfully: $ACCESS_TOKEN"
export ACCESS_TOKEN