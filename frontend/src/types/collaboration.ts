/**
 * ElevateIQ Collaboration Suite — TypeScript Definitions
 */

export type WhiteboardTool =
  | 'pencil'
  | 'eraser'
  | 'rectangle'
  | 'circle'
  | 'arrow'
  | 'text'
  | 'sticky'
  | 'laser';

export interface WhiteboardStroke {
  id: string;
  tool: WhiteboardTool;
  points: number[]; // [x1, y1, x2, y2, ...]
  color: string;
  width: number;
  text?: string;
  stickyColor?: string;
}

export interface PollOptionItem {
  id: string;
  poll_id: string;
  option_text: string;
  vote_count: number;
}

export interface PollItem {
  id: string;
  meeting_code: string;
  created_by: string;
  question: string;
  is_multiselect: boolean;
  is_published: boolean;
  is_closed: boolean;
  created_at: string;
  options: PollOptionItem[];
  total_votes: number;
}

export interface BreakoutRoomItem {
  id: string;
  meeting_code: string;
  room_name: string;
  duration_minutes: number;
  is_active: boolean;
  created_at: string;
  assigned_users: string[];
}
