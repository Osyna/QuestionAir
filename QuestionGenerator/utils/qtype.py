from typing import List, Dict
from dataclasses import dataclass

@dataclass
class Question:
    subject: str
    keywords: List[str]
    question_id: str
    question_text: str
    question_type: str
    choices: Dict[str, str]
    answers: List[str]
    source_file: str
    created_at: str
