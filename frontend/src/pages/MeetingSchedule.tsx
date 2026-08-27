import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import meetingsApi from '../api/meetings';
import GlassCard from '../components/common/GlassCard';
import Input from '../components/common/Input';
import Button from '../components/common/Button';
import { Calendar, Plus, Video, Lock, Users, AlertCircle, ArrowLeft } from 'lucide-react';

export const MeetingSchedule: React.FC = () => {
  const navigate = useNavigate();

  const [meetingType, setMeetingType] = useState<'instant' | 'scheduled'>('scheduled');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [scheduledStart, setScheduledStart] = useState('');
  const [maxParticipants, setMaxParticipants] = useState(50);
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    setLoading(true);
    try {
      const res = await meetingsApi.create({
        title: title.trim() || undefined,
        description: description.trim() || undefined,
        meeting_type: meetingType,
        scheduled_start: meetingType === 'scheduled' && scheduledStart ? new Date(scheduledStart).toISOString() : undefined,
        max_participants: Number(maxParticipants),
        password: password || undefined,
      });

      if (meetingType === 'instant') {
        navigate(`/room/${res.meeting.meeting_code}`);
      } else {
        navigate('/history');
      }
    } catch (err: unknown) {
      const error = err as { message?: string };
      setErrorMsg(error.message || 'Failed to create meeting.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Top Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate(-1)}
            className="p-2 rounded-xl hover:bg-white/10 text-gray-400 hover:text-white transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-black text-white">Create New Meeting</h1>
            <p className="text-xs text-gray-400">Launch an instant session or schedule for later</p>
          </div>
        </div>
      </div>

      <GlassCard variant="glow" className="p-8">
        {/* Type Toggle Tabs */}
        <div className="grid grid-cols-2 gap-3 p-1.5 rounded-xl bg-white/[0.03] border border-white/10 mb-6">
          <button
            type="button"
            onClick={() => setMeetingType('scheduled')}
            className={`flex items-center justify-center gap-2 py-2.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              meetingType === 'scheduled'
                ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-md'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <Calendar className="w-4 h-4" />
            Schedule for Later
          </button>

          <button
            type="button"
            onClick={() => setMeetingType('instant')}
            className={`flex items-center justify-center gap-2 py-2.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              meetingType === 'instant'
                ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-md'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <Video className="w-4 h-4" />
            Instant Meeting
          </button>
        </div>

        {/* Error Alert */}
        {errorMsg && (
          <div className="mb-6 p-3.5 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-center gap-3 text-rose-300 text-xs">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Meeting Title"
            placeholder="e.g. Q3 Strategic Planning Sync"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            disabled={loading}
          />

          <div className="space-y-1.5">
            <label className="block text-xs font-medium text-gray-300 tracking-wide uppercase">
              Description / Agenda
            </label>
            <textarea
              rows={3}
              placeholder="Provide context or instructions for participants..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              disabled={loading}
              className="w-full glass-input rounded-xl text-sm py-2.5 px-4 focus:outline-none"
            />
          </div>

          {meetingType === 'scheduled' && (
            <Input
              label="Scheduled Start Time"
              type="datetime-local"
              value={scheduledStart}
              onChange={(e) => setScheduledStart(e.target.value)}
              disabled={loading}
              required
            />
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Max Participants Cap"
              type="number"
              min={2}
              max={500}
              value={maxParticipants}
              onChange={(e) => setMaxParticipants(Number(e.target.value))}
              disabled={loading}
              leftIcon={<Users className="w-4 h-4" />}
            />

            <Input
              label="Room Password (Optional)"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
              leftIcon={<Lock className="w-4 h-4" />}
            />
          </div>

          <div className="pt-4 flex justify-end">
            <Button
              type="submit"
              variant="primary"
              size="lg"
              isLoading={loading}
              rightIcon={meetingType === 'instant' ? <Video className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
            >
              {meetingType === 'instant' ? 'Start Instant Meeting Now' : 'Schedule Meeting'}
            </Button>
          </div>
        </form>
      </GlassCard>
    </div>
  );
};

export default MeetingSchedule;
