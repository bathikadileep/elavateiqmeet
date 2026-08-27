import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import GlassCard from '../common/GlassCard';
import Button from '../common/Button';
import { Calendar, ArrowRight, Copy, Check } from 'lucide-react';
import type { Meeting } from '../../types/meeting';

export interface UpcomingMeetingsWidgetProps {
  meetings: Meeting[];
}

export const UpcomingMeetingsWidget: React.FC<UpcomingMeetingsWidgetProps> = ({ meetings }) => {
  const navigate = useNavigate();
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const handleCopyLink = (code: string, id: string) => {
    const link = `${window.location.origin}/room/${code}`;
    navigator.clipboard.writeText(link);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <GlassCard variant="default" className="flex flex-col h-full space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/10 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400">
            <Calendar className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Upcoming Sessions</h3>
            <p className="text-xs text-gray-400">Scheduled future meetings</p>
          </div>
        </div>

        <Button variant="ghost" size="sm" onClick={() => navigate('/history')}>
          View All
        </Button>
      </div>

      {/* List */}
      <div className="flex-1 space-y-3 overflow-y-auto max-h-[340px] pr-1">
        {meetings.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-10 text-center text-gray-400 space-y-2">
            <Calendar className="w-10 h-10 text-gray-600 stroke-1" />
            <p className="text-xs">No upcoming sessions scheduled.</p>
          </div>
        ) : (
          meetings.map((m) => {
            const joinUrl = `${window.location.origin}/room/${m.meeting_code}`;
            const isCopied = copiedId === m.id;

            return (
              <div
                key={m.id}
                className="p-3.5 rounded-xl glass-card hover:border-purple-500/30 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-xl bg-white/5 text-purple-400 border border-white/10">
                    <Calendar className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-white">{m.title}</h4>
                    <div className="flex items-center gap-1.5 mt-1 text-[11px] font-mono text-gray-400">
                      <span className="text-purple-300 font-semibold">{joinUrl}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Button
                    variant={isCopied ? 'glass' : 'ghost'}
                    size="sm"
                    onClick={() => handleCopyLink(m.meeting_code, m.id)}
                    leftIcon={isCopied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  >
                    {isCopied ? 'Copied' : 'Copy Link'}
                  </Button>

                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => navigate(`/room/${m.meeting_code}`)}
                    rightIcon={<ArrowRight className="w-3.5 h-3.5" />}
                  >
                    Enter
                  </Button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </GlassCard>
  );
};

export default UpcomingMeetingsWidget;
