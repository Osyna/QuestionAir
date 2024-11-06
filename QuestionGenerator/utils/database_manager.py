import sqlite3
import json
import random
from typing import List, Optional, Dict
from utils.qtype import Question
from datetime import datetime


class DatabaseManager:
    def __init__(self, db_path: str = "qcm_database.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject TEXT NOT NULL,
                    keywords TEXT NOT NULL,
                    question_id TEXT NOT NULL,
                    question_text TEXT NOT NULL,
                    question_type TEXT NOT NULL,
                    choices TEXT NOT NULL,
                    answers TEXT NOT NULL,
                    source_file TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            ''')
            conn.commit()

    def _row_to_question(self, row: tuple) -> Question:
        """Convert a database row to a Question object."""
        return Question(
                subject = row[1],
                keywords = json.loads(row[2]),
                question_id = row[3],
                question_text = row[4],
                question_type = row[5],
                choices = json.loads(row[6]),
                answers = json.loads(row[7]),
                source_file = row[8],
                created_at = row[9]
                )

    def insert_question(self, question: Question):
        """Insert a question into the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO questions (
                    subject, keywords, question_id, question_text,
                    question_type, choices, answers, source_file, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                question.subject,
                json.dumps(question.keywords),
                question.question_id,
                question.question_text,
                question.question_type,
                json.dumps(question.choices),
                json.dumps(question.answers),
                question.source_file,
                question.created_at
                ))
            conn.commit()

    def load_question(self, question_id: int) -> Optional[Question]:
        """Load a specific question by its database ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM questions WHERE id = ?', (question_id,))
            row = cursor.fetchone()
            return self._row_to_question(row) if row else None

    def load_random_question(self, subject: Optional[str] = None,
                             keywords: Optional[List[str]] = None) -> Optional[Question]:
        """Load a random question, optionally filtered by subject and/or keywords."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            query = 'SELECT * FROM questions'
            params = []
            conditions = []

            if subject:
                conditions.append('subject = ?')
                params.append(subject)

            if keywords:
                # Check if any of the provided keywords exist in the keywords JSON array
                keyword_conditions = ' OR '.join(
                        'keywords LIKE ?' for _ in keywords
                        )
                conditions.append(f'({keyword_conditions})')
                params.extend(f'%{k}%' for k in keywords)

            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)

            query += ' ORDER BY RANDOM() LIMIT 1'

            cursor.execute(query, params)
            row = cursor.fetchone()
            return self._row_to_question(row) if row else None

    def load_questions(self, limit: int = 10, offset: int = 0,
                       subject: Optional[str] = None,
                       keywords: Optional[List[str]] = None,
                       shuffle: bool = False) -> List[Question]:
        """Load multiple questions with various filtering options."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            query = 'SELECT * FROM questions'
            params = []
            conditions = []

            if subject:
                conditions.append('subject = ?')
                params.append(subject)

            if keywords:
                keyword_conditions = ' OR '.join(
                        'keywords LIKE ?' for _ in keywords
                        )
                conditions.append(f'({keyword_conditions})')
                params.extend(f'%{k}%' for k in keywords)

            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)

            if shuffle:
                query += ' ORDER BY RANDOM()'
            else:
                query += ' ORDER BY created_at DESC'

            query += ' LIMIT ? OFFSET ?'
            params.extend([limit, offset])

            cursor.execute(query, params)
            return [self._row_to_question(row) for row in cursor.fetchall()]

    def get_subjects(self) -> List[str]:
        """Get list of all unique subjects in the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT subject FROM questions ORDER BY subject')
            return [row[0] for row in cursor.fetchall()]

    def get_keywords(self) -> List[str]:
        """Get list of all unique keywords in the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT keywords FROM questions')
            keywords_set = set()
            for row in cursor.fetchall():
                keywords = json.loads(row[0])
                keywords_set.update(keywords)
            return sorted(list(keywords_set))

    def get_stats(self) -> Dict:
        """Get database statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            stats = {
                'total_questions':       cursor.execute('SELECT COUNT(*) FROM questions').fetchone()[0],
                'total_subjects':        cursor.execute('SELECT COUNT(DISTINCT subject) FROM questions').fetchone()[0],
                'questions_per_subject': {},
                'latest_question':       cursor.execute(
                    'SELECT created_at FROM questions ORDER BY created_at DESC LIMIT 1').fetchone()[0],
                'total_keywords':        len(self.get_keywords())
                }

            # Get questions count per subject
            cursor.execute('SELECT subject, COUNT(*) FROM questions GROUP BY subject')
            stats['questions_per_subject'] = dict(cursor.fetchall())

            return stats

    def search_questions(self, query: str) -> List[Question]:
        """Search questions by text content."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM questions 
                WHERE question_text LIKE ? 
                   OR subject LIKE ? 
                   OR keywords LIKE ?
                ORDER BY created_at DESC
            ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
            return [self._row_to_question(row) for row in cursor.fetchall()]