'use client';

import { useEffect, useState } from 'react';
import axios from 'axios';

interface SubjectSelectorProps {
  selectedSubject: string | null;
  onSubjectSelect: (subject: string) => void;
}

export function SubjectSelector({ selectedSubject, onSubjectSelect }: SubjectSelectorProps) {
  const [subjects, setSubjects] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSubjects = async () => {
      try {
        const response = await axios.get('http://localhost:8000/subjects');
        setSubjects(response.data);
      } catch (err) {
        setError('Failed to load subjects');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSubjects();
  }, []);

  if (isLoading) return <div>Loading subjects...</div>;
  if (error) return <div className="text-red-500">{error}</div>;

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium mb-2">
        Select a subject:
      </label>
      <select
        value={selectedSubject || ''}
        onChange={(e) => onSubjectSelect(e.target.value)}
        className="w-full p-2 border rounded-lg bg-white"
      >
        <option value="">Choose a subject...</option>
        {subjects.map((subject) => (
          <option key={subject} value={subject}>
            {subject}
          </option>
        ))}
      </select>
    </div>
  );
}