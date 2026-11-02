"""
FastAPI REST API Endpoints
Provides test retrieval, grading engine, attempt history, and analytics aggregations.
"""

from fastapi import APIRouter, HTTPException, Query
import json
import sqlite3
from typing import List, Dict, Any, Optional

from app.database import get_connection
from app.models import (
    QuestionPublic,
    ExamSubmission,
    ExamSubmissionResponse,
    QuestionResult,
    AttemptSummary,
    AnalyticsData,
    SectionAccuracy
)

router = APIRouter(prefix="/api", tags=["Exam & Analytics API"])

@router.get("/questions", response_model=List[QuestionPublic])
def get_exam_questions(
    level: int = Query(default=1, ge=1, le=6, description="HSK Level (1, 2, or 3)"),
    count: int = Query(default=8, ge=1, le=50, description="Number of questions in test")
):
    """
    Fetches randomized questions for the specified HSK level.
    Security Invariant: The answer key and explanations are stripped from response.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, level, part, question, pinyin, translation, options
        FROM questions
        WHERE level = ?
        ORDER BY RANDOM()
        LIMIT ?
    """, (level, count))
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        raise HTTPException(status_code=404, detail=f"No questions found for HSK Level {level}")
        
    questions = []
    for row in rows:
        options = json.loads(row["options"]) if isinstance(row["options"], str) else row["options"]
        questions.append(QuestionPublic(
            id=row["id"],
            level=row["level"],
            part=row["part"],
            question=row["question"],
            pinyin=row["pinyin"],
            translation=row["translation"],
            options=options
        ))
        
    return questions

@router.post("/submit", response_model=ExamSubmissionResponse)
def submit_exam(submission: ExamSubmission):
    """
    Evaluates submitted answers against the authoritative database key,
    computes scores and section breakdowns, and persists attempt telemetry.
    """
    if not submission.answers:
        raise HTTPException(status_code=400, detail="No answers provided in submission")
        
    question_ids = [ans.question_id for ans in submission.answers]
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Query corresponding questions
    placeholders = ",".join("?" for _ in question_ids)
    cursor.execute(f"""
        SELECT id, level, part, question, pinyin, options, correct_answer, explanation
        FROM questions
        WHERE id IN ({placeholders})
    """, question_ids)
    
    db_questions = {row["id"]: row for row in cursor.fetchall()}
    
    score = 0
    total = len(submission.answers)
    parts_map: Dict[str, List[int]] = {}  # {part: [correct, total]}
    results: List[QuestionResult] = []
    
    for user_ans in submission.answers:
        q_id = user_ans.question_id
        selected = user_ans.selected_option
        
        q_data = db_questions.get(q_id)
        if not q_data:
            continue
            
        part = q_data["part"]
        correct_answer = q_data["correct_answer"]
        is_correct = (selected == correct_answer) if selected is not None else False
        
        if part not in parts_map:
            parts_map[part] = [0, 0]
        parts_map[part][1] += 1
        
        if is_correct:
            score += 1
            parts_map[part][0] += 1
            
        results.append(QuestionResult(
            question_id=q_id,
            question=q_data["question"],
            pinyin=q_data["pinyin"],
            part=part,
            selected=selected,
            correct_answer=correct_answer,
            is_correct=is_correct,
            explanation=q_data["explanation"]
        ))
        
    percentage = round((score / total) * 100, 2) if total > 0 else 0.0
    
    # Persist attempt to SQLite database for analytics tracking
    cursor.execute("""
        INSERT INTO exam_attempts (
            user_id, level, score, total, percentage, time_spent_seconds, parts, answers_detail
        ) VALUES ('guest', ?, ?, ?, ?, ?, ?, ?)
    """, (
        submission.level,
        score,
        total,
        percentage,
        submission.time_spent_seconds,
        json.dumps(parts_map, ensure_ascii=False),
        json.dumps([r.model_dump() for r in results], ensure_ascii=False)
    ))
    
    attempt_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return ExamSubmissionResponse(
        attempt_id=attempt_id,
        level=submission.level,
        score=score,
        total=total,
        percentage=percentage,
        time_spent_seconds=submission.time_spent_seconds,
        parts=parts_map,
        results=results
    )

@router.get("/attempts", response_model=List[AttemptSummary])
def get_exam_attempts(limit: int = 50):
    """Retrieves chronological history of exam attempts."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, level, score, total, percentage, time_spent_seconds, parts, created_at
        FROM exam_attempts
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    attempts = []
    for r in rows:
        parts_data = json.loads(r["parts"]) if isinstance(r["parts"], str) else r["parts"]
        attempts.append(AttemptSummary(
            id=r["id"],
            level=r["level"],
            score=r["score"],
            total=r["total"],
            percentage=r["percentage"],
            time_spent_seconds=r["time_spent_seconds"],
            parts=parts_data,
            created_at=r["created_at"]
        ))
        
    return attempts

@router.get("/analytics", response_model=AnalyticsData)
def get_analytics():
    """
    Computes dimensional aggregates for user learning trajectory,
    including overall accuracy, section breakdown, and score history.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, level, score, total, percentage, time_spent_seconds, parts, created_at
        FROM exam_attempts
        ORDER BY created_at ASC
    """)
    attempts = cursor.fetchall()
    conn.close()
    
    if not attempts:
        return AnalyticsData(
            total_tests=0,
            average_score_pct=0.0,
            highest_score_pct=0.0,
            total_questions_answered=0,
            recent_scores=[],
            parts_accuracy={},
            weakest_part=None,
            strongest_part=None
        )
        
    total_tests = len(attempts)
    total_questions = sum(r["total"] for r in attempts)
    avg_score = round(sum(r["percentage"] for r in attempts) / total_tests, 1)
    highest_score = round(max(r["percentage"] for r in attempts), 1)
    
    # Recent 12 scores for time series charting
    recent_scores = []
    for r in attempts[-12:]:
        recent_scores.append({
            "id": r["id"],
            "level": r["level"],
            "score": r["score"],
            "total": r["total"],
            "percentage": r["percentage"],
            "date": r["created_at"]
        })
        
    # Aggregate accuracy by section
    accumulated_parts: Dict[str, List[int]] = {}
    for r in attempts:
        parts = json.loads(r["parts"]) if isinstance(r["parts"], str) else r["parts"]
        for part_name, (c_score, c_total) in parts.items():
            if part_name not in accumulated_parts:
                accumulated_parts[part_name] = [0, 0]
            accumulated_parts[part_name][0] += c_score
            accumulated_parts[part_name][1] += c_total
            
    parts_accuracy: Dict[str, SectionAccuracy] = {}
    weakest_part = None
    strongest_part = None
    min_pct = 999.0
    max_pct = -1.0
    
    for part_name, (score_val, total_val) in accumulated_parts.items():
        pct = round((score_val / total_val) * 100, 1) if total_val > 0 else 0.0
        parts_accuracy[part_name] = SectionAccuracy(
            score=score_val,
            total=total_val,
            percentage=pct
        )
        if pct < min_pct:
            min_pct = pct
            weakest_part = part_name
        if pct > max_pct:
            max_pct = pct
            strongest_part = part_name
            
    return AnalyticsData(
        total_tests=total_tests,
        average_score_pct=avg_score,
        highest_score_pct=highest_score,
        total_questions_answered=total_questions,
        recent_scores=recent_scores,
        parts_accuracy=parts_accuracy,
        weakest_part=weakest_part,
        strongest_part=strongest_part
    )
