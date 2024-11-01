'use client';

import { useState } from 'react';
import { Quiz } from '@/components/Quiz';
import { SubjectSelector } from '@/components/SubjectSelector';

export default function Home() {
  const [selectedSubject, setSelectedSubject] = useState<string | null>(null);
  const [isQuizStarted, setIsQuizStarted] = useState(false);

  const handleStartQuiz = () => {
    if (selectedSubject) {
      setIsQuizStarted(true);
    }
  };

  const handleReset = () => {
    setIsQuizStarted(false);
    setSelectedSubject(null);
  };

  return (
    <main className="min-h-screen p-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold text-center mb-8">QCM Quiz</h1>
        
        {!isQuizStarted ? (
          <div className="space-y-4">
            <SubjectSelector 
              selectedSubject={selectedSubject}
              onSubjectSelect={setSelectedSubject}
            />
            <button
              onClick={handleStartQuiz}
              disabled={!selectedSubject}
              className="w-full bg-blue-500 text-white p-3 rounded-lg disabled:opacity-50"
            >
              Start Quiz
            </button>
          </div>
        ) : (
          <Quiz 
            subject={selectedSubject!}
            onFinish={handleReset}
          />
        )}
      </div>
    </main>
  );
}