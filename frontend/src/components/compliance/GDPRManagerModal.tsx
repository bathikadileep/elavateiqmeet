import React, { useState } from 'react';
import client from '../../api/client';

interface GDPRManagerModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const GDPRManagerModal: React.FC<GDPRManagerModalProps> = ({ isOpen, onClose }) => {
  const [isExporting, setIsExporting] = useState(false);
  const [confirmPhrase, setConfirmPhrase] = useState('');
  const [forgetStatus, setForgetStatus] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleExportData = async () => {
    setIsExporting(true);
    try {
      const response = await client.get('/api/compliance/export', {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'gdpr_data_export.zip');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Failed downloading GDPR export bundle:', err);
    } finally {
      setIsExporting(false);
    }
  };

  const handleRightToBeForgotten = async () => {
    if (confirmPhrase !== 'delete my account permanently') {
      alert("Please type 'delete my account permanently' to confirm.");
      return;
    }
    try {
      const res = await client.post('/api/compliance/forget', {
        confirmation: confirmPhrase,
      });
      setForgetStatus(res.data?.message || 'Account successfully anonymized.');
    } catch (err: any) {
      setForgetStatus(err.response?.data?.error || 'Failed executing erasure request.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
      <div className="w-full max-w-lg p-6 bg-[#121422] border border-cyan-500/30 rounded-2xl shadow-2xl text-white">
        <h2 className="text-xl font-bold text-cyan-400 mb-4">🦁 Enterprise GDPR & Privacy Control</h2>

        <div className="space-y-6">
          <div className="p-4 bg-[#1a1d30] rounded-xl border border-cyan-500/20">
            <h3 className="text-md font-semibold text-cyan-300">GDPR Article 20: Data Portability</h3>
            <p className="text-xs text-gray-400 mt-1">
              Download a complete ZIP archive containing your profile details, hosted meeting history, chat messages, and assigned action items.
            </p>
            <button
              onClick={handleExportData}
              disabled={isExporting}
              className="mt-3 px-4 py-2 text-sm font-semibold bg-cyan-500 hover:bg-cyan-400 text-slate-950 rounded-lg transition"
            >
              {isExporting ? 'Generating ZIP...' : 'Export My Data Bundle'}
            </button>
          </div>

          <div className="p-4 bg-[#1a1d30] rounded-xl border border-red-500/20">
            <h3 className="text-md font-semibold text-red-400">GDPR Article 17: Right to be Forgotten</h3>
            <p className="text-xs text-gray-400 mt-1">
              Permanently anonymize your account details and purge your transcript history from platform databases.
            </p>
            <input
              type="text"
              placeholder="Type 'delete my account permanently'"
              value={confirmPhrase}
              onChange={(e) => setConfirmPhrase(e.target.value)}
              className="w-full mt-3 p-2 text-xs bg-slate-900 border border-red-500/30 rounded text-white focus:outline-none focus:border-red-500"
            />
            <button
              onClick={handleRightToBeForgotten}
              className="mt-3 px-4 py-2 text-sm font-semibold bg-red-600 hover:bg-red-500 text-white rounded-lg transition"
            >
              Execute Erasure Request
            </button>
            {forgetStatus && <p className="text-xs mt-2 text-yellow-400">{forgetStatus}</p>}
          </div>
        </div>

        <div className="mt-6 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-400 hover:text-white transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
