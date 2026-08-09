# Voxen

> A state-of-the-art multi-agent AI voice and chat orchestration platform. Build, secure, and monitor intelligent voice assistants, text chatbots, and Telegram gateways using your own API keys and custom pgvector knowledge bases.

[![Vue](https://img.shields.io/badge/Vue-3.4-4FC08D?logo=vue.js&logoColor=white)](https://vuejs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-async-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)](https://redis.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Key Features

* **🎙️ Voice Engine & Chat Lab**: Dual sandbox environments to test voice streaming (via WebSockets) and text-based multi-agent dialogs (via REST) in real time.
* **🧠 PGVector Knowledge Base (RAG)**: Context-aware responses driven by document vector embeddings. Supports uploading raw text files (`.txt`) and scraping custom URLs. Powered by Google's `gemini-embedding-001`.
* **🤖 Telegram Bot Gateways**: Connect live Telegram bots directly to your agent configurations. Features built-in bot verification, automatic webhook installation, and secure API key controls.
* **🔑 Secure External API Keys Suite**: Generate custom API keys (`vx_live_...`) to protect external webhook endpoints. Keys can be generated, previewed, and revoked on-demand.
* **📊 Unified Analytics Dashboard**: Track total requests, active conversation sessions, average latency breakdown (STT, TTS, Webhooks), and error rates with real-time logging.
* **🔒 Symmetric Encryption at Rest**: Per-user LLM and voice provider keys (Gemini, Groq, Azure, ElevenLabs) are encrypted using Fernet cryptography.

---

## Architecture Diagram

```
+---------------------------------------------------------------------------------+
|                                 Vue 3 Frontend                                  |
|                                                                                 |
|   Dashboard - Voice Lab - Chat Lab - Telegram Gateways - API Keys Dashboard     |
+----------------------------------------+----------------------------------------+
                                         |
                       REST / WebSocket  |  
                                         v
+---------------------------------------------------------------------------------+
|                                 FastAPI Backend                                 |
|                                                                                 |
|   [Auth Manager]   -->   [Agent Router]   -->   [Webhooks Gateway]              |
|         |                       |                       |                       |
|         v                       v                       v                       |
|   [PostgreSQL]            [LLM Router]            [Voice Pipeline]              |
|   - Users & Sessions      - Gemini / Groq /       - STT (Groq Whisper)          |
|   - API Keys & Configs      Anthropic Claude      - TTS (ElevenLabs / Azure)    |
|   - Transaction Logs      - Tool Calling (RAG)    - Webhooks (Sync / Async)     |
+---------------------------------------------------------------------------------+
```

---

## Project Structure

```
voxen/
├── docker-compose.yml              # Single-command Docker deployment
├── backend/
│   ├── main.py                     # FastAPI application entrypoint
│   ├── requirements.txt            # Python dependencies
│   ├── schema.sql                  # Initial database schema setup
│   └── app/
│       ├── database.py             # SQLAlchemy engine & session pool config
│       ├── llm_router.py           # Multi-provider LLM handler with tool calling
│       ├── models/
│       │   ├── user.py             # User authorization model
│       │   ├── agent_config.py     # Agent prompts, RAG configurations
│       │   ├── voxen_api_key.py    # Symmetric-encrypted API key definitions
│       │   ├── telegram_bot_config.py # Telegram linkage configurations
│       │   └── api_call.py         # Transaction logs for performance metrics
│       └── routes/
│           ├── chat.py             # In-app Chat Engine sandbox execution
│           ├── telegram.py         # Telegram verification & webhook controls
│           ├── voxen_api_keys.py   # API Key CRUD endpoints
│           └── webhooks.py         # External webhook API checking routes
└── frontend/
    ├── index.html                  # Core HTML single page application
    ├── package.json                # Frontend Vue dependencies
    └── src/
        ├── layouts/
        │   └── UserLayout.vue      # Main responsive shell with scrollable sidebar
        ├── views/
        │   ├── VoiceView.vue       # Voice Lab WebSocket test interface
        │   ├── TelegramBotsView.vue # Bot configuration drawer
        │   └── VoxenKeysView.vue   # Split-screen API keys suite
        └── components/
            └── metrics/
                └── ApiLogsTable.vue # Unified log viewer with inline loaders
```

---

## Deployment & Setup

### Option 1: Docker Compose (Recommended)

Start the entire stack (PostgreSQL database with schema initialization, Redis cache, FastAPI backend, and Vue frontend dev server) with a single command:

1. Clone this repository to your system.
2. Edit `backend/.env` to configure your external keys:
   ```env
   GEMINI_API_KEY=your-gemini-key
   JWT_SECRET=change-me-to-32-char-random-string
   ```
3. Run the docker-compose deployment:
   ```bash
   docker-compose up -d --build
   ```
4. Access the platform at `http://localhost:5173`.

---

### Option 2: Local Development (Manual Setup)

#### 1. Backend Setup (FastAPI)
```bash
cd backend

# Create and activate virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env

# Generate Fernet ENCRYPTION_KEY for API keys at rest
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Start the uvicorn development server
uvicorn main:app --reload --port 8000
```

#### 2. Frontend Setup (Vue 3)
```bash
cd frontend

# Install package dependencies
npm install

# Configure environment
cp .env.example .env
# Set: VITE_API_URL=http://localhost:8000

# Start local server
# Note: For Windows environments with running script restrictions, prefix with bypass:
powershell -ExecutionPolicy Bypass -Command "npm run dev"

# Build for production
powershell -ExecutionPolicy Bypass -Command "npm run build"
```

---

## Webhook Payload & Security

External API connections can be secured by linking them to a Voxen API Key. If keys are configured, incoming webhooks check for validation in this order:

1. **HTTP Request Header**: `X-Voxen-API-Key: vx_live_...`
2. **Query Parameter**: `?api_key=vx_live_...`
3. **JSON Body Parameter** (Text): `{"api_key": "vx_live_..."}`
4. **Form Parameter** (Voice): `api_key=vx_live_...`

### Text Webhook Example
`POST /api/v1/webhook/agent/{webhook_token}`

```json
{
  "text": "Hello, tell me about your projects.",
  "session_id": "session_id_hash",
  "language": "en",
  "api_key": "vx_live_your_voxen_key"
}
```

### Voice Webhook Example
`POST /api/v1/webhook/{webhook_id}`
* Request format: `multipart/form-data`
* Fields: `audio` (audio file binary), `language` (e.g. `en`), `session_id`, `api_key`.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
