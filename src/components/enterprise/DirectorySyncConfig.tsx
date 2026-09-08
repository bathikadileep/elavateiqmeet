import React, { useState } from 'react';
import { Database, RefreshCw, CheckCircle2, Server, Users, ArrowRight } from 'lucide-react';

export const DirectorySyncConfig: React.FC = () => {
  const [ldapHost, setLdapHost] = useState('ldap.enterprise.com');
  const [baseDn, setBaseDn] = useState('dc=enterprise,dc=com');
  const [isSyncing, setIsSyncing] = useState(false);
  const [lastSync, setLastSync] = useState<{ count: number; date: string } | null>({ count: 142, date: '2026-09-08 10:30 AM' });

  const handleSyncNow = () => {
    setIsSyncing(true);
    setTimeout(() => {
      setIsSyncing(false);
      setLastSync({ count: 145, date: 'Just now' });
    }, 1200);
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-xl">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <Database className="h-6 w-6 text-purple-400" />
          <div>
            <h2 className="text-lg font-bold text-white">LDAP / Active Directory Sync</h2>
            <p className="text-xs text-slate-400">Automated user provisioning & group membership sync</p>
          </div>
        </div>
        <button
          onClick={handleSyncNow}
          disabled={isSyncing}
          className="flex items-center gap-2 rounded-xl bg-purple-500/20 px-4 py-2 text-xs font-semibold text-purple-300 hover:bg-purple-500/30"
        >
          <RefreshCw className={`h-4 w-4 ${isSyncing ? 'animate-spin' : ''}`} />
          {isSyncing ? 'Syncing...' : 'Sync Now'}
        </button>
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <div>
          <label className="block text-xs font-semibold text-slate-300">LDAP Server Host</label>
          <input
            type="text"
            value={ldapHost}
            onChange={(e) => setLdapHost(e.target.value)}
            className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white focus:border-purple-500 focus:outline-none"
          />
        </div>
        <div>
          <label className="block text-xs font-semibold text-slate-300">Base Distinguished Name (DN)</label>
          <input
            type="text"
            value={baseDn}
            onChange={(e) => setBaseDn(e.target.value)}
            className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white focus:border-purple-500 focus:outline-none"
          />
        </div>
      </div>

      {lastSync && (
        <div className="mt-4 flex items-center justify-between rounded-xl bg-purple-950/20 p-3 border border-purple-500/20 text-xs text-purple-300">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            <span>Last Sync: <strong>{lastSync.date}</strong> ({lastSync.count} accounts active)</span>
          </div>
        </div>
      )}
    </div>
  );
};
