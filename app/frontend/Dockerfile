FROM nginx:stable-alpine
LABEL org.opencontainers.image.title="langgraph-frontend"
WORKDIR /usr/share/nginx/html

# Remove default nginx content
RUN rm -rf ./*

# Copy frontend static files (when building from the `app/frontend` directory use '.' as context)
COPY . /usr/share/nginx/html/

# tiny health page and ensure .well-known exists
RUN mkdir -p /usr/share/nginx/html/.well-known \
    && echo '{"status":"ok"}' > /usr/share/nginx/html/.well-known/health.json

ENV LANGGRAPH_API_URL="http://localhost:8003/run"

# Add entrypoint that injects runtime config or substitutes placeholder
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 80
HEALTHCHECK --interval=10s --timeout=3s --retries=3 CMD wget -q -O - http://localhost/.well-known/health.json || exit 1

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
