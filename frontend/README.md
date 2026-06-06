# AgentIQ — Vue 3 Frontend

Vue 3 + Vite + Tailwind CSS conversion of the AgentIQ Neural OS frontend.

## Tech Stack
- **Vue 3** (Composition API + `<script setup>`)
- **Vue Router 4** — with auth & admin guards
- **Pinia** — auth store + toast store
- **Tailwind CSS 3** — custom design tokens matching original
- **Material Symbols Outlined** — icon font
- **Web Speech API** — free STT + TTS (no API key needed)

## Project Structure

```
src/
├── assets/main.css          # Global CSS, glass utilities, animations
├── stores/
│   ├── auth.js              # JWT + user state (Pinia)
│   └── toast.js             # Toast notification store
├── composables/
│   └── useApi.js            # Fetch wrapper with auth headers + 401 guard
├── router/index.js          # Routes with auth/admin guards
├── views/
│   ├── LoginView.vue
│   ├── RegisterView.vue
│   ├── WorkspaceView.vue    # Voice (left) + BI platform (right)
│   ├── VoiceView.vue        # Immersive full-screen voice mode
│   ├── AgentsView.vue       # Agent fleet management
│   ├── ProfileView.vue      # User profile + settings tabs
│   └── AdminView.vue        # Admin command center (3 tabs)
└── components/
    ├── layout/AppLayout.vue         # Sidebar + topbar shell
    ├── ui/ToastContainer.vue        # Global toast notifications
    ├── voice/VoiceAgent.vue         # Orb + transcript panel
    ├── platform/
    │   ├── ConfigPanel.vue          # BI prompt input
    │   ├── ExecutionTerminal.vue    # Live log terminal
    │   ├── AgentTimeline.vue        # Pipeline step tracker
    │   └── StatsBar.vue             # Jobs / tokens / cost stats
    ├── agents/
    │   ├── AgentCard.vue            # Agent grid card
    │   └── AgentBuilder.vue         # Slide-out create/edit drawer
    └── admin/
        ├── AdminStats.vue           # Metric cards + SVG bar chart
        ├── UsersTable.vue           # User management + password reset modal
        └── JobsTable.vue            # All jobs + detail modal
```

## Setup

```bash
# 1. Install dependencies
npm install

# 2. Create environment file
cp .env.example .env
# Edit VITE_API_URL to point at your FastAPI backend

# 3. Run dev server
npm run dev

# 4. Build for production
npm run build
```

## Backend API
Expects a FastAPI backend running at `VITE_API_URL` (default `http://localhost:8000`) with these endpoints:

| Method | Path | Auth |
|--------|------|------|
| POST | `/api/v1/auth/register` | Public |
| POST | `/api/v1/auth/login` | Public |
| GET/PUT | `/api/v1/auth/me` | JWT |
| POST | `/api/v1/auth/change-password` | JWT |
| GET/POST | `/api/v1/agents` | JWT |
| PUT/DELETE | `/api/v1/agents/:uuid` | JWT |
| POST | `/api/v1/agents/:uuid/clone` | JWT |
| POST | `/api/v1/voice/chat` | JWT |
| POST | `/api/v1/plan` | JWT |
| GET | `/api/v1/plan/:job_id` | JWT |
| GET | `/api/v1/admin/stats` | Admin |
| GET | `/api/v1/admin/users` | Admin |
| PATCH | `/api/v1/admin/users/:uuid` | Admin |
| POST | `/api/v1/admin/users/:uuid/reset-password` | Admin |
| GET | `/api/v1/admin/jobs` | Admin |

## Voice Agent
Uses the browser's built-in **Web Speech API** — no API key required.
- `SpeechRecognition` for STT
- `SpeechSynthesisUtterance` for TTS
- 12 languages supported
- Transcribed text is sent to `/api/v1/voice/chat` → Gemini 2.5 Flash-Lite responds → spoken aloud

## Auth Flow
1. JWT stored in `localStorage` on login/register
2. All API calls attach `Authorization: Bearer <token>` via `useApi.js`
3. Any `401` response → auto logout + redirect to `/login`
4. Admin routes guarded in both Vue Router and backend
