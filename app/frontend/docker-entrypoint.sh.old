#!/bin/sh
set -e

# Replace @@API_URL@@ placeholder with actual API_URL environment variable
# This allows runtime configuration of the API URL
if [ -n "$API_URL" ]; then
  echo "Configuring API URL to: $API_URL"
  find /usr/share/nginx/html -type f -name "*.html" -exec sed -i "s|@@API_URL@@|$API_URL|g" {} \;
else
  echo "No API_URL set, using default"
  find /usr/share/nginx/html -type f -name "*.html" -exec sed -i "s|@@API_URL@@|/run|g" {} \;
fi

# Execute the main container command
exec "$@"
