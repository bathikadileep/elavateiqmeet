import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import meetingsApi from '../../api/meetings';
import GlassCard from '../common/GlassCard';
import Button from '../common/Button';
import Badge from '../common/Badge';
import { Video, Plus, ArrowRight, Radio, CalendarCheck, Copy, Check } from 'lucide-react';
import type { Meeting } from '../../types/meeting';

export interface TodaysMeetingsWidgetProps {
  meetings: Meeting[];
  onMeetingCreated?: () => void;
}

export const TodaysMeetingsWidget: React.FC<TodaysMeetingsWidgetProps> = ({
  meetings,
  onMeetingCreated,
}) => {
  const navigate = useNavigate();
  const [instantLoading, setInstantLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const handleStartInstant = async () => {
    setInstantLoading(true);
    try {
      const res = await meetingsApi.create({
        title: 'Instant Meeting',
        meeting_type: 'instant',
      });
      if (onMeetingCreated) onMeetingCreated();
      navigate(`/room/${res.meeting.meeting_code}`);
    } catch (err) {
      console.error('Failed to create instant meeting:', err);
    } finally {
      setInstantLoading(false);
    }
  };

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
          <div className="p-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            <CalendarCheck className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Today's Schedule</h3>
            <p className="text-xs text-gray-400">Active and upcoming meetings for today</p>
          </div>
        </div>

        <Button
          variant="primary"
          size="sm"
          isLoading={instantLoading}
          onClick={handleStartInstant}
          leftIcon={<Plus className="w-4 h-4" />}
        >
          Instant Meeting
        </Button>
      </div>

      {/* List */}
      <div className="flex-1 space-y-3 overflow-y-auto max-h-[340px] pr-1">
        {meetings.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-10 text-center text-gray-400 space-y-2">
            <Video className="w-10 h-10 text-gray-600 stroke-1" />
            <p className="text-xs">No meetings scheduled for today.</p>
            <Button
              variant="secondary"
              size="sm"
              isLoading={instantLoading}
              onClick={handleStartInstant}
              leftIcon={<Plus className="w-3.5 h-3.5" />}
            >
              Start Instant Meeting
            </Button>
          </div>
        ) : (
          meetings.map((meeting) => {
            const isLive = meeting.status === 'live';
            const joinUrl = `${window.location.origin}/room/${meeting.meeting_code}`;
            const isCopied = copiedId === meeting.id;

            return (
              <div
                key={meeting.id}
                className="p-3.5 rounded-xl glass-card hover:border-indigo-500/30 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3"
              >
                <div className="flex items-center gap-3">
                  <div className={`p-2.5 rounded-xl ${isLive ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' : 'bg-white/5 text-gray-400'}`}>
                    {isLive ? <Radio className="w-5 h-5 animate-pulse" /> : <Video className="w-5 h-5" />}
                  </div>

                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="text-sm font-semibold text-white">{meeting.title}</h4>
                      {isLive && (
                        <Badge variant="danger" size="sm" pulse>
                          LIVE
                        </Badge>
                      )}
                    </div>

                    {/* Full Meeting Link Display */}
                    <div className="flex items-center gap-1.5 mt-1 text-[11px] font-mono text-gray-400">
                      <span className="text-indigo-300 font-semibold">{joinUrl}</span>
                      <button
                        type="button"
                        onClick={() => handleCopyLink(meeting.meeting_code, meeting.id)}
                        className="p-1 rounded hover:bg-white/10 text-gray-400 hover:text-white transition-colors cursor-pointer"
                        title="Copy Meeting Link"
                      >
                        {isCopied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      </button>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Button
                    variant={isCopied ? 'glass' : 'ghost'}
                    size="sm"
                    onClick={() => handleCopyLink(meeting.meeting_code, meeting.id)}
                    leftIcon={isCopied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  >
                    {isCopied ? 'Copied' : 'Copy Link'}
                  </Button>

                  <Button
                    variant={isLive ? 'danger' : 'secondary'}
                    size="sm"
                    onClick={() => navigate(`/room/${meeting.meeting_code}`)}
                    rightIcon={<ArrowRight className="w-3.5 h-3.5" />}
                  >
                    {isLive ? 'Join Live' : 'Enter'}
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

export default TodaysMeetingsWidget;
