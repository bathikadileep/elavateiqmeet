/**
 * ElevateIQ AI Intelligence Suite — TypeScript Definitions
 */

export interface SpeechTranscriptItem {
  id: string;
  speaker_name: string;
  text: string;
  is_final: boolean;
  timestamp: string;
}

export interface ActionItemData {
  id: string;
  task_description: string;
  assigned_to: string;
  due_date?: string;
  is_completed: boolean;
}

export interface MeetingSummaryItem {
  id: string;
  meeting_code: string;
  executive_summary: string;
  key_decisions: string[];
  sentiment_score: string;
  sentiment_value: string;
  generated_at: string;
  action_items: ActionItemData[];
}

export type VirtualBackgroundMode = 'none' | 'blur-low' | 'blur-high' | 'office' | 'neon-studio';
