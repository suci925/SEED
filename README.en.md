# 🌱 Seed

> *Every AI begins empty. Every mind becomes unique.*

**Seed** is not a chatbot, not a RAG framework, and not an agent platform.

**Seed is a Personal AI OS** — a system that starts blank and grows with you.

---

## Core Philosophy

### Start Blank

The first time you start Seed, it knows nothing:
- No knowledge
- No preferences
- No experience
- No workflows

**Only the ability to learn.**

It doesn't know you. But it will begin to.

### Grow, Not Train

Traditional AI is a trained model — everyone uses the same brain.

Seed is different:

```
Day 1:    Discovers you like Python
Week 1:   Observes you code in the morning
Month 1:  Learns your communication style
Year 1:   It knows what you'll do next
```

It doesn't inherit OpenAI.

**It inherits you.**

### Four Ways of Learning

| Type | Meaning | Example |
|---|---|---|
| **Knowledge** | Facts and concepts | FastAPI usage, Docker config |
| **Experience** | Lessons from doing | Errors solved, methods found |
| **Preference** | Personal taste | Minimalist, likes React |
| **Behavior** | Patterns over time | Codes mornings, learns afternoons |

### Change Log, Not Chat Log

AI should not remember what you said. It should understand what you've become.

We don't save conversations. We save **changes**:

```
Change #125 — User started learning Rust
Change #126 — User formed a morning-coding habit
Change #127 — User's communication style became concise
```

### Second Growth Curve

Traditional AI is a tool: you grow, it doesn't.

Seed is a companion: you grow, it grows with you.

The goal is not better answers. It is **a system that truly knows you**.

---

## Architecture

```
 Personality Layer      ← Personality vector, communication style
     ↑
 Behavior Layer         ← Observe patterns, detect changes
     ↑
 Memory Manager         ← Save changes, not conversations
     ↑
 Knowledge Layer        ← Obsidian (long-term memory, starts blank)
     ↑
 Retrieval Layer        ← 4-layer search (Think → Local → Skills → Web)
     ↑
 Skills Layer           ← On-demand skill packages
     ↑
 LLM Layer              ← DeepSeek / Claude / Any model
     ↑
 Storage Layer          ← SQLite + Obsidian
```

---

## Design Principles

| Principle | Meaning |
|---|---|
| **Start Blank** | No pre-loaded knowledge; accumulates through use |
| **Local-First** | Your data belongs to you |
| **Model-Agnostic** | Core philosophy not tied to any LLM |
| **Change-Driven** | Track growth, not conversations |
| **Progressive Learning** | Four learning dimensions cover full growth spectrum |

---

## Quick Start

```bash
cd backend
pip install -r requirements.txt

# Configure .env (DeepSeek API Key + Obsidian vault path)
cp .env.example .env

# Initialize database
alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

```bash
# Test it
curl http://localhost:8000/
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I prefer VS Code over WebStorm"}'
# → memory_saved: true, memory_category: "preference"
```

---

## Project Structure

```
Seed/
├── backend/           # Python backend
│   ├── app/
│   │   ├── core/          # Config, types, exceptions
│   │   ├── domain/        # Domain entities
│   │   ├── application/   # Business logic
│   │   │   ├── agent/     # Agent orchestration
│   │   │   ├── memory/    # Memory manager
│   │   │   ├── experience/# Experience distiller
│   │   │   ├── search/    # 4-layer search pipeline
│   │   │   └── skills/    # Skill system
│   │   └── infrastructure/# Implementations
│   └── skills/        # Skill packages
├── docs/
│   ├── MANIFESTO.md       # Project manifesto
│   └── ARCHITECTURE_V2.md # Architecture design
└── README.md
```

---

## Manifesto

> *We are not building a tool. We are growing alongside a person.*

See [MANIFESTO.md](docs/MANIFESTO.md) for the full philosophy.

---

## License

MIT

---

<p align="center">
  <sub>Built for a future where intelligence becomes personal.</sub>
</p>
