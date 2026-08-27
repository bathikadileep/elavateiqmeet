import React, { useState, useEffect, useCallback } from 'react';
import { X, Bot, Sparkles, CheckCircle2, ListTodo, Download, RefreshCw, Smile } from 'lucide-react';
import client from '../../api/client';
import type { MeetingSummaryItem } from '../../types/ai';

export interface AISummaryModalProps {
  isOpen: boolean;
  onClose: () => void;
  roomCode: string;
}

export const AISummaryModal: React.FC<AISummaryModalProps> = ({ isOpen, onClose, roomCode }) => {
  const [summary, setSummary] = useState<MeetingSummaryItem | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchSummary = useCallback(async () => {
    try {
      setLoading(true);
      const res = await client.get<MeetingSummaryItem>(`/api/summaries/meeting/${roomCode}`);
      setSummary(res.data);
    } catch (err) {
      // Summary not generated yet, attempt auto-generating
      handleGenerate();
    } finally {
      setLoading(false);
    }
  }, [roomCode]);

  const handleGenerate = async () => {
    try {
      setLoading(true);
      const res = await client.post<MeetingSummaryItem>('/api/summaries/generate', {
        meeting_code: roomCode,
      });
      setSummary(res.data);
    } catch (err) {
      console.warn('Failed generating summary:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchSummary();
    }
  }, [isOpen, fetchSummary]);

  if (!isOpen) return null;

  const downloadReport = () => {
    if (!summary) return;
    const textContent = `
ELEVATEIQ AI MEETING SUMMARY REPORT
Meeting Code: ${summary.meeting_code}
Generated At: ${new Date(summary.generated_at).toLocaleString()}
Sentiment Score: ${summary.sentiment_score.toUpperCase()} (${summary.sentiment_value})

---------------------------------------------------------
EXECUTIVE SUMMARY:
${summary.executive_summary}

---------------------------------------------------------
KEY DECISIONS MADE:
${summary.key_decisions.map((d, i) => `${i + 1}. ${d}`).join('\n')}

---------------------------------------------------------
ACTION ITEMS & TASKS:
${summary.action_items.map((a, i) => `${i + 1}. [${a.assigned_to}] ${a.task_description} (Due: ${a.due_date || 'N/A'})`).join('\n')}
    `.trim();

    const blob = new Blob([textContent], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `elevateiq-ai-summary-${roomCode}.txt`;
    link.click();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-2xl max-h-[85vh] rounded-3xl glass-card border border-white/10 bg-[#080911]/95 p-6 text-white shadow-2xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-white/10 mb-4">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-2xl bg-indigo-500/20 border border-indigo-500/30 text-indigo-400">
              <Bot className="w-6 h-6 animate-bounce" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
                AI Meeting Intelligence Assistant
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  LLM / NLP Powered
                </span>
              </h2>
              <p className="text-xs text-gray-400">Automated summaries, key decisions, and task analytics</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleGenerate}
              disabled={loading}
              title="Regenerate AI Summary"
              className="p-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white transition-colors cursor-pointer"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>

            <button
              onClick={downloadReport}
              disabled={!summary}
              title="Download Report"
              className="px-3 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs flex items-center gap-1.5 shadow-lg cursor-pointer"
            >
              <Download className="w-4 h-4" /> Download
            </button>

            <button
              onClick={onClose}
              className="p-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto pr-1 space-y-4">
          {loading ? (
            <div className="py-16 text-center space-y-3">
              <Sparkles className="w-10 h-10 text-indigo-400 animate-spin mx-auto" />
              <p className="text-sm font-semibold text-gray-300">Analyzing meeting transcript with AI...</p>
            </div>
          ) : !summary ? (
            <div className="py-16 text-center text-gray-400">
              <Bot className="w-12 h-12 text-gray-600 mx-auto mb-2" />
              <p className="text-sm font-semibold">No transcript generated yet</p>
              <p className="text-xs text-gray-500 mt-1">Enable Subtitles (CC) during the call to record live transcripts</p>
            </div>
          ) : (
            <>
              {/* Executive Summary Card */}
              <div className="p-4 rounded-2xl bg-white/5 border border-white/10 space-y-2">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
                    <Sparkles className="w-4 h-4 text-indigo-400" /> Executive Summary
                  </h3>
                  <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-[10px] font-bold">
                    <Smile className="w-3.5 h-3.5" /> {summary.sentiment_score.toUpperCase()} SENTIMENT ({summary.sentiment_value})
                  </div>
                </div>
                <p className="text-sm text-gray-200 leading-relaxed">{summary.executive_summary}</p>
              </div>

              {/* Key Decisions */}
              <div className="p-4 rounded-2xl bg-white/5 border border-white/10 space-y-2">
                <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Key Decisions Made
                </h3>
                <ul className="space-y-1.5 text-xs text-gray-300">
                  {summary.key_decisions.map((decision, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 flex-shrink-0" />
                      <span>{decision}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Action Items */}
              <div className="p-4 rounded-2xl bg-white/5 border border-white/10 space-y-2">
                <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
                  <ListTodo className="w-4 h-4 text-amber-400" /> Action Items & Tasks
                </h3>
                <div className="space-y-2">
                  {summary.action_items.map((item) => (
                    <div key={item.id} className="p-3 rounded-xl bg-white/5 border border-white/10 flex items-center justify-between text-xs">
                      <div>
                        <p className="font-semibold text-white">{item.task_description}</p>
                        <span className="text-[10px] text-gray-400">Assigned to: <strong className="text-indigo-300">{item.assigned_to}</strong></span>
                      </div>
                      <span className="px-2 py-0.5 rounded-md bg-amber-500/20 text-amber-300 text-[10px] font-bold">
                        {item.due_date || 'Next Sprint'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default AISummaryModal;
