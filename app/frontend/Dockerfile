FROM nginx:stable-alpine
LABEL org.opencontainers.image.title="langgraph-frontend"
WORKDIR /usr/share/nginx/html

RUN rm -rf ./*

COPY . /usr/share/nginx/html/

RUN mkdir -p /usr/share/nginx/html/.well-known \
    && echo '{"status":"ok"}' > /usr/share/nginx/html/.well-known/health.json

ENV LANGGRAPH_API_URL="http://localhost:8000/run"

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 80
HEALTHCHECK --interval=10s --timeout=3s --retries=3 CMD wget -q -O - http://localhost/.well-known/health.json || exit 1

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
