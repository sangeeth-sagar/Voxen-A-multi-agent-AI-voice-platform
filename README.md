# Voxen

> A multi-agent AI voice platform that lets you create, configure, and orchestrate intelligent voice assistants using your own API keys across any language or provider.

[![Vue](https://img.shields.io/badge/Vue-3.4-4FC08D?logo=vue.js&logoColor=white)](https://vuejs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-async-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Deployed on Vercel](https://img.shields.io/badge/Frontend-Vercel-black?logo=vercel)](https://voxen-a-multi-agent-ai-voice-platfo.vercel.app)
[![Deployed on Render](https://img.shields.io/badge/Backend-Render-46E3B7?logo=render)](https://render.com)

**Live Demo: [voxen-a-multi-agent-ai-voice-platfo.vercel.app](https://voxen-a-multi-agent-ai-voice-platfo.vercel.app/login)**

---


## Architecture

```
+-------------------------------------------------------------------+
|                          Vue 3 Frontend                           |
|   (Vercel)                                                        |
|                                                                     |
|   Login/Register -- Voice Lab -- Agent Builder -- Admin Panel      |
|         |                |              |              |          |
|         +----------------+--------------+--------------+          |
|                            |                                       |
|              REST (fetch)  |  WebSocket (real-time)                |
+----------------------------+---------------------------------------+
                             v
+-------------------------------------------------------------------+
|                       FastAPI Backend                              |
|   (Render)                                                         |
|                                                                     |
|   Auth (JWT + refresh)  ->  Agents CRUD  ->  Webhooks               |
|         |                       |              |                   |
|         v                       v              v                   |
|   PostgreSQL              llm_router.py    tts_router.py            |
|   (users, agents,         (Gemini /         (ElevenLabs / Groq /    |
|    sessions, keys)         OpenAI /          Azure / Deepgram /     |
|                             Claude)           Browser fallback)     |
|                                  |                                  |
|                                  v                                  |
|                          Groq Whisper STT                           |
|                       (multilingual, thread-pooled)                  |
+-------------------------------------------------------------------+
```

Each voice agent is independently configured with its own LLM provider,
TTS provider, and language — all backed by the user's own encrypted
API keys, never shared across agents or users.

---

## Tech Stack

### Frontend
- **Vue 3** (Composition API + `<script setup>`)
- **Vue Router 4** — auth guards, role-based routing (user / superadmin)
- **Pinia** — auth store + toast store
- **Tailwind CSS 3** — custom design tokens, glassmorphism utilities
- **Material Symbols Outlined** — icon font
- **Web Speech API** — browser-native STT + TTS fallback
- **WebSocket** — real-time token streaming + audio playback

### Backend
- **FastAPI** — async Python REST + WebSocket server
- **SQLAlchemy** + **PostgreSQL** — relational data + Alembic migrations
- **Passlib / bcrypt** — password hashing
- **Cryptography (Fernet)** — API key encryption at rest
- **LangChain** — multi-provider LLM abstraction
- **Groq Whisper** — multilingual speech-to-text
- **uvloop + httptools** — high-performance async event loop

### AI Providers Supported
| Type | Providers |
|------|-----------|
| LLM | Google Gemini, OpenAI, Anthropic Claude |
| TTS | ElevenLabs, Groq, Azure TTS, Deepgram, Browser |
| STT | Groq Whisper, ElevenLabs Scribe, Deepgram |

---

## Project Structure

```
voxen/
+-- backend/
|   +-- main.py                        # FastAPI app entrypoint
|   +-- alembic/                       # Database migrations
|   +-- requirements.txt
|   +-- .env
|   +-- app/
|       +-- config.py                  # Pydantic settings
|       +-- database.py                # SQLAlchemy engine + session
|       +-- llm_router.py              # Multi-provider LLM (Gemini/OpenAI/Claude)
|       +-- tts_router.py              # Multi-provider TTS (ElevenLabs/Groq/Azure)
|       +-- auth/
|       |   +-- security.py            # JWT + bcrypt password utils
|       +-- models/
|       |   +-- user.py                # User + superadmin flag
|       |   +-- agent_config.py        # Voice agent configuration
|       |   +-- user_api_keys.py       # Encrypted per-user API keys
|       |   +-- agent_key_assignments.py  # Agent <-> provider key mapping
|       |   +-- conversation_session.py
|       |   +-- webhook_endpoint.py    # External webhook integrations
|       +-- routes/
|       |   +-- auth.py                # Register, login, me, change-password
|       |   +-- agents.py              # CRUD + clone agents
|       |   +-- voice_agent.py         # HTTP voice chat + sessions
|       |   +-- ws_voice.py            # WebSocket real-time streaming
|       |   +-- api_keys.py            # User API key management
|       |   +-- webhooks.py            # External suite webhook endpoints
|       |   +-- admin.py               # Superadmin-only user + agent management
|       +-- utils/
|           +-- encryption.py          # Fernet encrypt/decrypt for API keys
|
+-- frontend/
    +-- index.html
    +-- vite.config.js
    +-- .env                           # VITE_API_URL, VITE_WS_URL
    +-- src/
        +-- assets/main.css            # Global CSS, glass utilities, animations
        +-- stores/
        |   +-- auth.js                # JWT + user state (Pinia)
        |   +-- toast.js               # Toast notification store
        +-- composables/
        |   +-- useApi.js              # Fetch wrapper with auth headers + 401 guard
        |   +-- useLanguage.js         # Language state (en/hi/mr/ml)
        |   +-- useTTS.js              # Multi-provider TTS with voice fallback chain
        |   +-- useApiKeys.js          # CRUD for user-saved API keys
        |   +-- useTheme.js            # Light/dark theme, isolated for auth pages
        |   +-- useSessionTimer.js     # 10-minute idle timeout + token refresh
        |   +-- useNotifications.js    # Session-scoped notification panel
        |   +-- useWakeWord.js         # SpeechRecognition + wake word detection
        +-- router/index.js            # Routes with auth + superadmin guards
        +-- layouts/
        |   +-- UserLayout.vue         # Minimal 3-tab sidebar (Voice, Agents, Profile)
        |   +-- AdminLayout.vue        # Separate admin shell
        +-- views/
        |   +-- LoginView.vue
        |   +-- RegisterView.vue
        |   +-- VoiceView.vue          # Immersive voice mode + WebSocket streaming
        |   +-- AgentsView.vue         # Agent fleet — create, edit, webhook
        |   +-- ProfileView.vue        # Profile + API key management
        |   +-- admin/
        |       +-- DashboardView.vue  # Platform stats
        |       +-- UsersView.vue      # User management table
        |       +-- AgentsView.vue     # All agents across all users
        +-- components/
            +-- layout/AppLayout.vue         # Sidebar + topbar shell
            +-- ui/ToastContainer.vue        # Global toast notifications
            +-- ui/NotificationPanel.vue     # Slide-out notification feed
            +-- voice/VoiceAgent.vue         # Orb + transcript + streaming panel
            +-- LanguageSelector.vue         # en/hi/mr/ml picker with fallback badges
            +-- platform/
            |   +-- ConfigPanel.vue          # BI prompt input
            |   +-- ExecutionTerminal.vue    # Live log terminal
            |   +-- AgentTimeline.vue        # Pipeline step tracker
            |   +-- StatsBar.vue             # Jobs / tokens / cost stats
            +-- agents/
            |   +-- AgentCard.vue            # Agent grid card
            |   +-- AgentBuilder.vue         # Slide-out create/edit drawer
            +-- admin/
                +-- AdminStats.vue           # Metric cards + SVG bar chart
                +-- UsersTable.vue           # User management + password reset modal
                +-- JobsTable.vue            # All jobs + detail modal
```

---

## Setup

### Prerequisites
- Python 3.11
- Node.js 18+
- PostgreSQL 14+

### Backend

```bash
cd backend

# 1. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Fill in: DATABASE_URL, GOOGLE_API_KEY, GROQ_API_KEY, ENCRYPTION_KEY

# Generate ENCRYPTION_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 4. Run database migrations
python -m alembic upgrade head

# 5. Create superadmin account (first time only)
python scripts/create_superadmin.py

# 6. Start server
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Configure environment
cp .env.example .env
# VITE_API_URL=http://localhost:8000
# VITE_WS_URL=ws://localhost:8000

# 3. Run dev server
npm run dev

# 4. Build for production
npm run build
```

---

## Deployment

The live demo runs on **Render** (backend) + **Vercel** (frontend).

### Backend on Render

1. Create a new **Web Service** on Render, connected to this repo's
   `backend/` directory as the root.
2. **Build command:**
   ```
   pip install -r requirements.txt
   ```
3. **Start command:**
   ```
   uvicorn main:app --host 0.0.0.0 --port $PORT --loop uvloop --http httptools
   ```
4. Add a **PostgreSQL** instance on Render (or connect an external one)
   and set `DATABASE_URL` to its connection string.
5. Set all required environment variables (see Environment Variables
   below) in the Render dashboard.
6. After the first deploy, run migrations via the Render Shell:
   ```bash
   python -m alembic upgrade head
   python scripts/create_superadmin.py
   ```
7. Render's free tier spins down on inactivity — the first request
   after idle may take 30-60s to respond while the instance wakes up.

### Frontend on Vercel

1. Import this repo into Vercel, set the **root directory** to `frontend/`.
2. **Framework preset:** Vite
3. **Build command:** `npm run build`
4. **Output directory:** `dist`
5. Set environment variables in the Vercel dashboard:
   ```
   VITE_API_URL=https://your-backend.onrender.com
   VITE_WS_URL=wss://your-backend.onrender.com
   ```
6. Deploy — Vercel auto-builds on every push to `main`.

### Production server flags (reference)

If self-hosting the backend outside of Render's default start command:
```bash
uvicorn main:app --loop uvloop --http httptools --workers 2
```

---

## Environment Variables

### Backend `.env`
```env
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/voxen
GOOGLE_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key
ENCRYPTION_KEY=your_fernet_key
SECRET_KEY=your_jwt_secret
DEFAULT_LLM_PROVIDER=gemini
DEFAULT_TTS_PROVIDER=elevenlabs
DEFAULT_STT_PROVIDER=groq
ADMIN_EMAIL=admin@voxen.ai
```

### Frontend `.env`
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

---

## API Reference

### Public
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login, returns JWT + refresh token |
| POST | `/api/v1/auth/refresh` | Exchange refresh token for new access token |

### User (JWT required)
| Method | Path | Description |
|--------|------|-------------|
| GET/PUT | `/api/v1/auth/me` | Get / update profile |
| POST | `/api/v1/auth/change-password` | Change password |
| POST | `/api/v1/auth/logout` | Invalidate refresh token + clear session notifications |
| GET/POST | `/api/v1/agents` | List / create agents |
| PUT/DELETE | `/api/v1/agents/:uuid` | Update / delete agent |
| POST | `/api/v1/agents/:uuid/clone` | Clone an agent |
| POST | `/api/v1/voice/chat` | HTTP voice chat |
| GET | `/api/v1/voice-agent/sessions` | Conversation sessions |
| GET/POST | `/api/v1/keys` | List / add API keys |
| DELETE | `/api/v1/keys/:id` | Remove API key |
| GET | `/api/v1/keys/providers` | Supported providers list |
| POST | `/api/v1/webhook/agent/:id/generate` | Generate webhook URL |
| GET | `/api/v1/notifications` | Session-scoped notification feed |
| POST | `/api/v1/notifications/mark-seen` | Clear the unread notification badge |
| WS | `/ws/voice/:agent_uuid` | Real-time streaming |

### Admin (Superadmin JWT required)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/admin/users` | All users |
| PATCH | `/api/v1/admin/users/:id/toggle` | Suspend / reactivate user |
| PATCH | `/api/v1/admin/users/:id/promote` | Promote to superadmin |
| POST | `/api/v1/admin/users/:id/reset-password` | Reset user password |
| GET | `/api/v1/admin/agents` | All agents across all users |
| DELETE | `/api/v1/admin/agents/:id` | Delete any agent |
| GET | `/api/v1/admin/stats` | Platform-wide stats |

### External Webhook
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/webhook/agent/:token` | Trigger agent from external suite |

**Webhook payload:**
```json
{
  "text": "user message",
  "session_id": "optional-session-id",
  "language": "en",
  "metadata": {}
}
```

---

## Voice Agent

### Real-time Streaming (WebSocket)
Connect to `ws://localhost:8000/ws/voice/{agent_uuid}?token={jwt}` and exchange JSON messages:

| Direction | Type | Description |
|-----------|------|-------------|
| -> Send | `user_text` | User transcript + language |
| <- Receive | `agent_token` | LLM token stream (word by word) |
| <- Receive | `agent_response_complete` | Full response text |
| <- Receive | `tts_audio` | Base64 MP3 audio chunk |
| -> Send | `interrupt` | Stop agent mid-speech |
| <-> Both | `ping` / `pong` | Keep-alive |

The WebSocket connection is rejected with close code `4003` if the
target agent has been deactivated, and `4004` if the agent doesn't
exist — both the WebSocket route and the equivalent HTTP voice route
enforce the agent's active status consistently.

### Languages Supported
| Language | STT | TTS |
|----------|-----|-----|
| English | `en-GB` | Native |
| Hindi | `hi-IN` | Native |
| Marathi | `mr-IN` | Fallback to hi-IN |
| Malayalam | `ml-IN` | Fallback to hi-IN |

### TTS Fallback Chain
If the selected language voice is unavailable on the OS/browser:
```
ml-IN -> hi-IN -> en-IN -> en-US
mr-IN -> hi-IN -> en-IN -> en-US
```

---

## Auth & Session Security

1. JWT access token (10-minute expiry) + refresh token stored in `localStorage`
2. All API calls attach `Authorization: Bearer <token>` via `useApi.js`
3. Any `401` response triggers auto logout + redirect to `/login`
4. **Idle timeout:** if there is no user activity (click, keypress,
   scroll, touch) for 10 minutes, the session ends automatically and
   the access token is not refreshed, even if the refresh token is
   still technically valid
5. Refresh tokens are rotated on every use and stored server-side
   only as a SHA-256 hash, never in plaintext
6. After login, superadmins are redirected to `/admin`, regular users to `/`
7. Admin routes are guarded in both Vue Router (`requiresSuperadmin`) and backend (`require_superadmin` dependency)
8. Login/Register pages use an isolated theme system — switching
   light/dark on the auth pages never affects the rest of the app,
   and vice versa

---

## Notifications

Voxen includes a lightweight, **session-scoped** notification system,
intentionally in-memory rather than persisted to the database, since
these are ephemeral session feedback rather than a permanent audit log.

Notifications are generated for:
- Voice session completion (success or failure)
- Agent creation, updates, and webhook activation/deactivation
- Admin actions affecting your account (suspension, password reset, role change)

All notifications for a user are cleared automatically when the
session ends (logout or idle timeout).

---

## Per-Agent API Keys

Each voice agent can use a different LLM and voice provider with its own API key:

1. Go to **Profile -> API Keys** and add your keys for any provider
2. When creating an agent, select the LLM provider + key and TTS provider + key from your saved keys
3. Keys are encrypted at rest using Fernet symmetric encryption
4. Key previews (last 4 chars) are shown in the UI — full keys are never returned by the API

---

## External Integration (Webhook)

Connect Voxen agents to any external platform, automation suite, or CRM:

1. Open an agent -> click **Generate Webhook URL**
2. Copy the URL: `https://your-domain/api/v1/webhook/agent/{token}`
3. POST from your external tool with the payload above
4. Voxen processes the message and POSTs the response back to your `callback_url`

---

## Performance Notes

- Uses `uvloop` + `httptools` for 20-50% faster async throughput
- Groq Whisper STT runs in a thread pool via `asyncio.to_thread` to avoid blocking the event loop
- Embedding models (sentence-transformers) are loaded once at startup as module-level singletons
- ChromaDB client is cached, not re-instantiated per request
- LLM retries are capped at 2 with a 10s timeout to prevent CPU-burning retry loops
- DB connection pooling: `pool_size=5`, `max_overflow=10`, `pool_recycle=300`
- Frontend theme is applied via a synchronous inline script before Vue
  mounts, eliminating flash-of-wrong-theme on initial page load
- Icon font requests only the specific weight/fill instances actually
  used, rather than the full variable axis range

---

## Known Limitations

- Marathi and Malayalam currently have no native TTS voice and fall
  back to Hindi pronunciation — accurate native synthesis for these
  languages depends on provider support improving
- The in-memory notification store is per-process; in a
  horizontally-scaled multi-instance deployment, notifications would
  need to move to Redis to stay consistent across instances (not
  required at current scale)
- Render's free tier cold-starts after inactivity, adding latency to
  the first request of a new session

---

## License

MIT — see LICENSE for details.
