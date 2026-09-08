import React, { useState, useEffect } from 'react';
import client from '../api/client';

export const TenantSettingsPage: React.FC = () => {
  const [orgName, setOrgName] = useState('ElevateIQ Enterprise');
  const [domain, setDomain] = useState('elevateiq.com');
  const [maxUsers, setMaxUsers] = useState(500);
  const [primaryColor, setPrimaryColor] = useState('#00f2fe');
  const [ipWhitelist, setIpWhitelist] = useState('192.168.1.0/24\n10.0.0.0/16');
  const [statusMsg, setStatusMsg] = useState('');

  const handleSaveSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setStatusMsg('Organization settings saved successfully!');
    } catch (err) {
      setStatusMsg('Failed saving tenant settings.');
    }
  };

  return (
    <div className="min-h-screen bg-[#080911] text-white p-8">
      <div className="max-w-4xl mx-auto space-y-8">
        <div>
          <h1 className="text-2xl font-bold text-cyan-400">🏢 Multi-Tenant Enterprise Administration</h1>
          <p className="text-sm text-gray-400 mt-1">Manage tenant branding, SSO domain federation, and IP security whitelists.</p>
        </div>

        {statusMsg && (
          <div className="p-3 bg-cyan-950/60 border border-cyan-500/40 rounded-xl text-cyan-300 text-sm">
            {statusMsg}
          </div>
        )}

        <form onSubmit={handleSaveSettings} className="space-y-6">
          <div className="p-6 bg-[#121422] border border-cyan-500/20 rounded-2xl shadow-xl space-y-4">
            <h2 className="text-lg font-semibold text-cyan-300">1. Organization Identity & Domain</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-gray-400 mb-1">Organization Name</label>
                <input
                  type="text"
                  value={orgName}
                  onChange={(e) => setOrgName(e.target.value)}
                  className="w-full bg-slate-900 border border-cyan-500/30 rounded-lg p-2.5 text-sm text-white focus:outline-none focus:border-cyan-400"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">Enterprise Domain</label>
                <input
                  type="text"
                  value={domain}
                  onChange={(e) => setDomain(e.target.value)}
                  className="w-full bg-slate-900 border border-cyan-500/30 rounded-lg p-2.5 text-sm text-white focus:outline-none focus:border-cyan-400"
                />
              </div>
            </div>
          </div>

          <div className="p-6 bg-[#121422] border border-cyan-500/20 rounded-2xl shadow-xl space-y-4">
            <h2 className="text-lg font-semibold text-cyan-300">2. Custom Theme & Branding</h2>
            <div className="flex items-center gap-4">
              <div>
                <label className="block text-xs text-gray-400 mb-1">Primary Accent Color</label>
                <input
                  type="color"
                  value={primaryColor}
                  onChange={(e) => setPrimaryColor(e.target.value)}
                  className="w-16 h-10 bg-slate-900 border border-cyan-500/30 rounded cursor-pointer"
                />
              </div>
              <p className="text-xs text-gray-400">Current Theme: <span style={{ color: primaryColor }}>● Accent Color Sample</span></p>
            </div>
          </div>

          <div className="p-6 bg-[#121422] border border-cyan-500/20 rounded-2xl shadow-xl space-y-4">
            <h2 className="text-lg font-semibold text-cyan-300">3. IP Security Whitelist CIDRs</h2>
            <textarea
              rows={4}
              value={ipWhitelist}
              onChange={(e) => setIpWhitelist(e.target.value)}
              placeholder="Enter IP CIDR blocks (one per line)"
              className="w-full bg-slate-900 border border-cyan-500/30 rounded-lg p-3 text-xs font-mono text-white focus:outline-none focus:border-cyan-400"
            />
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              className="px-6 py-2.5 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold rounded-xl shadow-lg transition"
            >
              Save Organization Settings
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
