# Voxen

> A multi-agent AI voice platform that lets you create, configure, and orchestrate intelligent voice assistants using your own API keys across any language or provider.

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
├── backend/
│   ├── main.py                        # FastAPI app entrypoint
│   ├── alembic/                       # Database migrations
│   ├── requirements.txt
│   ├── .env
│   └── app/
│       ├── config.py                  # Pydantic settings
│       ├── database.py                # SQLAlchemy engine + session
│       ├── llm_router.py              # Multi-provider LLM (Gemini/OpenAI/Claude)
│       ├── tts_router.py              # Multi-provider TTS (ElevenLabs/Groq/Azure)
│       ├── auth/
│       │   └── security.py            # JWT + bcrypt password utils
│       ├── models/
│       │   ├── user.py                # User + superadmin flag
│       │   ├── agent_config.py        # Voice agent configuration
│       │   ├── user_api_keys.py       # Encrypted per-user API keys
│       │   ├── agent_key_assignments.py  # Agent ↔ provider key mapping
│       │   ├── conversation_session.py
│       │   └── webhook_endpoint.py    # External webhook integrations
│       ├── routes/
│       │   ├── auth.py                # Register, login, me, change-password
│       │   ├── agents.py              # CRUD + clone agents
│       │   ├── voice_agent.py         # HTTP voice chat + sessions
│       │   ├── ws_voice.py            # WebSocket real-time streaming
│       │   ├── api_keys.py            # User API key management
│       │   ├── webhooks.py            # External suite webhook endpoints
│       │   └── admin.py               # Superadmin-only user + agent management
│       └── utils/
│           └── encryption.py          # Fernet encrypt/decrypt for API keys
│
└── frontend/
    ├── index.html
    ├── vite.config.js
    ├── .env                           # VITE_API_URL, VITE_WS_URL
    └── src/
        ├── assets/main.css            # Global CSS, glass utilities, animations
        ├── stores/
        │   ├── auth.js                # JWT + user state (Pinia)
        │   └── toast.js               # Toast notification store
        ├── composables/
        │   ├── useApi.js              # Fetch wrapper with auth headers + 401 guard
        │   ├── useLanguage.js         # Language state (en/hi/mr/ml)
        │   ├── useTTS.js              # Multi-provider TTS with voice fallback chain
        │   ├── useApiKeys.js          # CRUD for user-saved API keys
        │   └── useWakeWord.js         # SpeechRecognition + wake word detection
        ├── router/index.js            # Routes with auth + superadmin guards
        ├── layouts/
        │   ├── UserLayout.vue         # Minimal 3-tab sidebar (Voice, Agents, Profile)
        │   └── AdminLayout.vue        # Separate admin shell
        ├── views/
        │   ├── LoginView.vue
        │   ├── RegisterView.vue
        │   ├── VoiceView.vue          # Immersive voice mode + WebSocket streaming
        │   ├── AgentsView.vue         # Agent fleet — create, edit, webhook
        │   ├── ProfileView.vue        # Profile + API key management
        │   └── admin/
        │       ├── DashboardView.vue  # Platform stats
        │       ├── UsersView.vue      # User management table
        │       └── AgentsView.vue     # All agents across all users
        └── components/
            ├── layout/AppLayout.vue         # Sidebar + topbar shell
            ├── ui/ToastContainer.vue        # Global toast notifications
            ├── voice/VoiceAgent.vue         # Orb + transcript + streaming panel
            ├── LanguageSelector.vue         # en/hi/mr/ml picker with fallback badges
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
# Production:
uvicorn main:app --loop uvloop --http httptools --workers 2
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
| POST | `/api/v1/auth/login` | Login, returns JWT |

### User (JWT required)
| Method | Path | Description |
|--------|------|-------------|
| GET/PUT | `/api/v1/auth/me` | Get / update profile |
| POST | `/api/v1/auth/change-password` | Change password |
| GET/POST | `/api/v1/agents` | List / create agents |
| PUT/DELETE | `/api/v1/agents/:uuid` | Update / delete agent |
| POST | `/api/v1/agents/:uuid/clone` | Clone an agent |
| POST | `/api/v1/voice/chat` | HTTP voice chat |
| GET | `/api/v1/voice-agent/sessions` | Conversation sessions |
| GET/POST | `/api/v1/keys` | List / add API keys |
| DELETE | `/api/v1/keys/:id` | Remove API key |
| GET | `/api/v1/keys/providers` | Supported providers list |
| POST | `/api/v1/webhook/agent/:id/generate` | Generate webhook URL |
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
| → Send | `user_text` | User transcript + language |
| ← Receive | `agent_token` | LLM token stream (word by word) |
| ← Receive | `agent_response_complete` | Full response text |
| ← Receive | `tts_audio` | Base64 MP3 audio chunk |
| → Send | `interrupt` | Stop agent mid-speech |
| ↔ Both | `ping` / `pong` | Keep-alive |

### Languages Supported
| Language | STT | TTS |
|----------|-----|-----|
| 🇬🇧 English | `en-GB` | Native |
| 🇮🇳 Hindi | `hi-IN` | Native |
| 🇮🇳 Marathi | `mr-IN` | Fallback to hi-IN |
| 🇮🇳 Malayalam | `ml-IN` | Fallback to hi-IN |

### TTS Fallback Chain
If the selected language voice is unavailable on the OS/browser:
```
ml-IN → hi-IN → en-IN → en-US
mr-IN → hi-IN → en-IN → en-US
```

---

## Auth Flow

1. JWT stored in `localStorage` on login/register
2. All API calls attach `Authorization: Bearer <token>` via `useApi.js`
3. Any `401` response → auto logout + redirect to `/login`
4. After login, superadmins are redirected to `/admin`, regular users to `/`
5. Admin routes are guarded in both Vue Router (`requiresSuperadmin`) and backend (`require_superadmin` dependency)

---

## Per-Agent API Keys

Each voice agent can use a different LLM and voice provider with its own API key:

1. Go to **Profile → API Keys** and add your keys for any provider
2. When creating an agent, select the LLM provider + key and TTS provider + key from your saved keys
3. Keys are encrypted at rest using Fernet symmetric encryption
4. Key previews (last 4 chars) are shown in the UI — full keys are never returned by the API

---

## External Integration (Webhook)

Connect Voxen agents to any external platform, automation suite, or CRM:

1. Open an agent → click **Generate Webhook URL**
2. Copy the URL: `https://your-domain/api/v1/webhook/agent/{token}`
3. POST from your external tool with the payload above
4. Voxen processes the message and POSTs the response back to your `callback_url`

---

## Performance Notes

- Uses `uvloop` + `httptools` for 20–50% faster async throughput
- Groq Whisper STT runs in a thread pool via `asyncio.to_thread` to avoid blocking the event loop
- Embedding models (sentence-transformers) are loaded once at startup as module-level singletons
- ChromaDB client is cached — not re-instantiated per request
- LLM retries are capped at 2 with a 10s timeout to prevent CPU-burning retry loops
- DB connection pooling: `pool_size=5`, `max_overflow=10`, `pool_recycle=300`