import React, { useEffect, useState, useCallback } from 'react';
import filesApi from '../api/files';
import type { FileItem } from '../types/files';
import GlassCard from '../components/common/GlassCard';
import Button from '../components/common/Button';
import Badge from '../components/common/Badge';
import Spinner from '../components/common/Spinner';
import FileUploadModal from '../components/files/FileUploadModal';
import FilePreviewModal from '../components/files/FilePreviewModal';
import { Folder, UploadCloud, Search, Download, Eye, Trash2, FileText, Image, Video, Music } from 'lucide-react';

export const FileManager: React.FC = () => {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');

  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [previewFile, setPreviewFile] = useState<FileItem | null>(null);

  const fetchFiles = useCallback(async () => {
    setLoading(true);
    try {
      const res = await filesApi.list();
      setFiles(res.files);
    } catch (err) {
      console.error('Failed to load file manager files:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchFiles();
  }, [fetchFiles]);

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this file?')) return;
    try {
      await filesApi.delete(id);
      setFiles((prev) => prev.filter((f) => f.id !== id));
    } catch (err) {
      console.error('Failed to delete file:', err);
    }
  };

  const getFileIcon = (mime: string) => {
    if (mime.startsWith('image/')) return <Image className="w-5 h-5 text-purple-400" />;
    if (mime.startsWith('video/')) return <Video className="w-5 h-5 text-rose-400" />;
    if (mime.startsWith('audio/')) return <Music className="w-5 h-5 text-cyan-400" />;
    return <FileText className="w-5 h-5 text-indigo-400" />;
  };

  const filteredFiles = files.filter((f) => {
    const matchesSearch = f.original_name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = categoryFilter === 'all' || f.file_category === categoryFilter;
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="space-y-6 pb-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-white">File Sharing & Asset Manager</h1>
          <p className="text-xs text-gray-400">Secure local file storage, meeting attachments, and recordings</p>
        </div>

        <Button
          variant="primary"
          onClick={() => setUploadModalOpen(true)}
          leftIcon={<UploadCloud className="w-4 h-4" />}
        >
          Upload New File
        </Button>
      </div>

      {/* Filter & Search Bar */}
      <GlassCard variant="subtle" className="p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-3 pointer-events-none" />
          <input
            type="text"
            placeholder="Search files..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full glass-input text-xs py-2 pl-9 pr-3 rounded-xl focus:outline-none"
          />
        </div>

        {/* Category Tabs */}
        <div className="flex items-center gap-1 bg-white/5 p-1 rounded-xl w-full sm:w-auto overflow-x-auto">
          {['all', 'attachment', 'recording', 'avatar', 'transcript'].map((cat) => (
            <button
              key={cat}
              onClick={() => setCategoryFilter(cat)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold capitalize transition-all cursor-pointer ${
                categoryFilter === cat ? 'bg-indigo-600 text-white shadow-sm' : 'text-gray-400 hover:text-white'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </GlassCard>

      {/* File Cards Grid */}
      {loading ? (
        <Spinner text="Loading files..." />
      ) : filteredFiles.length === 0 ? (
        <GlassCard variant="default" className="py-16 text-center text-gray-400 space-y-3">
          <Folder className="w-12 h-12 text-gray-600 mx-auto stroke-1" />
          <h3 className="text-base font-bold text-white">No files found</h3>
          <p className="text-xs">Upload attachments or meeting recordings to view them here.</p>
        </GlassCard>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filteredFiles.map((file) => (
            <GlassCard
              key={file.id}
              variant="hover"
              className="p-4 flex flex-col justify-between space-y-4"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="p-3 rounded-xl bg-white/5 border border-white/10 shrink-0">
                  {getFileIcon(file.mime_type)}
                </div>

                <div className="flex-1 min-w-0">
                  <h4 className="text-sm font-bold text-white truncate" title={file.original_name}>
                    {file.original_name}
                  </h4>
                  <p className="text-[10px] text-gray-400 font-mono mt-0.5">
                    {(file.size_bytes / (1024 * 1024)).toFixed(2)} MB
                  </p>
                  <div className="mt-1.5">
                    <Badge variant="info" size="sm">
                      {file.file_category}
                    </Badge>
                  </div>
                </div>
              </div>

              {/* Actions Footer */}
              <div className="flex items-center justify-between border-t border-white/10 pt-3 text-xs">
                <span className="text-[10px] text-gray-400 font-mono">
                  {new Date(file.created_at).toLocaleDateString()}
                </span>

                <div className="flex items-center gap-1">
                  <button
                    onClick={() => setPreviewFile(file)}
                    title="Preview"
                    className="p-1.5 rounded-lg hover:bg-white/10 text-gray-400 hover:text-white transition-colors cursor-pointer"
                  >
                    <Eye className="w-4 h-4" />
                  </button>

                  <a href={filesApi.getDownloadUrl(file.id)} download title="Download">
                    <div className="p-1.5 rounded-lg hover:bg-white/10 text-gray-400 hover:text-white transition-colors cursor-pointer">
                      <Download className="w-4 h-4" />
                    </div>
                  </a>

                  <button
                    onClick={() => handleDelete(file.id)}
                    title="Delete"
                    className="p-1.5 rounded-lg hover:bg-rose-500/20 text-gray-400 hover:text-rose-400 transition-colors cursor-pointer"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </GlassCard>
          ))}
        </div>
      )}

      {/* Upload Modal */}
      {uploadModalOpen && (
        <FileUploadModal
          onClose={() => setUploadModalOpen(false)}
          onUploaded={(newFile) => setFiles((prev) => [newFile, ...prev])}
        />
      )}

      {/* Preview Modal */}
      {previewFile && (
        <FilePreviewModal file={previewFile} onClose={() => setPreviewFile(null)} />
      )}
    </div>
  );
};

export default FileManager;
