import React, { useState, useEffect, useCallback } from 'react';
import { X, Vote, Plus, BarChart2, CheckCircle2, Lock } from 'lucide-react';
import client from '../../api/client';
import type { PollItem } from '../../types/collaboration';
import PollCreateModal from './PollCreateModal';
import PollResultsVisualization from './PollResultsVisualization';

export interface PollModalProps {
  isOpen: boolean;
  onClose: () => void;
  roomCode: string;
}

export const PollModal: React.FC<PollModalProps> = ({ isOpen, onClose, roomCode }) => {
  const [polls, setPolls] = useState<PollItem[]>([]);
  const [selectedOptions, setSelectedOptions] = useState<Record<string, string[]>>({});
  const [createOpen, setCreateOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [expandedAnalyticsPollId, setExpandedAnalyticsPollId] = useState<string | null>(null);

  const fetchPolls = useCallback(async () => {
    try {
      setLoading(true);
      const res = await client.get<PollItem[]>(`/api/polls/meeting/${roomCode}`);
      setPolls(res.data);
    } catch (err) {
      console.warn('Failed to fetch polls:', err);
    } finally {
      setLoading(false);
    }
  }, [roomCode]);

  useEffect(() => {
    if (isOpen) {
      fetchPolls();
    }
  }, [isOpen, fetchPolls]);

  if (!isOpen) return null;

  const handleToggleOption = (pollId: string, optionId: string, isMultiselect: boolean) => {
    setSelectedOptions((prev) => {
      const current = prev[pollId] || [];
      if (isMultiselect) {
        const next = current.includes(optionId) ? current.filter((id) => id !== optionId) : [...current, optionId];
        return { ...prev, [pollId]: next };
      }
      return { ...prev, [pollId]: [optionId] };
    });
  };

  const handleVote = async (pollId: string, isMultiselect: boolean) => {
    const selected = selectedOptions[pollId] || [];
    if (selected.length === 0) return;

    try {
      await client.post(`/api/polls/${pollId}/vote`, {
        option_ids: selected,
      });
      fetchPolls();
    } catch (err) {
      console.warn('Failed to submit vote:', err);
    }
  };

  const handlePublish = async (pollId: string) => {
    try {
      await client.post(`/api/polls/${pollId}/publish`, {});
      fetchPolls();
    } catch (err) {
      console.warn('Failed to publish poll:', err);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-xl max-h-[85vh] rounded-3xl glass-card border border-white/10 bg-[#0c0e1a]/95 p-6 text-white shadow-2xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-white/10 mb-4">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-2xl bg-indigo-500/20 border border-indigo-500/30 text-indigo-400">
              <Vote className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white tracking-tight">Live Meeting Polls</h2>
              <p className="text-xs text-gray-400">Interactive voting and real-time analytics</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setCreateOpen(true)}
              className="px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition-colors flex items-center gap-1.5 shadow-lg shadow-indigo-600/30 cursor-pointer"
            >
              <Plus className="w-4 h-4" /> Create Poll
            </button>

            <button
              onClick={onClose}
              className="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Poll List Body */}
        <div className="flex-1 overflow-y-auto pr-1 space-y-4">
          {loading ? (
            <div className="text-center py-12 text-sm text-gray-400">Loading polls...</div>
          ) : polls.length === 0 ? (
            <div className="text-center py-12 text-gray-400">
              <BarChart2 className="w-12 h-12 mx-auto text-gray-600 mb-3 stroke-[1.5]" />
              <p className="text-sm font-semibold">No polls created yet</p>
              <p className="text-xs text-gray-500 mt-1">Click "Create Poll" to start a live voting session</p>
            </div>
          ) : (
            polls.map((poll) => (
              <div key={poll.id} className="p-4 rounded-2xl bg-white/5 border border-white/10 space-y-3">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="text-sm font-bold text-white">{poll.question}</h3>
                    <span className="text-[10px] text-gray-400 font-medium">
                      {poll.is_multiselect ? 'Multi-choice' : 'Single choice'} • {poll.total_votes} Total Votes
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setExpandedAnalyticsPollId(expandedAnalyticsPollId === poll.id ? null : poll.id)}
                      className="px-2.5 py-1 rounded-xl bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 text-xs font-semibold flex items-center gap-1.5 border border-indigo-500/30 transition"
                    >
                      <BarChart2 className="w-3.5 h-3.5" />
                      {expandedAnalyticsPollId === poll.id ? 'Hide Charts' : 'Analytics'}
                    </button>
                    {poll.is_published ? (
                      <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-[10px] font-semibold flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" /> Published
                      </span>
                    ) : (
                      <button
                        onClick={() => handlePublish(poll.id)}
                        className="px-2.5 py-1 rounded-xl bg-white/10 hover:bg-white/20 text-indigo-300 text-xs font-semibold cursor-pointer"
                      >
                        Publish Results
                      </button>
                    )}
                  </div>
                </div>

                {expandedAnalyticsPollId === poll.id ? (
                  <div className="pt-2">
                    <PollResultsVisualization poll={poll} onRefresh={fetchPolls} />
                  </div>
                ) : (
                  <>

                {/* Option Voting list */}
                <div className="space-y-2 pt-1">
                  {poll.options.map((opt) => {
                    const selected = (selectedOptions[poll.id] || []).includes(opt.id);
                    const percentage = poll.total_votes > 0 ? Math.round((opt.vote_count / poll.total_votes) * 100) : 0;

                    return (
                      <div
                        key={opt.id}
                        onClick={() => !poll.is_closed && handleToggleOption(poll.id, opt.id, poll.is_multiselect)}
                        className={`relative p-3 rounded-xl border transition-all cursor-pointer overflow-hidden ${
                          selected ? 'bg-indigo-600/30 border-indigo-500' : 'bg-white/5 border-white/10 hover:border-white/20'
                        }`}
                      >
                        {/* Progress Bar overlay */}
                        <div
                          className="absolute inset-y-0 left-0 bg-indigo-500/15 transition-all duration-500 pointer-events-none"
                          style={{ width: `${percentage}%` }}
                        />

                        <div className="relative z-10 flex items-center justify-between text-xs">
                          <span className="font-semibold text-white">{opt.option_text}</span>
                          <span className="font-bold text-indigo-300">{percentage}% ({opt.vote_count})</span>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {!poll.is_closed && (
                  <div className="pt-2 flex justify-end">
                    <button
                      onClick={() => handleVote(poll.id, poll.is_multiselect)}
                      className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs cursor-pointer shadow-md"
                    >
                      Submit Vote
                    </button>
                  </div>
                )}
                  </>
                )}
              </div>
            ))
          )}
        </div>

        <PollCreateModal
          isOpen={createOpen}
          onClose={() => setCreateOpen(false)}
          roomCode={roomCode}
          onPollCreated={fetchPolls}
        />
      </div>
    </div>
  );
};

export default PollModal;
