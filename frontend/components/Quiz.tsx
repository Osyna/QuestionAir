'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';

interface Question {
  id: number;
  subject: string;
  question_text: string;
  choices: Record<string, string>;
  answers: string[];
}

interface QuizProps {
  subject: string;
  onFinish: () => void;
}

export function Quiz({ subject, onFinish }: QuizProps) {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, string>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [showResults, setShowResults] = useState(false);
  const [score, setScore] = useState(0);

  useEffect(() => {
    const fetchQuestions = async () => {
      try {
        const response = await axios.get(`http://localhost:8000/quiz/generate`, {
          params: {
            subject,
            num_questions: 5
          }
        });
        setQuestions(response.data);
      } catch (error) {
        console.error('Failed to fetch questions:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchQuestions();
  }, [subject]);

  const handleAnswerSelect = (answerId: string) => {
    setSelectedAnswers(prev => ({
      ...prev,
      [questions[currentQuestionIndex].id]: answerId
    }));
  };

  const handleNext = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
    } else {
      calculateScore();
      setShowResults(true);
    }
  };

  const calculateScore = () => {
    const correctAnswers = questions.reduce((count, question) => {
      const selectedAnswer = selectedAnswers[question.id];
      return count + (selectedAnswer === question.answers[0] ? 1 : 0);
    }, 0);
    setScore((correctAnswers / questions.length) * 100);
  };

  if (isLoading) return <div>Loading questions...</div>;

  if (showResults) {
    return (
      <div className="space-y-4">
        <h2 className="text-2xl font-bold text-center">Quiz Results</h2>
        <p className="text-xl text-center">Your score: {score.toFixed(1)}%</p>
        <div className="text-center">
          <button
            onClick={onFinish}
            className="bg-blue-500 text-white px-4 py-2 rounded-lg"
          >
            Start New Quiz
          </button>
        </div>
      </div>
    );
  }

  const currentQuestion = questions[currentQuestionIndex];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold">Question {currentQuestionIndex + 1}/{questions.length}</h2>
        <span>Subject: {subject}</span>
      </div>

      <div className="border rounded-lg p-4 space-y-4">
        <p className="text-lg">{currentQuestion.question_text}</p>

        <div className="space-y-2">
          {Object.entries(currentQuestion.choices).map(([key, value]) => (
            <button
              key={key}
              onClick={() => handleAnswerSelect(key)}
              className={`w-full p-3 text-left rounded-lg border ${
                selectedAnswers[currentQuestion.id] === key
                  ? 'bg-blue-100 border-blue-500'
                  : 'hover:bg-gray-50'
              }`}
            >
              {key}. {value}
            </button>
          ))}
        </div>

        <button
          onClick={handleNext}
          disabled={!selectedAnswers[currentQuestion.id]}
          className="w-full bg-blue-500 text-white p-3 rounded-lg disabled:opacity-50"
        >
          {currentQuestionIndex === questions.length - 1 ? 'Finish Quiz' : 'Next Question'}
        </button>
      </div>
    </div>
  );
}