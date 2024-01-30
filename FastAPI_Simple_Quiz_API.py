from typing import Dict
import uvicorn

from fastapi import FastAPI, HTTPException
from typing import List
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

app = FastAPI()



DATABASE_URL = "postgresql+psycopg2://postgres:vivek123@localhost/quizzes"
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()
Base = declarative_base()

class Question(BaseModel):
    statement: str
    options: List[str]



class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    
    class Question(BaseModel):
        statement: str
        options: List[str]

    questions = Column(JSON, nullable=False)



class QuizResponse(BaseModel):
    questions: List[str]
    options: List[List[str]]



class QuizAnswer(BaseModel):
    quiz_id: int
    user_answers: List[str]



class QuizResult(BaseModel):
    quiz_id: int
    score: int
    correct_answers: List[str]



@app.get("/quizzes/{quiz_id}", response_model=QuizResponse)
def get_quiz(quiz_id: int):
    quiz = session.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

  
    questions_data = quiz.questions
    questions = [Question(**q) for q in questions_data]

   
    questions_statements = [q.statement for q in questions]
    options = [[f"{chr(65 + i)}: {option}" for i, option in enumerate(q.options)] for q in questions]

    return {"questions": questions_statements, "options": options}



def is_valid_option(option: str, total_options: int) -> bool:
    return option.upper() in [chr(65 + i) for i in range(total_options)]

@app.post("/submit")
def submit_quiz_answers(answers: List[QuizAnswer]):
    result = {"quiz_id": answers[0].quiz_id, "score": 0, "correct_answers": []}
    quiz = session.query(Quiz).filter(Quiz.id == result["quiz_id"]).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    for answer in answers:
        question_index = answer.quiz_id - 1

        if question_index >= len(quiz.questions):
            raise HTTPException(status_code=400, detail=f"Invalid quiz_id: {answer.quiz_id}")

        question = quiz.questions[question_index]
        total_options = len(question["options"])

        if not is_valid_option(answer.user_answers[0], total_options):
            raise HTTPException(status_code=400, detail=f"Invalid answer for question {answer.quiz_id}")

        correct_answer = question["options"][0].split(":")[1].strip()
        if answer.user_answers[0] == correct_answer:
            result["score"] += 1
        result["correct_answers"].append(correct_answer)

    return result




@app.get("/result/{quiz_id}", response_model=QuizResult)
def get_quiz_result(quiz_id: int):
    quiz = session.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    total_questions = len(quiz.questions)
    return {
        "quiz_id": quiz_id,
        "score": 0,
        "correct_answers": [question.options[0].split(":")[1].strip() for question in quiz.questions],
    }




def init_db():
    Base.metadata.create_all(bind=engine)
    
    
    sample_quizzes = [
        {
            "name": "Quiz 1",
            "questions": [
                {"statement": "What is the capital of France?", "options": ["A: Paris", "B: London", "C: Berlin", "D: Madrid"]},
                {"statement": "Which planet is known as the Red Planet?", "options": ["A: Mars", "B: Venus", "C: Jupiter", "D: Saturn"]},
                {"statement": "Who wrote 'Romeo and Juliet'?", "options": ["A: William Shakespeare", "B: Charles Dickens", "C: Jane Austen", "D: Mark Twain"]},
            ],
        },
        
    ]

    for quiz_data in sample_quizzes:
        quiz = Quiz(**quiz_data)
        session.add(quiz)

    session.commit()



if __name__ == "__main__":
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=8000)
