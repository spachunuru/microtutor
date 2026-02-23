"""Tests for lesson context in the chat endpoint."""
import json
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.server import app
from app.database import get_db, _connection
import app.database as db_module


@pytest.fixture(autouse=True)
def fresh_db(tmp_path):
    """Use a fresh in-memory DB for each test."""
    db_module._connection = None
    from app.config import settings
    original = settings.db_path
    settings.db_path = tmp_path / "test.db"
    get_db()  # initialize schema
    yield
    db_module._connection = None
    settings.db_path = original


@pytest.fixture
def client():
    return TestClient(app)


MOCK_RESPONSE = "Here is my tutoring response."


def _seed_skill_and_lesson(content: dict | None = None):
    """Insert a skill and lesson, return (skill_id, lesson_id)."""
    from app.database import execute
    skill_id = execute(
        "INSERT INTO skills (user_id, name, description) VALUES (1, 'Python Basics', 'Learn Python')",
        (),
    )
    lesson_content = content or {
        "topic": "Variables and Types",
        "objective": "Understand how to declare variables and use basic types",
        "key_points": [
            "Variables store values",
            "Python is dynamically typed",
            "Common types: int, float, str, bool",
        ],
        "exercises": [
            {
                "title": "Declare a variable",
                "instructions": "Create a variable called name and assign your name to it",
                "starter_code": "# write your code here",
            },
            {
                "title": "Type checking",
                "instructions": "Use type() to print the type of each variable",
                "starter_code": "x = 42",
            },
        ],
    }
    lesson_id = execute(
        "INSERT INTO lessons (skill_id, topic, order_index, content_json) VALUES (?, 'Variables and Types', 1, ?)",
        (skill_id, json.dumps(lesson_content)),
    )
    return skill_id, lesson_id


# --- Lesson context tests ---

@patch("app.routes.chat.tutor.chat", return_value=MOCK_RESPONSE)
def test_chat_with_lesson_id(mock_chat, client):
    """When lesson_id is provided, tutor receives lesson context."""
    skill_id, lesson_id = _seed_skill_and_lesson()

    resp = client.post("/api/chat", json={
        "skill_id": skill_id,
        "lesson_id": lesson_id,
        "message": "What are variables?",
        "history": [],
    })

    assert resp.status_code == 200
    assert resp.json()["response"] == MOCK_RESPONSE

    # Verify the skill_context passed to tutor.chat contains lesson info
    call_args = mock_chat.call_args
    context = call_args[1].get("skill_context") or call_args[0][1]
    assert "Variables and Types" in context
    assert "Understand how to declare variables" in context
    assert "dynamically typed" in context
    assert "Declare a variable" in context
    assert "Type checking" in context
    # Starter code should NOT appear in context
    assert "starter_code" not in context
    assert "# write your code here" not in context


@patch("app.routes.chat.tutor.chat", return_value=MOCK_RESPONSE)
def test_chat_without_lesson_id(mock_chat, client):
    """When lesson_id is omitted, works with just skill context (no crash)."""
    skill_id, _ = _seed_skill_and_lesson()

    resp = client.post("/api/chat", json={
        "skill_id": skill_id,
        "message": "Tell me about Python",
        "history": [],
    })

    assert resp.status_code == 200
    call_args = mock_chat.call_args
    context = call_args[1].get("skill_context") or call_args[0][1]
    assert "Python Basics" in context
    # No lesson-specific content
    assert "Variables and Types" not in context


@patch("app.routes.chat.tutor.chat", return_value=MOCK_RESPONSE)
def test_chat_no_skill_no_lesson(mock_chat, client):
    """General chat with neither skill_id nor lesson_id still works."""
    resp = client.post("/api/chat", json={
        "message": "Hello tutor!",
        "history": [],
    })

    assert resp.status_code == 200
    call_args = mock_chat.call_args
    context = call_args[1].get("skill_context") or call_args[0][1]
    assert context == ""


@patch("app.routes.chat.tutor.chat", return_value=MOCK_RESPONSE)
def test_chat_invalid_lesson_id(mock_chat, client):
    """Non-existent lesson_id is silently ignored."""
    resp = client.post("/api/chat", json={
        "lesson_id": 9999,
        "message": "Help me",
        "history": [],
    })

    assert resp.status_code == 200
    call_args = mock_chat.call_args
    context = call_args[1].get("skill_context") or call_args[0][1]
    assert context == ""


@patch("app.routes.chat.tutor.chat", return_value=MOCK_RESPONSE)
def test_chat_lesson_without_content_json(mock_chat, client):
    """Lesson exists but has no content_json — no crash."""
    from app.database import execute
    skill_id = execute(
        "INSERT INTO skills (user_id, name, description) VALUES (1, 'Test', 'desc')", ()
    )
    execute(
        "INSERT INTO lessons (skill_id, topic, order_index) VALUES (?, 'Empty', 1)",
        (skill_id,),
    )

    resp = client.post("/api/chat", json={
        "skill_id": skill_id,
        "lesson_id": 1,
        "message": "Help",
        "history": [],
    })

    assert resp.status_code == 200


@patch("app.routes.chat.tutor.chat", return_value=MOCK_RESPONSE)
def test_chat_lesson_partial_content(mock_chat, client):
    """Lesson content_json with only some fields still works."""
    content = {"topic": "Loops", "key_points": ["for loops", "while loops"]}
    skill_id, lesson_id = _seed_skill_and_lesson(content)

    resp = client.post("/api/chat", json={
        "skill_id": skill_id,
        "lesson_id": lesson_id,
        "message": "Explain loops",
        "history": [],
    })

    assert resp.status_code == 200
    call_args = mock_chat.call_args
    context = call_args[1].get("skill_context") or call_args[0][1]
    assert "Loops" in context
    assert "for loops" in context
    # No objective or exercises since they weren't in the content
    assert "Objective" not in context
    assert "Exercises" not in context


# --- lesson_id persistence tests ---

@patch("app.routes.chat.tutor.chat", return_value=MOCK_RESPONSE)
def test_chat_saves_lesson_id_to_db(mock_chat, client):
    """Chat messages include lesson_id in the database."""
    from app.database import query
    skill_id, lesson_id = _seed_skill_and_lesson()

    client.post("/api/chat", json={
        "skill_id": skill_id,
        "lesson_id": lesson_id,
        "message": "Help with variables",
        "history": [],
    })

    rows = query("SELECT skill_id, lesson_id, role, content FROM chat_messages ORDER BY id")
    assert len(rows) == 2  # user + assistant
    for row in rows:
        assert row["skill_id"] == skill_id
        assert row["lesson_id"] == lesson_id
    assert rows[0]["role"] == "user"
    assert rows[1]["role"] == "assistant"


@patch("app.routes.chat.tutor.chat", return_value=MOCK_RESPONSE)
def test_chat_saves_with_lesson_only(mock_chat, client):
    """Messages saved when lesson_id provided but skill_id is None."""
    from app.database import query
    _, lesson_id = _seed_skill_and_lesson()

    client.post("/api/chat", json={
        "lesson_id": lesson_id,
        "message": "Help me",
        "history": [],
    })

    rows = query("SELECT lesson_id, skill_id FROM chat_messages")
    assert len(rows) == 2
    assert rows[0]["lesson_id"] == lesson_id
    assert rows[0]["skill_id"] is None


@patch("app.routes.chat.tutor.chat", return_value=MOCK_RESPONSE)
def test_chat_no_messages_saved_without_ids(mock_chat, client):
    """No messages saved when neither skill_id nor lesson_id provided."""
    from app.database import query

    client.post("/api/chat", json={
        "message": "General question",
        "history": [],
    })

    rows = query("SELECT * FROM chat_messages")
    assert len(rows) == 0


# --- Review service tests ---

def test_review_queue_includes_lesson_topic():
    """Review queue cards include lesson_topic from JOIN."""
    from app.database import execute
    from app.services.review_service import get_review_queue

    skill_id = execute("INSERT INTO skills (user_id, name) VALUES (1, 'Test')", ())
    lesson_id = execute(
        "INSERT INTO lessons (skill_id, topic, order_index) VALUES (?, 'My Topic', 1)",
        (skill_id,),
    )
    execute(
        "INSERT INTO review_cards (user_id, lesson_id, question, answer, next_review_at) VALUES (1, ?, 'Q?', 'A.', datetime('now'))",
        (lesson_id,),
    )

    cards = get_review_queue(1)
    assert len(cards) == 1
    assert cards[0]["lesson_topic"] == "My Topic"
    assert cards[0]["lesson_id"] == lesson_id


def test_review_rate_returns_achievements():
    """Rating a review card returns new_achievements list."""
    from app.database import execute
    from app.services.review_service import rate_card

    skill_id = execute("INSERT INTO skills (user_id, name) VALUES (1, 'Test')", ())
    lesson_id = execute(
        "INSERT INTO lessons (skill_id, topic, order_index) VALUES (?, 'Topic', 1)",
        (skill_id,),
    )
    card_id = execute(
        "INSERT INTO review_cards (user_id, lesson_id, question, answer, next_review_at) VALUES (1, ?, 'Q?', 'A.', datetime('now'))",
        (lesson_id,),
    )

    result = rate_card(1, card_id, 4)  # "Good"
    assert "new_achievements" in result
    assert isinstance(result["new_achievements"], list)
    # first_review achievement should be unlocked
    keys = [a["key"] for a in result["new_achievements"]]
    assert "first_review" in keys
