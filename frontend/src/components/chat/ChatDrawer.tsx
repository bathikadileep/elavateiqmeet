import React, { useState, useEffect, useRef } from 'react';
import { useSocket } from '../../contexts/SocketContext';
import { useAuth } from '../../hooks/useAuth';
import Avatar from '../common/Avatar';
import Button from '../common/Button';
import Badge from '../common/Badge';
import { MessageSquare, Users, Send, X, Lock, Info } from 'lucide-react';
import type { RoomUser } from '../../types/chat';

export interface ChatDrawerProps {
  onClose: () => void;
}

export const ChatDrawer: React.FC<ChatDrawerProps> = ({ onClose }) => {
  const { user } = useAuth();
  const {
    messages,
    onlineUsers,
    typingUsers,
    sendMessage,
    sendPrivateMessage,
    startTyping,
    stopTyping,
  } = useSocket();

  const [activeTab, setActiveTab] = useState<'public' | 'private' | 'roster'>('public');
  const [selectedRecipient, setSelectedRecipient] = useState<RoomUser | null>(null);
  const [inputText, setInputText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, typingUsers]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputText(e.target.value);
    if (e.target.value.trim()) {
      startTyping(selectedRecipient?.user_id || undefined);
    } else {
      stopTyping(selectedRecipient?.user_id || undefined);
    }
  };

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    if (selectedRecipient && selectedRecipient.user_id) {
      sendPrivateMessage(inputText, selectedRecipient.user_id);
    } else {
      sendMessage(inputText);
    }

    stopTyping(selectedRecipient?.user_id || undefined);
    setInputText('');
  };

  // Filter messages for current tab
  const displayedMessages = messages.filter((m) => {
    if (selectedRecipient) {
      // Private messages between me and recipient
      return (
        m.is_private &&
        ((m.sender_id === user?.id && m.recipient_id === selectedRecipient.user_id) ||
          (m.sender_id === selectedRecipient.user_id && m.recipient_id === user?.id))
      );
    }
    // Public room messages
    return !m.is_private;
  });

  return (
    <div className="w-80 sm:w-96 h-full glass-card border-l border-white/10 flex flex-col justify-between bg-[#080911]/90 backdrop-blur-2xl z-40 select-none">
      {/* Header */}
      <div className="p-4 border-b border-white/10 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <MessageSquare className="w-5 h-5 text-indigo-400" />
          <h3 className="text-base font-bold text-white">In-Meeting Chat</h3>
        </div>

        <button
          onClick={onClose}
          className="p-1.5 rounded-xl hover:bg-white/10 text-gray-400 hover:text-white transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Tabs Bar */}
      <div className="flex items-center gap-1 p-2 bg-white/[0.02] border-b border-white/5 text-xs">
        <button
          onClick={() => {
            setActiveTab('public');
            setSelectedRecipient(null);
          }}
          className={`flex-1 py-1.5 rounded-lg font-semibold transition-all cursor-pointer ${
            activeTab === 'public' ? 'bg-indigo-600 text-white shadow-sm' : 'text-gray-400 hover:text-white'
          }`}
        >
          Meeting Chat
        </button>

        <button
          onClick={() => setActiveTab('roster')}
          className={`flex-1 py-1.5 rounded-lg font-semibold transition-all flex items-center justify-center gap-1.5 cursor-pointer ${
            activeTab === 'roster' ? 'bg-indigo-600 text-white shadow-sm' : 'text-gray-400 hover:text-white'
          }`}
        >
          <Users className="w-3.5 h-3.5" />
          Participants ({onlineUsers.length})
        </button>
      </div>

      {/* Direct Message Active Header */}
      {selectedRecipient && (
        <div className="px-4 py-2 bg-indigo-500/10 border-b border-indigo-500/20 flex items-center justify-between text-xs">
          <div className="flex items-center gap-2 text-indigo-300">
            <Lock className="w-3.5 h-3.5" />
            <span>Private DM with <strong>{selectedRecipient.display_name}</strong></span>
          </div>
          <button
            onClick={() => setSelectedRecipient(null)}
            className="text-gray-400 hover:text-white text-[11px] underline cursor-pointer"
          >
            Clear
          </button>
        </div>
      )}

      {/* Content Area */}
      <div className="flex-1 p-4 overflow-y-auto space-y-3">
        {activeTab === 'roster' ? (
          /* Online Participant Roster */
          <div className="space-y-2">
            <div className="text-[11px] font-bold text-gray-500 uppercase tracking-wider mb-2">
              Active Room Participants
            </div>
            {onlineUsers.map((u) => (
              <div
                key={u.sid}
                className="p-2.5 rounded-xl glass-card flex items-center justify-between text-xs"
              >
                <div className="flex items-center gap-2.5">
                  <Avatar name={u.display_name} size="sm" status="online" />
                  <div>
                    <span className="font-semibold text-white">{u.display_name}</span>
                    <span className="block text-[10px] text-gray-400">@{u.username}</span>
                  </div>
                </div>

                {u.user_id !== user?.id && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setSelectedRecipient(u);
                      setActiveTab('private');
                    }}
                  >
                    DM
                  </Button>
                )}
              </div>
            ))}
          </div>
        ) : (
          /* Chat Messages Feed */
          <div className="space-y-3">
            {displayedMessages.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center text-gray-400 space-y-2">
                <Info className="w-8 h-8 text-gray-600 stroke-1" />
                <p className="text-xs">No messages yet. Send a message to start conversing!</p>
              </div>
            ) : (
              displayedMessages.map((m) => {
                if (m.is_system) {
                  return (
                    <div key={m.id} className="flex items-center justify-center my-2">
                      <span className="text-[10px] bg-white/5 border border-white/10 text-gray-400 px-3 py-1 rounded-full">
                        {m.content}
                      </span>
                    </div>
                  );
                }

                const isMe = m.sender_id === user?.id;

                return (
                  <div key={m.id} className={`flex flex-col ${isMe ? 'items-end' : 'items-start'}`}>
                    <div className="flex items-center gap-1.5 mb-1 text-[10px] text-gray-400 px-1">
                      <span className="font-semibold text-gray-300">{isMe ? 'You' : m.sender_name}</span>
                      <span>•</span>
                      <span>{new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                      {m.is_private && <Badge variant="info" size="sm">DM</Badge>}
                    </div>

                    <div
                      className={`max-w-[85%] px-3.5 py-2 rounded-2xl text-xs leading-relaxed ${
                        isMe
                          ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-tr-none shadow-md'
                          : 'bg-white/10 border border-white/10 text-gray-100 rounded-tl-none'
                      }`}
                    >
                      {m.content}
                    </div>
                  </div>
                );
              })
            )}

            {/* Typing Indicator */}
            {typingUsers.length > 0 && (
              <div className="flex items-center gap-2 text-xs text-indigo-400 italic py-1 animate-pulse">
                <span className="flex h-2 w-2 relative">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
                </span>
                <span>
                  {typingUsers.map((u) => u.display_name).join(', ')}{' '}
                  {typingUsers.length === 1 ? 'is' : 'are'} typing...
                </span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Footer Form */}
      {activeTab !== 'roster' && (
        <form onSubmit={handleSend} className="p-3 border-t border-white/10 bg-[#080911]/90 flex items-center gap-2">
          <input
            type="text"
            placeholder={selectedRecipient ? `Private message to ${selectedRecipient.display_name}...` : 'Type a message...'}
            value={inputText}
            onChange={handleInputChange}
            className="flex-1 glass-input text-xs py-2.5 px-3.5 rounded-xl focus:outline-none"
          />

          <Button
            type="submit"
            variant="primary"
            size="sm"
            disabled={!inputText.trim()}
            rightIcon={<Send className="w-3.5 h-3.5" />}
          >
            Send
          </Button>
        </form>
      )}
    </div>
  );
};

export default ChatDrawer;
