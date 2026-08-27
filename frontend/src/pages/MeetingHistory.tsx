import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import meetingsApi, { type MeetingHistoryItem } from '../api/meetings';
import GlassCard from '../components/common/GlassCard';
import Button from '../components/common/Button';
import Badge from '../components/common/Badge';
import Spinner from '../components/common/Spinner';
import InviteModal from '../components/meetings/InviteModal';
import EditMeetingModal from '../components/meetings/EditMeetingModal';
import { Video, Plus, Search, Calendar, UserPlus, Edit, Trash2, ArrowRight } from 'lucide-react';

export const MeetingHistory: React.FC = () => {
  const navigate = useNavigate();

  const [meetings, setMeetings] = useState<MeetingHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const [inviteMeeting, setInviteMeeting] = useState<MeetingHistoryItem | null>(null);
  const [editMeeting, setEditMeeting] = useState<MeetingHistoryItem | null>(null);

  const fetchHistory = useCallback(async () => {
    setLoading(true);
    try {
      const res = await meetingsApi.getHistory();
      setMeetings(res.meetings);
    } catch (err) {
      console.error('Failed to fetch meeting history:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this meeting?')) return;
    try {
      await meetingsApi.delete(id);
      setMeetings((prev) => prev.filter((m) => m.id !== id));
    } catch (err) {
      console.error('Failed to delete meeting:', err);
    }
  };

  const filteredMeetings = meetings.filter((m) => {
    const matchesSearch =
      m.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.meeting_code.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'all' || m.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-white">Meeting History & Sessions</h1>
          <p className="text-xs text-gray-400">View past sessions, scheduled meetings, and participant invites</p>
        </div>

        <Button
          variant="primary"
          onClick={() => navigate('/meeting/new')}
          leftIcon={<Plus className="w-4 h-4" />}
        >
          New Meeting
        </Button>
      </div>

      {/* Filter Bar */}
      <GlassCard variant="subtle" className="p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
        {/* Search */}
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-3 pointer-events-none" />
          <input
            type="text"
            placeholder="Search by title or code..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full glass-input text-xs py-2 pl-9 pr-3 rounded-xl focus:outline-none"
          />
        </div>

        {/* Status Filter Tabs */}
        <div className="flex items-center gap-1 bg-white/5 p-1 rounded-xl w-full sm:w-auto">
          {['all', 'live', 'scheduled', 'ended'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold capitalize transition-all cursor-pointer ${
                statusFilter === st ? 'bg-indigo-600 text-white shadow-sm' : 'text-gray-400 hover:text-white'
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </GlassCard>

      {/* Table / Cards List */}
      {loading ? (
        <Spinner text="Loading meeting history..." />
      ) : filteredMeetings.length === 0 ? (
        <GlassCard variant="default" className="py-16 text-center text-gray-400 space-y-3">
          <Calendar className="w-12 h-12 text-gray-600 mx-auto stroke-1" />
          <h3 className="text-base font-bold text-white">No meetings found</h3>
          <p className="text-xs">Schedule a new meeting or start an instant room.</p>
        </GlassCard>
      ) : (
        <div className="grid grid-cols-1 gap-3">
          {filteredMeetings.map((m) => {
            const isLive = m.status === 'live';
            return (
              <GlassCard
                key={m.id}
                variant="hover"
                className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
              >
                <div className="flex items-center gap-3.5">
                  <div className={`p-3 rounded-xl ${isLive ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' : 'bg-white/5 text-gray-400'}`}>
                    <Video className="w-5 h-5" />
                  </div>

                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-bold text-white">{m.title}</h3>
                      <Badge variant={isLive ? 'danger' : m.status === 'scheduled' ? 'info' : 'neutral'} size="sm">
                        {m.status}
                      </Badge>
                      {m.is_host && <Badge variant="warning" size="sm">Host</Badge>}
                    </div>

                    <p className="text-xs text-gray-400 font-mono mt-1">
                      Code: <span className="text-indigo-300 font-semibold">{m.meeting_code}</span> • Created: {new Date(m.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setInviteMeeting(m)}
                    leftIcon={<UserPlus className="w-3.5 h-3.5" />}
                  >
                    Invite
                  </Button>

                  {m.is_host && m.status === 'scheduled' && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setEditMeeting(m)}
                      leftIcon={<Edit className="w-3.5 h-3.5" />}
                    >
                      Edit
                    </Button>
                  )}

                  {m.is_host && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(m.id)}
                      className="hover:text-rose-400"
                      leftIcon={<Trash2 className="w-3.5 h-3.5" />}
                    >
                      Delete
                    </Button>
                  )}

                  <Button
                    variant={isLive ? 'danger' : 'primary'}
                    size="sm"
                    onClick={() => navigate(`/room/${m.meeting_code}`)}
                    rightIcon={<ArrowRight className="w-3.5 h-3.5" />}
                  >
                    {isLive ? 'Join Live' : 'Enter'}
                  </Button>
                </div>
              </GlassCard>
            );
          })}
        </div>
      )}

      {/* Invite Modal */}
      {inviteMeeting && (
        <InviteModal meeting={inviteMeeting} onClose={() => setInviteMeeting(null)} />
      )}

      {/* Edit Modal */}
      {editMeeting && (
        <EditMeetingModal
          meeting={editMeeting}
          onClose={() => setEditMeeting(null)}
          onUpdated={(updated) => {
            setMeetings((prev) => prev.map((item) => (item.id === updated.id ? { ...item, ...updated } : item)));
          }}
        />
      )}
    </div>
  );
};

export default MeetingHistory;
