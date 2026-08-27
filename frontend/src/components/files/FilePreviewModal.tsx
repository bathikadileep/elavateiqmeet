import React from 'react';
import filesApi from '../../api/files';
import GlassCard from '../common/GlassCard';
import Button from '../common/Button';
import { X, Download, FileText, Eye } from 'lucide-react';
import type { FileItem } from '../../types/files';

export interface FilePreviewModalProps {
  file: FileItem;
  onClose: () => void;
}

export const FilePreviewModal: React.FC<FilePreviewModalProps> = ({ file, onClose }) => {
  const previewUrl = filesApi.getPreviewUrl(file.id);
  const downloadUrl = filesApi.getDownloadUrl(file.id);

  const isImage = file.mime_type.startsWith('image/');
  const isVideo = file.mime_type.startsWith('video/');
  const isAudio = file.mime_type.startsWith('audio/');
  const isPdf = file.mime_type === 'application/pdf';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#080911]/85 backdrop-blur-md animate-in fade-in duration-200">
      <GlassCard variant="glow" className="w-full max-w-3xl p-6 relative max-h-[90vh] flex flex-col justify-between">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/10 pb-4 mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-400">
              <Eye className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white truncate max-w-md">{file.original_name}</h3>
              <p className="text-[11px] text-gray-400 font-mono">
                {file.mime_type} • {(file.size_bytes / (1024 * 1024)).toFixed(2)} MB
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <a href={downloadUrl} download target="_blank" rel="noreferrer">
              <Button variant="primary" size="sm" leftIcon={<Download className="w-3.5 h-3.5" />}>
                Download
              </Button>
            </a>
            <button
              onClick={onClose}
              className="p-1.5 rounded-xl hover:bg-white/10 text-gray-400 hover:text-white transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content Viewer Body */}
        <div className="flex-1 overflow-auto flex items-center justify-center min-h-[300px] max-h-[60vh] bg-black/40 rounded-2xl border border-white/5 p-4">
          {isImage ? (
            <img src={previewUrl} alt={file.original_name} className="max-h-full max-w-full object-contain rounded-lg" />
          ) : isVideo ? (
            <video src={previewUrl} controls className="max-h-full max-w-full rounded-lg" />
          ) : isAudio ? (
            <audio src={previewUrl} controls className="w-full max-w-md" />
          ) : isPdf ? (
            <iframe src={previewUrl} title={file.original_name} className="w-full h-full min-h-[400px] rounded-lg" />
          ) : (
            <div className="flex flex-col items-center justify-center text-gray-400 space-y-3 py-12">
              <FileText className="w-16 h-16 text-gray-600 stroke-1" />
              <p className="text-sm font-semibold text-gray-300">Inline preview unavailable for this format.</p>
              <a href={downloadUrl} download>
                <Button variant="secondary" size="sm" leftIcon={<Download className="w-3.5 h-3.5" />}>
                  Download File
                </Button>
              </a>
            </div>
          )}
        </div>
      </GlassCard>
    </div>
  );
};

export default FilePreviewModal;
