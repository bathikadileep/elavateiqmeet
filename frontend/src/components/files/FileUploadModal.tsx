import React, { useState } from 'react';
import filesApi from '../../api/files';
import GlassCard from '../common/GlassCard';
import Button from '../common/Button';
import { UploadCloud, X, FileText, CheckCircle2, AlertCircle } from 'lucide-react';
import type { FileItem } from '../../types/files';

export interface FileUploadModalProps {
  meetingId?: string;
  onClose: () => void;
  onUploaded: (newFile: FileItem) => void;
}

export const FileUploadModal: React.FC<FileUploadModalProps> = ({ meetingId, onClose, onUploaded }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [category, setCategory] = useState<string>('attachment');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setErrorMsg('Please select a file to upload.');
      return;
    }

    setLoading(true);
    setErrorMsg(null);

    try {
      const res = await filesApi.upload(selectedFile, meetingId, category);
      onUploaded(res.file);
      onClose();
    } catch (err: unknown) {
      const error = err as { message?: string };
      setErrorMsg(error.message || 'File upload failed.');
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
            <UploadCloud className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">Upload File</h3>
            <p className="text-xs text-gray-400">Upload documents, attachments, or avatars</p>
          </div>
        </div>

        {errorMsg && (
          <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-center gap-2.5 text-rose-300 text-xs">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Drag & Drop Zone */}
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleFileDrop}
            className={`border-2 border-dashed rounded-2xl p-6 text-center transition-all cursor-pointer relative ${
              isDragging
                ? 'border-indigo-500 bg-indigo-500/10'
                : 'border-white/15 bg-white/[0.02] hover:bg-white/[0.04]'
            }`}
          >
            <input
              type="file"
              onChange={handleFileSelect}
              className="absolute inset-0 opacity-0 cursor-pointer"
            />

            {selectedFile ? (
              <div className="flex flex-col items-center gap-2 text-emerald-400">
                <CheckCircle2 className="w-8 h-8" />
                <span className="text-sm font-semibold text-white truncate max-w-full">
                  {selectedFile.name}
                </span>
                <span className="text-[11px] text-gray-400 font-mono">
                  {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                </span>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-2 text-gray-400">
                <FileText className="w-8 h-8 text-gray-500" />
                <p className="text-xs font-semibold text-gray-300">
                  Drag and drop file here or <span className="text-indigo-400">browse</span>
                </p>
                <p className="text-[10px] text-gray-500">Maximum file size: 50MB</p>
              </div>
            )}
          </div>

          {/* Category Dropdown */}
          <div className="space-y-1.5">
            <label className="block text-xs font-medium text-gray-300 tracking-wide uppercase">
              File Category
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full glass-input rounded-xl text-xs py-2.5 px-3.5 focus:outline-none bg-[#080911]"
            >
              <option value="attachment">Attachment</option>
              <option value="recording">Recording</option>
              <option value="avatar">Avatar</option>
              <option value="transcript">Transcript</option>
            </select>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="ghost" size="sm" onClick={onClose}>
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              isLoading={loading}
              disabled={!selectedFile}
              leftIcon={<UploadCloud className="w-3.5 h-3.5" />}
            >
              Upload Now
            </Button>
          </div>
        </form>
      </GlassCard>
    </div>
  );
};

export default FileUploadModal;
