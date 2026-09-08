import React, { useState } from 'react';
import { Key, RefreshCw, ShieldCheck, Clock, CheckCircle } from 'lucide-react';

interface KeyVersion {
  id: string;
  type: string;
  version: number;
  status: 'ACTIVE' | 'DEPRECATED';
  createdAt: string;
}

export const KeyRotationPanel: React.FC = () => {
  const [keys, setKeys] = useState<KeyVersion[]>([
    { id: 'kid_jwt_v2_1700', type: 'JWT_RS256', version: 2, status: 'ACTIVE', createdAt: '2026-09-01' },
    { id: 'kid_jwt_v1_1600', type: 'JWT_RS256', version: 1, status: 'DEPRECATED', createdAt: '2026-06-01' },
  ]);

  const [isRotating, setIsRotating] = useState(false);

  const handleRotate = () => {
    setIsRotating(true);
    setTimeout(() => {
      const newVer: KeyVersion = {
        id: `kid_jwt_v${keys.length + 1}_${Date.now()}`,
        type: 'JWT_RS256',
        version: keys.length + 1,
        status: 'ACTIVE',
        createdAt: new Date().toISOString().split('T')[0],
      };
      setKeys([newVer, ...keys.map(k => ({ ...k, status: 'DEPRECATED' as const }))]);
      setIsRotating(false);
    }, 1000);
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-xl">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <Key className="h-6 w-6 text-amber-400" />
          <div>
            <h2 className="text-lg font-bold text-white">Cryptographic Key Ring</h2>
            <p className="text-xs text-slate-400">Zero-downtime key rotation for JWT signing and database encryption</p>
          </div>
        </div>
        <button
          onClick={handleRotate}
          disabled={isRotating}
          className="flex items-center gap-2 rounded-xl bg-amber-500/20 px-4 py-2 text-xs font-semibold text-amber-300 hover:bg-amber-500/30"
        >
          <RefreshCw className={`h-4 w-4 ${isRotating ? 'animate-spin' : ''}`} />
          {isRotating ? 'Rotating Key...' : 'Rotate Key Now'}
        </button>
      </div>

      <div className="mt-6 space-y-3">
        {keys.map((k) => (
          <div key={k.id} className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/60 p-4">
            <div className="flex items-center gap-3">
              <ShieldCheck className={`h-5 w-5 ${k.status === 'ACTIVE' ? 'text-emerald-400' : 'text-slate-500'}`} />
              <div>
                <span className="font-mono text-sm font-semibold text-white">{k.id}</span>
                <div className="text-xs text-slate-400">Version {k.version} | Created: {k.createdAt}</div>
              </div>
            </div>
            <span className={`rounded-full px-3 py-1 text-xs font-bold ${k.status === 'ACTIVE' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-slate-800 text-slate-400'}`}>
              {k.status}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};
