# AgentIQ — Neural OS
![Python](https://img.shields.io/badge/Python-3.11%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green?style=for-the-badge&logo=fastapi)
![Vue](https://img.shields.io/badge/Vue-3-brightgreen?style=for-the-badge&logo=vue.js)
![Tailwind CSS](https://img.shields.io/badge/Tailwind%20CSS-3-38bdf8?style=for-the-badge&logo=tailwind-css)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active%20Development-brightgreen?style=for-the-badge)

AI-powered business intelligence with 8 LangGraph agents  
Built-in voice assistant using free browser Web Speech API  
Full auth system, admin panel, agent fleet management

---

## Table of Contents
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
- [Environment Variables](#environment-variables)
- [Database Setup](#database-setup)
- [Running the App](#running-the-app)
- [API Reference](#api-reference)
- [Frontend Pages](#frontend-pages)
- [AI Agent Pipeline](#ai-agent-pipeline)
- [Voice Agent Flow](#voice-agent-flow)
- [Deployment](#deployment)
- [Known Issues](#known-issues)
- [Contributing](#contributing)
- [License](#license)

---

## Features

| Backend Features | Frontend Features |
|------------------|-------------------|
| JWT authentication with bcrypt | Vue 3 Composition API + Pinia state |
| Role-based access control (admin/user) | Voice agent with animated neural orb |
| 8-agent LangGraph AI pipeline | 12-language voice support (free, no API key) |
| Gemini 2.5 Flash-Lite LLM integration | Real-time execution terminal |
| Voice chat endpoint (STT → LLM → TTS) | Agent fleet management with slide-out drawer |
| Agent CRUD with clone/template system | Admin command center with SVG bar charts |
| Admin panel: user management, job monitoring, stats | Dark glassmorphism UI design |
| PostgreSQL + SQLAlchemy + Alembic migrations | JWT auth with auto-logout on 401 |
| Background task processing | Toast notification system |
| Structlog audit logging | Mobile-responsive layout |
| CORS configured for Vue dev server | |

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Backend** |
| Runtime | Python 3.11 | Core language |
| Framework | FastAPI 0.111 | API server |
| ORM | SQLAlchemy 2.0 | Database access |
| Migrations | Alembic | Schema versioning |
| Auth | python-jose + passlib bcrypt | JWT + password hashing |
| LLM | langchain-google-genai (Gemini 2.5 Flash-Lite) | AI model |
| AI Pipeline | LangGraph | Agent workflow |
| Database | PostgreSQL | Relational storage |
| Validation | Pydantic v2 | Data validation |
| Logging | structlog | Structured logging |
| **Frontend** |
| Framework | Vue 3 (Composition API) | UI framework |
| Build | Vite 5 | Development server |
| State | Pinia | State management |
| Router | Vue Router 4 | Client-side routing |
| Styling | Tailwind CSS 3 | Utility-first CSS |
| Icons | Material Symbols Outlined | Icon set |
| Voice | Web Speech API (free, browser-native) | STT/TTS |
| HTTP | Fetch API with Bearer auth | API communication |

---

## Project Structure

<details>
<summary>Click to expand project structure</summary>

```bash
agentiq/
├── backend/
│   ├── main.py                    # FastAPI app + router registration
│   ├── requirements.txt
│   ├── .env                       # Environment variables (not committed)
│   ├── alembic.ini
│   ├── alembic/versions/          # DB migrations
│   └── app/
│       ├── config.py              # Settings (pydantic-settings)
│       ├── database.py            # SQLAlchemy engine + get_db
│       ├── llm_router.py          # Gemini LLM factory
│       ├── worker.py              # Background plan generation
│       ├── auth/
│       │   ├── security.py        # bcrypt + JWT
│       │   └── dependencies.py    # get_current_user, require_admin
│       ├── models/
│       │   ├── user.py            # User + UserRole enum
│       │   ├── agent_config.py    # AgentConfig + voice fields
│       │   └── plan.py            # Plan + AgentTrace + JobStatus
│       ├── schemas/
│       │   ├── user.py            # UserRegister, UserResponse, TokenResponse
│       │   ├── agent_config.py    # AgentConfigCreate/Update/Response
│       │   └── plan.py            # PlanCreate, PlanResponse
│       ├── routes/
│       │   ├── auth.py            # register/login/me/logout/change-password
│       │   ├── agents.py          # CRUD + clone
│       │   ├── voice.py           # POST /voice/chat
│       │   ├── plan.py            # POST + GET /plan
│       │   └── admin.py           # users/jobs/stats/reset-password
│       └── agents/                # LangGraph AI agents (unchanged)
│
└── agentiq-vue/
    ├── index.html
    ├── vite.config.js
    ├── tailwind.config.js
    ├── package.json
    ├── .env                       # VITE_API_URL
    └── src/
        ├── main.js
        ├── App.vue
        ├── router/index.js        # Routes + auth/admin guards
        ├── stores/
        │   ├── auth.js            # JWT + user (Pinia)
        │   └── toast.js           # Toast notifications (Pinia)
        ├── composables/
        │   └── useApi.js          # Fetch wrapper + 401 guard
        ├── views/                 # 7 page views
        └── components/            # 14 components across 5 categories
```
</details>

---

## Prerequisites

Before setting up the project, ensure you have the following installed:

- **Python 3.11 or higher**
- **Node.js 18 or higher**
- **PostgreSQL 14 or higher** (running locally or via Docker)
- **Git**

> 💡 **Tip**: You can use Docker to run PostgreSQL quickly:
> ```bash
> docker run --name agentiq-db -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=agentiq -p 5432:5432 -d postgres:16
> ```

---

## Installation & Setup

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <repo-url> && cd agentiq
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   # Linux/macOS:
   source venv/bin/activate
   # Windows:
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Create the `.env` file**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and fill in the required variables (see [Environment Variables](#environment-variables)).

5. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

6. **Start the backend**
   ```bash
   uvicorn main:app --reload --port 8000
   ```

### Frontend Setup

1. **Navigate to the frontend folder**
   ```bash
   cd agentiq-vue
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Create environment file**
   ```bash
   cp .env.example .env
   ```
   Set `VITE_API_URL=http://localhost:8000` in `.env`.

4. **Start the development server**
   ```bash
   npm run dev
   ```
   The app will open at [http://localhost:5173](http://localhost:5173).

---

## Environment Variables

### Backend (`.env`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | — | PostgreSQL connection string (e.g., `postgresql://user:pass@localhost:5432/dbname`) |
| `GOOGLE_API_KEY` | Yes | — | Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey) |
| `JWT_SECRET` | Yes | — | Random 32+ character string for JWT signing |
| `CORS_ORIGINS` | No | `["http://localhost:5173"]` | Allowed frontend origins (JSON array) |
| `APP_NAME` | No | `AgentIQ` | Application name |
| `APP_VERSION` | No | `2.4.0` | Application version |
| `MAX_AGENTS_PER_USER` | No | `20` | Maximum agents per user account |

### Frontend (`.env`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VITE_API_URL` | Yes | `http://localhost:8000` | Backend API base URL |

> 🔑 **Note**: Get a free Gemini API key at [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

---

## Database Setup

The project uses **Alembic** for schema migrations. There are 4 migration files:
- `001_agent_traces`
- `002_created_by`
- `003_users_agents`
- `004_voice_fields`

### Migration Commands

```bash
# Apply all migrations
alembic upgrade head

# Check current version
alembic current

# Rollback one step
alembic downgrade -1

# Auto-generate new migration after model changes
alembic revision --autogenerate -m "description"
```

### Tables Created

- `users` — Operator accounts with role and usage statistics
- `agent_configs` — Voice and BI agent configurations
- `plans` — Business intelligence job records
- `agent_traces` — Per-agent execution telemetry

---

## API Reference

### AUTH (Public)
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/auth/register` | — | Register new operator + creates 2 default agents |
| POST | `/api/v1/auth/login` | — | Login, returns JWT + user object |
| GET | `/api/v1/auth/me` | JWT | Get current user profile |
| PUT | `/api/v1/auth/me` | JWT | Update username |
| POST | `/api/v1/auth/change-password` | JWT | Change own password |
| POST | `/api/v1/auth/logout` | JWT | Logout (client discards token) |

### AGENTS (JWT Required)
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/agents` | JWT | List own + public + template agents |
| POST | `/api/v1/agents` | JWT | Create new agent |
| GET | `/api/v1/agents/:uuid` | JWT | Get single agent |
| PUT | `/api/v1/agents/:uuid` | JWT | Update agent (owner only) |
| DELETE | `/api/v1/agents/:uuid` | JWT | Delete agent (owner only) |
| POST | `/api/v1/agents/:uuid/clone` | JWT | Clone public/template agent |

### VOICE (JWT Required)
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/voice/chat` | JWT | Send transcribed text, receive spoken response |

### BUSINESS INTELLIGENCE (JWT Optional)
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/plan` | Optional | Submit a business intelligence job |
| GET | `/api/v1/plan/:job_id` | Optional | Poll job status and retrieve result |

### ADMIN (Admin Role Required)
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/admin/users` | JWT (Admin) | List all users |
| PATCH | `/api/v1/admin/users/:uuid` | JWT (Admin) | Update user role or active status |
| POST | `/api/v1/admin/users/:uuid/reset-password` | JWT (Admin) | Force reset user password |
| GET | `/api/v1/admin/jobs` | JWT (Admin) | List all jobs across all users |
| GET | `/api/v1/admin/stats` | JWT (Admin) | Platform-wide statistics |

---

## Frontend Pages

| Page | Route | Auth | Description |
|------|-------|------|-------------|
| Login | `/login` | Public | JWT login form with email + password |
| Register | `/register` | Public | New operator registration |
| Workspace | `/workspace` | Auth | Split view: Voice agent (45%) + BI platform (55%) |
| Voice | `/voice` | Auth | Immersive full-screen voice mode with animated orb |
| Agents | `/agents` | Auth | Agent fleet grid with create/edit/clone/delete drawer |
| Profile | `/profile` | Auth | User stats + change username/password + my agents tab |
| Admin | `/admin` | Admin only | Command center: overview stats, users table, jobs table |

---

## AI Agent Pipeline

```text
User Prompt
    │
    ▼
┌─────────────┐
│ Orchestrator│ ← Parse + route prompt
└──────┬──────┘
       │
    ▼
┌─────────────┐
│   Memory    │ ← ChromaDB vector retrieve
└──────┬──────┘
       │
    ▼
┌─────────────┐
│  Research   │ ← Tavily / DuckDuckGo search
└──────┬──────┘
       │
    ▼
┌─────────────┐
│  Strategy   │ ← GTM + pricing analysis
└──────┬──────┘
       │
    ▼
┌─────────────┐
│   Critic    │ ← Quality review (retry if fail)
└──────┬──────┘
       │
    ▼
┌─────────────┐
│   Planner   │ ← Week-by-week plan
└──────┬──────┘
       │
    ▼
┌─────────────┐
│     QA      │ ← Validate + score output
└──────┬──────┘
       │
    ▼
┌─────────────┐
│  Formatter  │ ← JSON + Markdown output
└──────┬──────┘
       │
    ▼
┌─────────────┐
│   Memory    │ ← ChromaDB vector store
└─────────────┘
```

---

## Voice Agent Flow

1. 🎙️  **User clicks orb** → browser `SpeechRecognition` starts (free, no API key)  
2. 📝  **Browser transcribes speech** → text string produced locally  
3. 📡  **Text sent** via `POST /api/v1/voice/chat` with JWT token  
4. 🤖  **Backend loads** agent's `system_prompt` + `knowledge_base_text`  
5. ✨  **Gemini 2.5 Flash-Lite** generates concise conversational response  
6. 📬  **Response text returned** to browser  
7. 🔊  **Browser `speechSynthesis`** speaks the response aloud (free, no API key)  

> ✅ **Note**: STT and TTS are both 100% free using built-in browser APIs.  
> Only the LLM (Gemini) requires an API key, which has a generous free tier.

---

## Deployment

### Backend (Railway / Render / VPS)
- Set all environment variables in the platform dashboard  
- Change `JWT_SECRET` to a strong random string  
- Set `DATABASE_URL` to your production PostgreSQL URL  
- Set `CORS_ORIGINS` to your production frontend URL  
- Run: `alembic upgrade head` before starting  
- Start command: `uvicorn main:app --host 0.0.0.0 --port 8000`

### Frontend (Vercel / Netlify)
- Set `VITE_API_URL` to your production backend URL  
- Build command: `npm run build`  
- Output directory: `dist`  
- All routes must redirect to `index.html` (SPA routing)

### Security Checklist for Production
- [ ] `JWT_SECRET` is at least 32 random characters  
- [ ] `GOOGLE_API_KEY` is restricted to your domain in Google Console  
- [ ] `CORS_ORIGINS` does NOT include `localhost`  
- [ ] PostgreSQL is not publicly accessible (use internal networking)  
- [ ] `.env` file is in `.gitignore`

---

## Known Issues

1. **WebSocket live agent timeline not yet implemented**  
   The `ExecutionTerminal` polls via REST every 2 seconds instead of streaming.  
   **Impact**: Slight delay in live log updates during plan generation.

2. **Plan history endpoint not yet implemented**  
   `GET /api/v1/plan/history` is listed in the architecture but not built.  
   **Impact**: No job history page in the frontend.

3. **Celery/Redis not wired up**  
   Background tasks use FastAPI `BackgroundTasks` instead of Celery.  
   **Impact**: Tasks run in the same process; not suitable for high load.

4. **Web Speech API browser support**  
   `SpeechRecognition` is not supported in Firefox.  
   **Recommendation**: Use Chrome, Edge, or Safari.

---

## Contributing

1. Fork the repository  
2. Create a feature branch: `git checkout -b feature/your-feature`  
3. Make changes and test locally  
4. Commit with a clear message: `git commit -m "feat: add X"`  
5. Push and open a Pull Request  

### Code Style
- **Backend**: Follow PEP 8, use type hints everywhere  
- **Frontend**: Use Vue 3 Composition API with `<script setup>`  
- **Commits**: Use conventional commits (`feat/fix/docs/refactor`)

---

## License

This project is licensed under the MIT License.