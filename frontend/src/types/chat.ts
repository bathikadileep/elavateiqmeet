export interface ChatMessage {
  id: string;
  room_code: string;
  sender_id?: string | null;
  sender_name: string;
  content: string;
  is_private: boolean;
  recipient_id?: string | null;
  timestamp: string;
  is_system?: boolean;
}

export interface RoomUser {
  sid: string;
  user_id?: string | null;
  username: string;
  display_name: string;
}

export interface TypingUser {
  user_id?: string | null;
  display_name: string;
  recipient_id?: string | null;
}
