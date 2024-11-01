from datetime import datetime
import sqlite3
from typing import List, Dict, Optional


class ProgressTracker:
    def __init__(self, db_path: str = "progress.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS quiz_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    quiz_date TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    score REAL NOT NULL,
                    total_questions INTEGER NOT NULL,
                    correct_answers INTEGER NOT NULL
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS question_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_id INTEGER NOT NULL,
                    times_shown INTEGER DEFAULT 0,
                    times_correct INTEGER DEFAULT 0,
                    last_shown TEXT,
                    difficulty_rating REAL DEFAULT 0.5
                )
            ''')
            conn.commit()

    def record_attempt(self, user_id: str, subject: str,
                       questions: List[int], answers: List[str],
                       correct_answers: List[bool]):
        """Record a quiz attempt and update question statistics."""
        score = sum(correct_answers) / len(questions) * 100

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Record the quiz attempt
            cursor.execute('''
                INSERT INTO quiz_attempts (
                    user_id, quiz_date, subject, score,
                    total_questions, correct_answers
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                datetime.now().isoformat(),
                subject,
                score,
                len(questions),
                sum(correct_answers)
                ))

            # Update question statistics
            for q_id, is_correct in zip(questions, correct_answers):
                cursor.execute('''
                    INSERT INTO question_stats (
                        question_id, times_shown, times_correct,
                        last_shown
                    ) VALUES (?, 1, ?, ?)
                    ON CONFLICT(question_id) DO UPDATE SET
                        times_shown = times_shown + 1,
                        times_correct = times_correct + ?,
                        last_shown = ?
                ''', (
                    q_id,
                    1 if is_correct else 0,
                    datetime.now().isoformat(),
                    1 if is_correct else 0,
                    datetime.now().isoformat()
                    ))

            conn.commit()

    def get_user_progress(self, user_id: str) -> Dict:
        """Get user's progress statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            stats = {
                'total_quizzes':      0,
                'average_score':      0,
                'subjects_taken':     set(),
                'progress_over_time': [],
                'strongest_subject':  None,
                'weakest_subject':    None
                }

            # Get basic stats
            cursor.execute('''
                SELECT COUNT(*), AVG(score)
                FROM quiz_attempts
                WHERE user_id = ?
            ''', (user_id,))
            row = cursor.fetchone()
            stats['total_quizzes'] = row[0]
            stats['average_score'] = row[1] if row[1] else 0

            # Get subject performance
            cursor.execute('''
                SELECT subject, AVG(score)
                FROM quiz_attempts
                WHERE user_id = ?
                GROUP BY subject
            ''', (user_id,))

            subject_scores = {}
            for subject, avg_score in cursor.fetchall():
                subject_scores[subject] = avg_score
                stats['subjects_taken'].add(subject)

            if subject_scores:
                stats['strongest_subject'] = max(subject_scores.items(),
                                                 key = lambda x: x[1])
                stats['weakest_subject'] = min(subject_scores.items(),
                                               key = lambda x: x[1])

            # Get progress over time
            cursor.execute('''
                SELECT quiz_date, score
                FROM quiz_attempts
                WHERE user_id = ?
                ORDER BY quiz_date
            ''', (user_id,))
            stats['progress_over_time'] = cursor.fetchall()

            return stats

    def get_question_recommendations(self, user_id: str,
                                     subject: Optional[str] = None,
                                     limit: int = 10) -> List[int]:
        """Get recommended questions based on difficulty and past performance."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            query = '''
                SELECT 
                    qs.question_id,
                    CAST(qs.times_correct AS FLOAT) / 
                        CASE WHEN qs.times_shown = 0 THEN 1 
                        ELSE qs.times_shown END as success_rate,
                    qs.last_shown
                FROM question_stats qs
                JOIN questions q ON qs.question_id = q.id
                WHERE 1=1
            '''
            params = []

            if subject:
                query += " AND q.subject = ?"
                params.append(subject)

            query += '''
                ORDER BY 
                    CASE 
                        WHEN qs.times_shown = 0 THEN 1
                        WHEN success_rate < 0.3 THEN 2
                        ELSE 3
                    END,
                    RANDOM()
                LIMIT ?
            '''
            params.append(limit)

            cursor.execute(query, params)
            return [row[0] for row in cursor.fetchall()]