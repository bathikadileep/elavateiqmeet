import React, { useState } from 'react';
import meetingsApi from '../../api/meetings';
import GlassCard from '../common/GlassCard';
import Input from '../common/Input';
import Button from '../common/Button';
import { Edit3, X, Save, AlertCircle } from 'lucide-react';
import type { Meeting } from '../../types/meeting';

export interface EditMeetingModalProps {
  meeting: Meeting;
  onClose: () => void;
  onUpdated: (updatedMeeting: Meeting) => void;
}

export const EditMeetingModal: React.FC<EditMeetingModalProps> = ({
  meeting,
  onClose,
  onUpdated,
}) => {
  const [title, setTitle] = useState(meeting.title);
  const [description, setDescription] = useState(meeting.description || '');
  const [maxParticipants, setMaxParticipants] = useState(meeting.max_participants);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    if (!title.trim()) {
      setErrorMsg('Meeting title is required.');
      return;
    }

    setLoading(true);
    try {
      const res = await meetingsApi.update(meeting.id, {
        title: title.trim(),
        description: description.trim(),
        max_participants: Number(maxParticipants),
      });
      onUpdated(res.meeting);
      onClose();
    } catch (err: unknown) {
      const error = err as { message?: string };
      setErrorMsg(error.message || 'Failed to update meeting.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#080911]/80 backdrop-blur-md animate-in fade-in duration-200">
      <GlassCard variant="glow" className="w-full max-w-md p-6 relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-xl hover:bg-white/10 text-gray-400 hover:text-white transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 mb-6">
          <div className="p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            <Edit3 className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">Edit Scheduled Meeting</h3>
            <p className="text-xs text-gray-400">Update session parameters</p>
          </div>
        </div>

        {errorMsg && (
          <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-center gap-2.5 text-rose-300 text-xs">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Meeting Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            disabled={loading}
            required
          />

          <div className="space-y-1.5">
            <label className="block text-xs font-medium text-gray-300 tracking-wide uppercase">
              Description
            </label>
            <textarea
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              disabled={loading}
              className="w-full glass-input rounded-xl text-sm py-2.5 px-4 focus:outline-none"
              placeholder="Brief agenda or instructions..."
            />
          </div>

          <Input
            label="Max Participants"
            type="number"
            min={2}
            max={500}
            value={maxParticipants}
            onChange={(e) => setMaxParticipants(Number(e.target.value))}
            disabled={loading}
            required
          />

          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="ghost" size="sm" onClick={onClose}>
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              isLoading={loading}
              rightIcon={<Save className="w-3.5 h-3.5" />}
            >
              Save Changes
            </Button>
          </div>
        </form>
      </GlassCard>
    </div>
  );
};

export default EditMeetingModal;
