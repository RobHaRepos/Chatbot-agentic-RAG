#!/bin/sh
set -e

# If LANGGRAPH_API_URL is provided, try to replace placeholder in index.html
HTML_INDEX="/usr/share/nginx/html/index.html"
RUNTIME_JSON="/usr/share/nginx/html/runtime-config.json"

if [ -n "${LANGGRAPH_API_URL}" ]; then
  if grep -q "@@API_URL@@" "$HTML_INDEX" 2>/dev/null; then
    echo "Replacing @@API_URL@@ in index.html with $LANGGRAPH_API_URL"
    sed -i "s|@@API_URL@@|${LANGGRAPH_API_URL}|g" "$HTML_INDEX"
  else
    # write runtime config JSON that app.js may read
    echo "Writing runtime-config.json with apiBase=${LANGGRAPH_API_URL}"
    cat > "$RUNTIME_JSON" <<EOF
{"apiBase":"${LANGGRAPH_API_URL}"}
EOF
  fi
fi

# If no index.html present (unlikely) keep going
exec "$@"
