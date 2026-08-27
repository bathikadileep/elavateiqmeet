export interface FileItem {
  id: string;
  uploader_id?: string | null;
  meeting_id?: string | null;
  file_category: 'avatar' | 'attachment' | 'recording' | 'transcript';
  original_name: string;
  mime_type: string;
  size_bytes: number;
  created_at: string;
}
