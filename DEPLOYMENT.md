# Frontend Deployment Guide

## Quick Start

```powershell
# Build and deploy all services
docker-compose up --build -d

# Access frontend at http://localhost:8003
```

## Development Mode

```powershell
cd app/frontend
npm install
npm run dev  # Runs on http://localhost:3000
```

## Architecture

**Tech Stack:** React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui + Zustand

**Structure:**
```
app/frontend/src/
├── components/      # UI components (chat, layout, shared)
├── pages/          # Routes (Chat, Vector Stores, Settings)
├── services/       # API layer (chat, TTS, logger)
├── store/          # State management (Zustand)
├── types/          # TypeScript definitions
└── utils/          # Helper functions
```

## Docker Configuration

**docker-compose.yml:**
```yaml
frontend:
  build:
    context: ./app/frontend
  ports:
    - "8003:80"
  environment:
    API_URL: "http://localhost:8000/run"
```

**Multi-stage build:** Node.js (build) → Nginx (serve)

## API Endpoints

- **Chat:** `POST ${API_URL}` - Send message, get response
- **TTS:** `POST ${API_URL.replace('/run', '/tts')}` - Generate speech

## Useful Commands

```powershell
# Rebuild frontend only
docker-compose up -d --build frontend

# View logs
docker-compose logs -f frontend

# Stop services
docker-compose down

# Check service status
docker-compose ps
```

## Environment Configuration

**Development (.env):**
```
VITE_API_BASE=http://localhost:8000/run
```

**Production (docker-compose.yml):**
```yaml
environment:
  API_URL: "https://your-api.com/run"
```

## Features

✅ **Current:**
- Chat interface with message history
- Text-to-speech functionality
- Loading states and error handling
- Multi-page navigation (Chat, Vector Stores, Settings)
- Responsive dark theme

🔜 **Planned:**
- Vector store management (UI ready, needs backend API)
- Settings configuration
- Message persistence

## Troubleshooting

**Frontend not connecting:**
```powershell
# Check API URL in container
docker-compose exec frontend cat /usr/share/nginx/html/index.html | Select-String "api-base"

# Verify backend is running
curl http://localhost:8000/health
```

**Build fails:**
```powershell
# Clear cache and rebuild
docker-compose build --no-cache frontend
```

**TypeScript errors in VS Code:**
- Reload window: `Ctrl+Shift+P` → "Reload Window"
- Or restart TS server: `Ctrl+Shift+P` → "TypeScript: Restart TS Server"

## Project Highlights

- **Type-safe:** Full TypeScript coverage
- **Component-based:** Reusable, testable architecture
- **State management:** Centralized with Zustand
- **Production-ready:** Optimized builds, gzip, caching
- **Scalable:** Easy to add features/pages

## Next Steps

1. Deploy: `docker-compose up --build -d`
2. Access: http://localhost:8003
3. Test chat functionality
4. Implement vector store backend APIs when ready

---

**Old vanilla JS frontend preserved in `app/frontend/static/` for reference.**
