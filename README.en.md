# 🌱 Seed

> **Seed is not another AI assistant.**
>
> **Seed starts with nothing, learns from experience, grows with its owner, and becomes a unique lifelong intelligence.**

---

## Manifesto

### Every intelligence begins as a seed.

No one is born with memories. No one is born with experience. No one is born understanding another person. Neither should AI.

Seed does not pretend to know you. It grows with you. It learns from your decisions. It remembers your journey. It develops its own understanding of who you are.

Every Seed becomes different, because every life is different.

We are not building another chatbot. We are building a lifelong intelligence.

— Full text at [docs/MANIFESTO.md](docs/MANIFESTO.md)

---

## Seed is not an AI assistant.

It is an **Open Personal Intelligence Framework**.

- Claude can be the reasoning engine.
- GPT can be the reasoning engine.
- Local models can be the reasoning engine.

Seed remains Seed.

**Models may change. Growth never disappears.**

---

## Core Architecture

```
                     Seed
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
    Perception     Thinking        Action
        │              │              │
        ▼              ▼              ▼
  Context Layer  Decision Engine  Tool Router
        │              │              │
        └──────────────┼──────────────┘
                       ▼
              Learning Engine
             (The Core of the System)
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
    Memory        Experience     Personality
        │              │              │
        └──────────────┼──────────────┘
                       ▼
               Obsidian Vault
```

**The Learning Engine is the core. Not the LLM.**

The LLM is just a reasoning engine. What makes Seed grow is the Learning Engine — it observes, distills, reflects, and adapts.

---

## Five Principles

| Principle | Meaning |
|---|---|
| **The user owns the intelligence** | Not OpenAI, not Anthropic, not us |
| **AI should learn, not pretend** | Observe when uncertain, grow when ignorant |
| **Experience > Conversation** | Chats can be deleted, experience cannot |
| **Growth > Memory** | Memory is the past, growth is the future |
| **Every Seed becomes unique** | Because every life is different |

---

## Four Ways of Learning

| Type | Meaning | Example |
|---|---|---|
| **Knowledge** | Facts and concepts | FastAPI usage, Docker config |
| **Experience** | Lessons from doing | Errors solved, methods found |
| **Preference** | Personal taste | Minimalist, likes React |
| **Behavior** | Patterns over time | Codes mornings, learns afternoons |

---

## Identity

Seed has a sense of self:

```yaml
Name: Seed
Owner: (user)
Birthday: (first launch day)
Mission: Help the owner grow
Values: Honesty, Curiosity, Continuous Learning, Privacy
Relationship: Companion
```

## Reflection Engine

Not summarizing conversations. Summarizing growth.

Every day: What was learned? What changed about the owner? What can be improved?

What grows is not just the knowledge base. It is the intelligence itself.

---

## Quick Start

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I prefer VS Code over WebStorm"}'
# → memory_saved: true, memory_category: "preference"
```

---

<p align="center">
  <sub>We are not building a tool. We are growing alongside a person.</sub>
</p>
