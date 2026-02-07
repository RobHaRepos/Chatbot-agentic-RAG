# Multi-stage build for production
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies (--ignore-scripts prevents execution of arbitrary scripts from packages)
RUN npm ci --ignore-scripts

# Copy source code explicitly (only files needed for the build)
COPY src/ ./src/
COPY index.html tsconfig.json tsconfig.node.json vite.config.ts ./
COPY tailwind.config.js postcss.config.js components.json ./

# Build the application
RUN npm run build

# Production stage with nginx
FROM nginx:1.29.5-alpine3.23

# Set ownership for nginx user (nginx user already exists in nginx:alpine image)
RUN chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid

# Copy built files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy and set up docker entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh && \
    chown -R nginx:nginx /usr/share/nginx/html

# Switch to non-root user
USER nginx

EXPOSE 80

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
