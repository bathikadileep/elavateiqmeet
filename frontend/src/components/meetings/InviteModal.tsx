import React, { useState } from 'react';
import meetingsApi from '../../api/meetings';
import GlassCard from '../common/GlassCard';
import Input from '../common/Input';
import Button from '../common/Button';
import { UserPlus, X, Copy, Check, Send, AlertCircle, CheckCircle2 } from 'lucide-react';
import type { Meeting } from '../../types/meeting';

export interface InviteModalProps {
  meeting: Meeting;
  onClose: () => void;
}

export const InviteModal: React.FC<InviteModalProps> = ({ meeting, onClose }) => {
  const [emailInput, setEmailInput] = useState('');
  const [usernameInput, setUsernameInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const joinUrl = `${window.location.origin}/room/${meeting.meeting_code}`;

  const handleCopyLink = () => {
    navigator.clipboard.writeText(joinUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSendInvites = async (e: React.FormEvent) => {
    e.preventDefault();
    setSuccessMsg(null);
    setErrorMsg(null);

    const emails = emailInput.split(',').map((s) => s.trim()).filter(Boolean);
    const usernames = usernameInput.split(',').map((s) => s.trim()).filter(Boolean);

    if (emails.length === 0 && usernames.length === 0) {
      setErrorMsg('Please enter at least one email address or username to invite.');
      return;
    }

    setLoading(true);
    try {
      const res = await meetingsApi.invite(meeting.id, { emails, usernames });
      setSuccessMsg(res.message);
      setEmailInput('');
      setUsernameInput('');
    } catch (err: unknown) {
      const error = err as { message?: string };
      setErrorMsg(error.message || 'Failed to send invitations.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#080911]/80 backdrop-blur-md animate-in fade-in duration-200">
      <GlassCard variant="glow" className="w-full max-w-lg p-6 relative">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-xl hover:bg-white/10 text-gray-400 hover:text-white transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            <UserPlus className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">Invite Participants</h3>
            <p className="text-xs text-gray-400">Share room link or send direct invitations</p>
          </div>
        </div>

        {/* Shareable Link Box */}
        <div className="mb-6 p-3.5 rounded-xl bg-white/[0.02] border border-white/10 space-y-2">
          <label className="text-xs font-semibold text-gray-300 uppercase tracking-wider">
            Shareable Room Link
          </label>
          <div className="flex items-center gap-2">
            <input
              type="text"
              readOnly
              value={joinUrl}
              className="w-full glass-input text-xs py-2 px-3 rounded-lg font-mono text-gray-300 select-all"
            />
            <Button
              type="button"
              variant={copied ? 'glass' : 'primary'}
              size="sm"
              onClick={handleCopyLink}
              leftIcon={copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            >
              {copied ? 'Copied' : 'Copy'}
            </Button>
          </div>
        </div>

        {/* Notifications Alert */}
        {successMsg && (
          <div className="mb-4 p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl flex items-center gap-2.5 text-emerald-300 text-xs">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}

        {errorMsg && (
          <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-center gap-2.5 text-rose-300 text-xs">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Direct Invite Form */}
        <form onSubmit={handleSendInvites} className="space-y-4">
          <Input
            label="Invite by Email (Comma Separated)"
            placeholder="colleague1@example.com, colleague2@example.com"
            value={emailInput}
            onChange={(e) => setEmailInput(e.target.value)}
            disabled={loading}
          />

          <Input
            label="Invite by Username (Comma Separated)"
            placeholder="alice, bob, charlie"
            value={usernameInput}
            onChange={(e) => setUsernameInput(e.target.value)}
            disabled={loading}
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
              rightIcon={<Send className="w-3.5 h-3.5" />}
            >
              Send Invitations
            </Button>
          </div>
        </form>
      </GlassCard>
    </div>
  );
};

export default InviteModal;
