
import uvicorn

from fastapi import FastAPI, HTTPException
from typing import List
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

app = FastAPI()

# Database Connection

DATABASE_URL = "postgresql+psycopg2://postgres:vivek123@localhost/quizzes"
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()
Base = declarative_base()


# Quiz Model
class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    questions = Column(JSON, nullable=False)


# Quiz Response Model
class QuizResponse(BaseModel):
    questions: List[str]
    options: List[List[str]]


# Quiz Answer Model
class QuizAnswer(BaseModel):
    quiz_id: int
    user_answers: List[str]


# Quiz Result Model
class QuizResult(BaseModel):
    quiz_id: int
    score: int
    correct_answers: List[str]


# Retrieve a specific quiz
@app.get("/quizzes/{quiz_id}", response_model=QuizResponse)
def get_quiz(quiz_id: int):
    quiz = session.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    questions = quiz.questions.keys()
    options = [list(quiz.questions[q]) for q in questions]
    return {"questions": list(questions), "options": options}


# Allow users to submit their quiz answers
@app.post("/submit")
def submit_quiz_answers(answers: List[QuizAnswer]):
    result = {"quiz_id": answers[0].quiz_id, "score": 0, "correct_answers": []}
    quiz = session.query(Quiz).filter(Quiz.id == result["quiz_id"]).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    for answer in answers:
        question = list(quiz.questions.keys())[answer.quiz_id - 1]
        correct_answer = quiz.questions[question][0]
        if answer.user_answers[0] == correct_answer:
            result["score"] += 1
        result["correct_answers"].append(correct_answer)

    return result


# Return the quiz result for a specific quiz
@app.get("/result/{quiz_id}", response_model=QuizResult)
def get_quiz_result(quiz_id: int):
    quiz = session.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    return {
        "quiz_id": quiz_id,
        "score": 0,
        "correct_answers": list(quiz.questions.values()),
    }


# Initialize the database
def init_db():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=8000)