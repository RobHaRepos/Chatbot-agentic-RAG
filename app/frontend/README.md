# LangGraph Chat Frontend

Modern React-based frontend for the LangGraph Chat application.

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development and optimized builds
- **Tailwind CSS** for styling
- **shadcn/ui** for UI components
- **Zustand** for state management
- **React Router** for navigation
- **Axios** for API calls

## Development

### Prerequisites

- Node.js 20+
- npm

### Install Dependencies

```bash
npm install
```

### Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:5173` (Vite default).

### Build for Production

```bash
npm run build
```

## Docker

### Build Image

```bash
docker build -t langgraph-chat-frontend .
```

### Run Container

```bash
docker run -p 80:80 -e API_URL=http://your-api-url/run langgraph-chat-frontend
```

## Project Structure

```
src/
├── components/
│   ├── chat/              # Chat-related components
│   ├── layout/            # Layout components (Sidebar, etc.)
│   └── ui/                # shadcn/ui components
├── pages/                 # Page components
├── services/              # API services
├── store/                 # Zustand state management
├── types/                 # TypeScript types
├── utils/                 # Utility functions
├── lib/                   # Library utilities
├── App.tsx                # Main app component
└── main.tsx               # Entry point
```

## Features

- **Chat Interface**: Real-time chat with AI assistant
- **Text-to-Speech**: Convert bot responses to speech via [Kokoro TTS](https://github.com/RobHaRepos/TTS_kokoro.git)
- **Vector Store Management**: Create stores, upload documents, manage embeddings
- **Prompt Templates**: Create and edit per-store LLM prompt templates
- **Document Management**: Update content/filenames, delete documents, view chunks
- **Retrieval Testing**: Test search queries with configurable k parameter
- **Dark Mode**: Built-in dark theme

## Configuration

The API URL is configured at runtime via the `API_URL` environment variable in Docker, or via `VITE_API_BASE` in development.
