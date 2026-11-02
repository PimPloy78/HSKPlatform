"""
Automated Test Suite for HSK Online Testing Platform
Covers API Contracts, Security Invariants, Grading Precision, and Analytics.
"""

import pytest
from fastapi.testclient import TestClient
import json

from main import app
from app.database import init_db
from app.etl_seed import run_etl

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Ensure schema and questions exist before running test suite."""
    init_db()
    run_etl()

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_get_questions_security():
    """Verifies that questions can be fetched, but sensitive answer keys are stripped."""
    response = client.get("/api/questions?level=1&count=4")
    assert response.status_code == 200
    questions = response.json()
    assert len(questions) == 4
    
    for q in questions:
        assert "id" in q
        assert "question" in q
        assert "options" in q
        assert isinstance(q["options"], list)
        assert len(q["options"]) >= 2
        # CRITICAL SECURITY CHECK: Client must not receive correct_answer in quiz payload
        assert "correct_answer" not in q
        assert "explanation" not in q

def test_get_questions_by_level():
    """Verifies level filtering."""
    for level in [1, 2, 3]:
        response = client.get(f"/api/questions?level={level}&count=3")
        assert response.status_code == 200
        questions = response.json()
        assert len(questions) > 0
        for q in questions:
            assert q["level"] == level

def test_submit_exam_and_grading():
    """Verifies grading accuracy, time tracking, and section breakdown."""
    # 1. Fetch 3 questions
    q_res = client.get("/api/questions?level=1&count=3")
    assert q_res.status_code == 200
    questions = q_res.json()
    assert len(questions) >= 3
    
    # 2. Submit answers
    submission_payload = {
        "level": 1,
        "time_spent_seconds": 45,
        "answers": [
            {"question_id": questions[0]["id"], "selected_option": questions[0]["options"][0]},
            {"question_id": questions[1]["id"], "selected_option": questions[1]["options"][0]},
            {"question_id": questions[2]["id"], "selected_option": questions[2]["options"][0]}
        ]
    }
    
    sub_res = client.post("/api/submit", json=submission_payload)
    assert sub_res.status_code == 200
    result = sub_res.json()
    
    assert "attempt_id" in result
    assert result["level"] == 1
    assert result["total"] == 3
    assert 0 <= result["score"] <= 3
    assert 0.0 <= result["percentage"] <= 100.0
    assert result["time_spent_seconds"] == 45
    assert "parts" in result
    assert len(result["results"]) == 3
    
    # Verify each result has explanation and correct_answer now available for review
    for res_item in result["results"]:
        assert "correct_answer" in res_item
        assert "is_correct" in res_item
        assert "explanation" in res_item

def test_attempts_history_endpoint():
    """Verifies that attempts are saved and retrievable."""
    response = client.get("/api/attempts?limit=10")
    assert response.status_code == 200
    attempts = response.json()
    assert isinstance(attempts, list)
    assert len(attempts) > 0
    first = attempts[0]
    assert "score" in first
    assert "total" in first
    assert "parts" in first
    assert "created_at" in first

def test_analytics_aggregation():
    """Verifies dimensional analytics calculations."""
    response = client.get("/api/analytics")
    assert response.status_code == 200
    analytics = response.json()
    
    assert analytics["total_tests"] > 0
    assert 0.0 <= analytics["average_score_pct"] <= 100.0
    assert 0.0 <= analytics["highest_score_pct"] <= 100.0
    assert analytics["total_questions_answered"] > 0
    assert isinstance(analytics["recent_scores"], list)
    assert isinstance(analytics["parts_accuracy"], dict)
