import React, { useState } from 'react';
import client from '../../api/client';

interface QAQuestion {
  id: string;
  participant_name: string;
  question: string;
  upvotes: number;
  is_approved: boolean;
  is_answered: boolean;
  answer_text?: string;
}

interface WebinarQAWidgetProps {
  roomCode: string;
  speakerName: string;
}

export const WebinarQAWidget: React.FC<WebinarQAWidgetProps> = ({ roomCode, speakerName }) => {
  const [questions, setQuestions] = useState<QAQuestion[]>([]);
  const [newQuestion, setNewQuestion] = useState('');

  const handleAskQuestion = async () => {
    if (!newQuestion.trim()) return;
    try {
      const res = await client.post('/api/webinar/qa/ask', {
        room_code: roomCode,
        question: newQuestion,
        speaker_name: speakerName,
      });
      if (res.data) {
        setQuestions((prev) => [...prev, res.data]);
        setNewQuestion('');
      }
    } catch (err) {
      console.error('Failed submitting Q&A question:', err);
    }
  };

  const handleUpvote = async (questionId: string) => {
    try {
      const res = await client.post('/api/webinar/qa/upvote', {
        room_code: roomCode,
        question_id: questionId,
      });
      if (res.data) {
        setQuestions((prev) =>
          prev.map((q) => (q.id === questionId ? { ...q, upvotes: res.data.upvotes } : q))
        );
      }
    } catch (err) {
      console.error('Failed upvoting question:', err);
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#0d0e19] border-l border-cyan-500/20 text-white p-4">
      <h3 className="text-md font-bold text-cyan-400 mb-3">💬 Webinar Q&A Queue</h3>

      <div className="flex-1 overflow-y-auto space-y-3 pr-1">
        {questions.length === 0 ? (
          <p className="text-xs text-gray-500 italic">No questions submitted yet. Be the first to ask!</p>
        ) : (
          questions.map((q) => (
            <div key={q.id} className="p-3 bg-[#16182a] rounded-xl border border-cyan-500/10 flex items-start justify-between">
              <div>
                <p className="text-xs font-semibold text-cyan-300">{q.participant_name}</p>
                <p className="text-xs text-gray-200 mt-1">{q.question}</p>
                {q.is_answered && (
                  <p className="text-xs text-green-400 mt-2 bg-green-950/40 p-2 rounded">
                    <strong>Answer:</strong> {q.answer_text}
                  </p>
                )}
              </div>
              <button
                onClick={() => handleUpvote(q.id)}
                className="flex items-center gap-1 text-xs px-2 py-1 bg-cyan-950/60 hover:bg-cyan-900 border border-cyan-500/30 rounded text-cyan-300 transition"
              >
                ▲ {q.upvotes}
              </button>
            </div>
          ))
        )}
      </div>

      <div className="mt-3 flex gap-2">
        <input
          type="text"
          placeholder="Ask a question..."
          value={newQuestion}
          onChange={(e) => setNewQuestion(e.target.value)}
          className="flex-1 text-xs bg-slate-900 border border-cyan-500/30 rounded-lg p-2 text-white focus:outline-none focus:border-cyan-400"
        />
        <button
          onClick={handleAskQuestion}
          className="text-xs font-semibold bg-cyan-500 hover:bg-cyan-400 text-slate-950 px-3 py-2 rounded-lg transition"
        >
          Ask
        </button>
      </div>
    </div>
  );
};
