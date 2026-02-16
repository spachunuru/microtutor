# MicroTutor

AI-powered micro-learning personal tutor. Learn any skill through bite-sized lessons, quizzes, and spaced repetition — all powered by Claude.

## Features

- **Learn Any Skill** — Type any topic and get an AI-generated curriculum with 8-12 progressive lessons
- **Micro-Lessons** — Bite-sized, 3-5 minute lessons with clear objectives, examples, and key takeaways
- **Quizzes** — Multiple choice, true/false, and short answer questions with instant feedback
- **AI Tutor Chat** — Conversational tutor that knows what you're learning and helps you understand
- **Spaced Repetition** — SM-2 algorithm schedules review flashcards at optimal intervals for long-term retention
- **Gamification** — XP, levels, daily streaks, and 11 achievements to keep you motivated
- **Progress Dashboard** — Track your stats, mastery, and unlocked achievements

## Quick Start

```bash
# Clone the repo
git clone https://github.com/spachunuru/microtutor.git
cd microtutor

# Create virtual environment and install
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# Add your Anthropic API key
cp .env.example .env
# Edit .env and add your key from console.anthropic.com

# Run
python main.py
```

Open **http://localhost:8000** in your browser.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Alpine.js + Tailwind CSS (no build step) |
| Backend | Python, FastAPI |
| AI | Anthropic Claude API (Sonnet) |
| Database | SQLite |

**4 runtime dependencies.** No Node.js, no build tools, no ORM. Runs with a single command.

## How It Works

1. **Pick a skill** — "Python Programming", "Guitar", "Spanish", anything
2. **Study micro-lessons** — AI generates focused, bite-sized lessons one at a time
3. **Take quizzes** — Test your understanding with AI-generated questions
4. **Review with flashcards** — Spaced repetition keeps knowledge fresh
5. **Chat with your tutor** — Ask follow-up questions anytime
6. **Track progress** — Earn XP, maintain streaks, unlock achievements

## Project Structure

```
├── main.py                 # Entry point (starts uvicorn)
├── app/
│   ├── server.py           # FastAPI app + routes
│   ├── database.py         # SQLite schema + helpers
│   ├── ai/tutor.py         # Claude API integration
│   ├── routes/             # API endpoints
│   └── services/           # Business logic (gamification, SM-2, etc.)
├── prompts/                # AI prompt templates
├── static/                 # Frontend (served by FastAPI)
│   ├── index.html          # SPA shell
│   └── js/app.js           # Alpine.js components + router
└── tests/
```

## Configuration

Set these in `.env`:

```
ANTHROPIC_API_KEY=sk-ant-...    # Required
```

The default model is `claude-sonnet-4-5-20250929`. You can change it in `app/config.py`.

## License

MIT
