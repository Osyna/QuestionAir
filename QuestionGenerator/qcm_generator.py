import ollama
from typing import List, Optional
from datetime import datetime
import json
import re
from pathlib import Path

from utils.database_manager import DatabaseManager
from utils.qtype import Question
from utils.utilities import read_markdown, scan_folder, format_user_prompt, format_system_prompt
from keyword_extractor import KeywordExtractor
from logging_config import setup_logger


class QCMGenerator:
    def __init__(self, model: str = "llama3.1:latest",
                 embedding_model: str = "nomic-embed-text"):
        self.model = model
        self.db_manager = DatabaseManager('../data/qcm_database.db')
        self.keyword_extractor = KeywordExtractor(embedding_model)
        self.response_pattern = re.compile(
                r'\|\s*([^|]+?)\s*\|\s*(\[[^\]]+\])\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*"QCM"\s*\|\s*({[^}]+})\s*\|\s*(\[[^\]]+\])\s*\|'
                )
        self.logger = setup_logger('qcm_generator')

    def clean_json_string(self, s: str) -> str:
        """Clean and format string for JSON parsing."""
        self.logger.debug(f"Cleaning JSON string: {s}")

        # First, handle French apostrophes and quotes properly
        s = s.replace('"', '\\"')  # Escape existing double quotes
        s = s.replace("'", "\\'")  # Escape single quotes

        # Replace the outer single quotes with double quotes for JSON
        if s.startswith("'") and s.endswith("'"):
            s = f'"{s[1:-1]}"'

        s = s.strip()
        self.logger.debug(f"Cleaned JSON string: {s}")
        return s

    def parse_choices(self, choices_str: str) -> dict:
        """Parse choices string into a dictionary."""
        self.logger.debug(f"Attempting to parse choices: {choices_str}")

        try:
            # First attempt: try direct JSON parsing
            try:
                return json.loads(choices_str)
            except json.JSONDecodeError as e:
                self.logger.debug(f"Direct JSON parsing failed: {str(e)}")

            # Second attempt: clean and try again
            cleaned = choices_str.replace('\\"', '"')
            cleaned = cleaned.replace("\\'", "'")
            cleaned = cleaned.replace("d'", "d'")
            cleaned = cleaned.replace("l'", "l'")

            self.logger.debug(f"Cleaned choices string: {cleaned}")

            try:
                return json.loads(cleaned)
            except json.JSONDecodeError as e:
                self.logger.debug(f"Cleaned JSON parsing failed: {str(e)}")

                # Final attempt: manual parsing
                choices = {}
                parts = cleaned.strip('{}').split('","')

                for part in parts:
                    if ':' in part:
                        key, value = part.split(':', 1)
                        key = key.strip().strip('"')
                        value = value.strip().strip('"')
                        choices[key] = value

                self.logger.debug(f"Manual parsing result: {choices}")
                return choices

        except Exception as e:
            self.logger.error(f"Failed to parse choices: {choices_str}")
            self.logger.error(f"Error details: {str(e)}")
            raise e

    def analyze_md(self, file_path: str) -> Optional[List[Question]]:
        """Analyze markdown file and generate questions."""
        file_name = Path(file_path).name
        self.logger.info(f"Processing file: {file_name}")

        content = read_markdown(file_path)
        if not content or len(content) < 200:
            self.logger.warning(f"File {file_name} is too short or empty")
            return None

        # Extract keywords
        extracted_keywords = self.keyword_extractor.extract_keywords(content, num_keywords = 5)
        self.logger.debug(f"Extracted keywords: {extracted_keywords}")

        prompt = format_user_prompt().format(
                content = content,
                suggested_keywords = ", ".join(extracted_keywords)
                )

        try:
            self.logger.debug("Sending request to LLM")
            response = ollama.chat(model = self.model, messages = [
                {
                    'role':    'system',
                    'content': format_system_prompt()
                    },
                {
                    'role':    'user',
                    'content': prompt
                    }
                ])

            self.logger.debug(f"Raw LLM response: {response['message']['content']}")
            return self.parse_response(response['message']['content'], file_path)

        except Exception as e:
            self.logger.error(f"Error during API call for {file_name}")
            self.logger.error(f"Error details: {str(e)}")
            return None

    def parse_response(self, response: str, source_file: str) -> List[Question]:
        """Parse the LLM response with detailed logging."""
        questions = []
        file_name = Path(source_file).name
        self.logger.info(f"Parsing response for {file_name}")

        # Clean response
        cleaned_response = '\n'.join(line for line in response.split('\n')
                                     if line.strip() and not line.strip().startswith('|-'))

        self.logger.debug(f"Cleaned response:\n{cleaned_response}")
        matches = self.response_pattern.finditer(cleaned_response)

        # Count total matches
        matches = list(matches)
        total_matches = len(matches)
        self.logger.info(f"Found {total_matches} potential questions in response")

        for i, match in enumerate(matches, 1):
            try:
                self.logger.debug(f"Processing question {i}/{total_matches}")
                self.logger.debug(f"Raw match: {match.group(0)}")

                # Parse each component with detailed logging
                subject = match.group(1).strip()
                keywords = self.parse_keywords(match.group(2))
                question_id = match.group(3).strip()
                question_text = match.group(4).strip()

                self.logger.debug(f"Parsed components for question {question_id}:")
                self.logger.debug(f"  Subject: {subject}")
                self.logger.debug(f"  Keywords: {keywords}")
                self.logger.debug(f"  Question: {question_text}")

                try:
                    choices = self.parse_choices(match.group(5))
                    self.logger.debug(f"  Choices: {choices}")
                except Exception as e:
                    self.logger.error(f"Failed to parse choices in question {question_id}")
                    self.logger.error(f"Raw choices: {match.group(5)}")
                    self.logger.error(f"Error: {str(e)}")
                    continue

                answers = self.parse_answers(match.group(6))
                self.logger.debug(f"  Answers: {answers}")

                # Validation with detailed logging
                validation_errors = []
                if len(choices) != 4:
                    validation_errors.append(f"Expected 4 choices, got {len(choices)}")
                if not all(k in choices for k in ['A', 'B', 'C', 'D']):
                    validation_errors.append("Missing required choice keys (A,B,C,D)")
                if len(answers) != 1:
                    validation_errors.append(f"Expected 1 answer, got {len(answers)}")
                elif answers[0] not in ['A', 'B', 'C', 'D']:
                    validation_errors.append(f"Invalid answer: {answers[0]}")

                if validation_errors:
                    self.logger.error(f"Validation failed for question {question_id}:")
                    for error in validation_errors:
                        self.logger.error(f"  - {error}")
                    continue

                question = Question(
                        subject = subject,
                        keywords = keywords,
                        question_id = question_id,
                        question_text = question_text,
                        question_type = "QCM",
                        choices = choices,
                        answers = answers,
                        source_file = source_file,
                        created_at = datetime.now().isoformat()
                        )
                questions.append(question)
                self.logger.info(f"Successfully parsed question {question_id}")

            except Exception as e:
                self.logger.error(f"Error parsing question {i}/{total_matches}")
                self.logger.error(f"Raw match: {match.group(0)}")
                self.logger.error(f"Error details: {str(e)}")
                continue

        if len(questions) != 5:
            self.logger.warning(f"Expected 5 questions, got {len(questions)} for {file_name}")
            self.logger.warning("Questions processed:")
            for q in questions:
                self.logger.warning(f"  - {q.question_id}: {q.question_text}")

        return questions

    def process_folder(self, folder_path: str):
        """Process all markdown files with detailed logging."""
        self.logger.info(f"Starting folder processing: {folder_path}")
        md_files = scan_folder(folder_path)
        total_questions = 0
        processed_files = 0
        failed_files = []

        self.logger.info(f"Found {len(md_files)} markdown files")

        for file_path in md_files:
            file_name = Path(file_path).name
            self.logger.info(f"\nProcessing file: {file_name}")

            questions = self.analyze_md(file_path)

            if questions:
                for question in questions:
                    try:
                        self.db_manager.insert_question(question)
                    except Exception as e:
                        self.logger.error(f"Failed to insert question {question.question_id}")
                        self.logger.error(f"Error details: {str(e)}")
                        continue

                total_questions += len(questions)
                processed_files += 1
                self.logger.info(f"Successfully processed {len(questions)} questions from {file_name}")
            else:
                self.logger.error(f"Failed to process {file_name}")
                failed_files.append(file_name)

        self.logger.info("\nProcessing Summary:")
        self.logger.info(f"Files processed: {processed_files}/{len(md_files)}")
        self.logger.info(f"Total questions generated: {total_questions}")
        if failed_files:
            self.logger.warning("Failed files:")
            for file in failed_files:
                self.logger.warning(f"  - {file}")