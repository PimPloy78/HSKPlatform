"""
Pydantic Schemas for Data Contracts & API Validation
Enforces runtime typing, input sanitization, and output serialization.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class QuestionPublic(BaseModel):
    id: int
    level: int
    part: str
    question: str
    pinyin: Optional[str] = None
    translation: Optional[str] = None
    options: List[str]

class UserAnswer(BaseModel):
    question_id: int
    selected_option: Optional[str] = None

class ExamSubmission(BaseModel):
    level: int = Field(default=1, ge=1, le=6)
    time_spent_seconds: int = Field(default=0, ge=0)
    answers: List[UserAnswer]

class QuestionResult(BaseModel):
    question_id: int
    question: str
    pinyin: Optional[str] = None
    part: str
    selected: Optional[str] = None
    correct_answer: str
    is_correct: bool
    explanation: Optional[str] = None

class ExamSubmissionResponse(BaseModel):
    attempt_id: int
    level: int
    score: int
    total: int
    percentage: float
    time_spent_seconds: int
    parts: Dict[str, List[int]]  # {"คำศัพท์": [3, 4], "ไวยากรณ์": [2, 2]}
    results: List[QuestionResult]

class AttemptSummary(BaseModel):
    id: int
    level: int
    score: int
    total: int
    percentage: float
    time_spent_seconds: int
    parts: Dict[str, List[int]]
    created_at: str

class SectionAccuracy(BaseModel):
    score: int
    total: int
    percentage: float

class AnalyticsData(BaseModel):
    total_tests: int
    average_score_pct: float
    highest_score_pct: float
    total_questions_answered: int
    recent_scores: List[Dict[str, Any]]
    parts_accuracy: Dict[str, SectionAccuracy]
    weakest_part: Optional[str] = None
    strongest_part: Optional[str] = None
