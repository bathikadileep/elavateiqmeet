import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { io, Socket } from 'socket.io-client';
import { useAuth } from '../hooks/useAuth';
import type { ChatMessage, RoomUser, TypingUser } from '../types/chat';

export interface SocketContextType {
  socket: Socket | null;
  isConnected: boolean;
  activeRoom: string | null;
  messages: ChatMessage[];
  onlineUsers: RoomUser[];
  typingUsers: TypingUser[];
  joinRoom: (roomCode: string) => void;
  leaveRoom: () => void;
  sendMessage: (content: string) => void;
  sendPrivateMessage: (content: string, recipientId: string) => void;
  startTyping: (recipientId?: string) => void;
  stopTyping: (recipientId?: string) => void;
}

export const SocketContext = createContext<SocketContextType | undefined>(undefined);

const getSocketUrl = () => {
  if (import.meta.env.VITE_SOCKET_URL) return import.meta.env.VITE_SOCKET_URL;
  const host = typeof window !== 'undefined' ? window.location.hostname : 'localhost';
  return `http://${host}:5000`;
};

export const SocketProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();

  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [activeRoom, setActiveRoom] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [onlineUsers, setOnlineUsers] = useState<RoomUser[]>([]);
  const [typingUsers, setTypingUsers] = useState<TypingUser[]>([]);

  const typingTimeoutRef = useRef<Record<string, ReturnType<typeof setTimeout>>>({});

  useEffect(() => {
    const sio = io(getSocketUrl(), {
      withCredentials: true,
      autoConnect: true,
      reconnection: true,
      reconnectionAttempts: 10,
      reconnectionDelay: 1000,
    });

    sio.on('connect', () => {
      setIsConnected(true);
    });

    sio.on('disconnect', () => {
      setIsConnected(false);
    });

    sio.on('user_joined', (data) => {
      const sysMsg: ChatMessage = {
        id: `sys-join-${Date.now()}`,
        room_code: data.room_code || '',
        sender_name: 'System',
        content: `${data.display_name || data.username} joined the meeting.`,
        is_private: false,
        timestamp: new Date().toISOString(),
        is_system: true,
      };
      setMessages((prev) => [...prev, sysMsg]);
    });

    sio.on('user_left', (data) => {
      const sysMsg: ChatMessage = {
        id: `sys-left-${Date.now()}`,
        room_code: data.room_code || '',
        sender_name: 'System',
        content: `${data.display_name || data.username} left the meeting.`,
        is_private: false,
        timestamp: new Date().toISOString(),
        is_system: true,
      };
      setMessages((prev) => [...prev, sysMsg]);
    });

    sio.on('room_roster', (data) => {
      setOnlineUsers(data.users || []);
    });

    sio.on('new_message', (msg: ChatMessage) => {
      setMessages((prev) => [...prev, msg]);
    });

    sio.on('user_typing', (data: TypingUser) => {
      setTypingUsers((prev) => {
        if (!prev.some((u) => u.display_name === data.display_name)) {
          return [...prev, data];
        }
        return prev;
      });

      // Clear typing indicator after 3 seconds of inactivity
      const key = data.display_name;
      if (typingTimeoutRef.current[key]) {
        clearTimeout(typingTimeoutRef.current[key]);
      }
      typingTimeoutRef.current[key] = setTimeout(() => {
        setTypingUsers((prev) => prev.filter((u) => u.display_name !== data.display_name));
      }, 3000);
    });

    sio.on('user_stopped_typing', (data: TypingUser) => {
      setTypingUsers((prev) => prev.filter((u) => u.display_name !== data.display_name));
    });

    setSocket(sio);

    return () => {
      sio.disconnect();
    };
  }, []);

  const joinRoom = useCallback(
    (roomCode: string) => {
      if (!socket) return;
      setActiveRoom(roomCode);
      setMessages([]);
      socket.emit('join_room', {
        room_code: roomCode,
        user_id: user?.id || null,
        username: user?.username || 'Guest',
        display_name: user?.display_name || user?.username || 'Guest',
        timestamp: new Date().toISOString(),
      });
    },
    [socket, user]
  );

  const leaveRoom = useCallback(() => {
    if (!socket || !activeRoom) return;
    socket.emit('leave_room', { room_code: activeRoom });
    setActiveRoom(null);
    setMessages([]);
    setOnlineUsers([]);
  }, [socket, activeRoom]);

  const sendMessage = useCallback(
    (content: string) => {
      if (!socket || !activeRoom || !content.trim()) return;
      socket.emit('send_message', {
        room_code: activeRoom,
        content: content.trim(),
        user_id: user?.id || null,
        display_name: user?.display_name || user?.username || 'Guest',
      });
    },
    [socket, activeRoom, user]
  );

  const sendPrivateMessage = useCallback(
    (content: string, recipientId: string) => {
      if (!socket || !activeRoom || !content.trim()) return;
      socket.emit('send_message', {
        room_code: activeRoom,
        content: content.trim(),
        recipient_id: recipientId,
        user_id: user?.id || null,
        display_name: user?.display_name || user?.username || 'Guest',
      });
    },
    [socket, activeRoom, user]
  );

  const startTyping = useCallback(
    (recipientId?: string) => {
      if (!socket || !activeRoom) return;
      socket.emit('typing_start', {
        room_code: activeRoom,
        recipient_id: recipientId || null,
        user_id: user?.id || null,
        display_name: user?.display_name || user?.username || 'Someone',
      });
    },
    [socket, activeRoom, user]
  );

  const stopTyping = useCallback(
    (recipientId?: string) => {
      if (!socket || !activeRoom) return;
      socket.emit('typing_stop', {
        room_code: activeRoom,
        recipient_id: recipientId || null,
        user_id: user?.id || null,
      });
    },
    [socket, activeRoom, user]
  );

  return (
    <SocketContext.Provider
      value={{
        socket,
        isConnected,
        activeRoom,
        messages,
        onlineUsers,
        typingUsers,
        joinRoom,
        leaveRoom,
        sendMessage,
        sendPrivateMessage,
        startTyping,
        stopTyping,
      }}
    >
      {children}
    </SocketContext.Provider>
  );
};

export const useSocket = () => {
  const context = useContext(SocketContext);
  if (!context) {
    throw new Error('useSocket must be used within a SocketProvider');
  }
  return context;
};
