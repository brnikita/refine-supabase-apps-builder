# Blueprint Apps Builder

Generate business web applications from natural language prompts using AI.

## Quick Start

1. **Set up environment:**
   ```bash
   cp .env.example .env
   # Add your OpenRouter API key to .env
   ```

2. **Run with Docker:**
   ```bash
   docker-compose up --build
   ```

3. **Access the app:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Features

- Generate CRUD apps from text descriptions
- Automatic database schema creation
- Role-based permissions
- Start/Stop/Delete app lifecycle
- Dynamic runtime UI

## Tech Stack

- **Frontend:** Next.js, Tailwind CSS
- **Backend:** FastAPI, SQLAlchemy
- **Database:** PostgreSQL
- **LLM:** OpenRouter API

## Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENROUTER_API_KEY` | Your OpenRouter API key (required) |
| `SECRET_KEY` | JWT secret key |

