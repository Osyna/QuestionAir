from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
import uvicorn

from utils.database_manager import DatabaseManager

app = FastAPI(title="QCM API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = DatabaseManager('../data/qcm_database.db')

class QuestionResponse(BaseModel):
    id: int
    subject: str
    question_text: str
    choices: dict
    answers: List[str]

@app.get("/subjects")
async def get_subjects():
    return db.get_subjects()

@app.get("/keywords")
async def get_keywords():
    return db.get_keywords()

@app.get("/questions/random")
async def get_random_question(
    subject: Optional[str] = None,
    keywords: Optional[List[str]] = Query(None)
):
    question = db.load_random_question(subject, keywords)
    if not question:
        raise HTTPException(status_code=404, detail="No matching questions found")
    return question

@app.get("/quiz/generate")
async def generate_quiz(
    num_questions: int = Query(10, gt=0, le=50),
    subject: Optional[str] = None,
    keywords: Optional[List[str]] = Query(None),
    shuffle: bool = True
):
    questions = db.load_questions(
        limit=num_questions,
        subject=subject,
        keywords=keywords,
        shuffle=shuffle
    )
    return questions

@app.get("/stats")
async def get_stats():
    return db.get_stats()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)