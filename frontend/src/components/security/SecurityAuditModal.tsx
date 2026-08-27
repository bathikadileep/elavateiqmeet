import React, { useState, useEffect, useCallback } from 'react';
import { X, ShieldCheck, Lock, ShieldAlert, Key, Globe, RefreshCw, UserX } from 'lucide-react';
import client from '../../api/client';
import type { AuditLogItem, IPRuleItem, SSOProviderItem } from '../../types/security';

export interface SecurityAuditModalProps {
  isOpen: boolean;
  onClose: () => void;
  isE2EEEnabled: boolean;
  onToggleE2EE: () => void;
}

export const SecurityAuditModal: React.FC<SecurityAuditModalProps> = ({
  isOpen,
  onClose,
  isE2EEEnabled,
  onToggleE2EE,
}) => {
  const [activeTab, setActiveTab] = useState<'audit' | 'sso' | 'ip' | 'dlp'>('audit');
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([]);
  const [ssoProviders, setSsoProviders] = useState<SSOProviderItem[]>([]);
  const [ipRules, setIpRules] = useState<IPRuleItem[]>([]);
  const [newCidr, setNewCidr] = useState('');
  const [targetUserId, setTargetUserId] = useState('');
  const [revoking, setRevoking] = useState(false);
  const [loading, setLoading] = useState(false);

  const fetchSecurityData = useCallback(async () => {
    try {
      setLoading(true);
      const [logsRes, providersRes, ipRes] = await Promise.all([
        client.get<AuditLogItem[]>('/api/security/audit-logs'),
        client.get<SSOProviderItem[]>('/api/v1/auth/sso/providers'),
        client.get<IPRuleItem[]>('/api/security/ip-rules'),
      ]);
      setAuditLogs(logsRes.data);
      setSsoProviders(providersRes.data);
      setIpRules(ipRes.data);
    } catch (err) {
      console.warn('Failed fetching security data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isOpen) {
      fetchSecurityData();
    }
  }, [isOpen, fetchSecurityData]);

  if (!isOpen) return null;

  const handleAddIpRule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCidr.trim()) return;

    try {
      await client.post('/api/security/ip-rules', {
        cidr_range: newCidr.trim(),
        description: 'Enterprise Allowed Subnet',
      });
      setNewCidr('');
      fetchSecurityData();
    } catch (err) {
      console.warn('Failed adding IP rule:', err);
    }
  };

  const handleRevokeSession = async () => {
    if (!targetUserId.trim()) return;
    try {
      setRevoking(true);
      await client.post('/api/security/revoke-session', { user_id: targetUserId.trim() });
      setTargetUserId('');
      fetchSecurityData();
    } catch (err) {
      console.warn('Failed revoking session:', err);
    } finally {
      setRevoking(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-4xl max-h-[90vh] rounded-3xl glass-card border border-white/10 bg-[#080911]/95 p-6 text-white shadow-2xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-white/10 mb-4">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-2xl bg-emerald-500/20 border border-emerald-500/30 text-emerald-400">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
                Enterprise Security & Governance
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  SOC2 Certified
                </span>
              </h2>
              <p className="text-xs text-gray-400">Zero-trust E2EE, SSO Governance, DLP Scanner & Audit Stream</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onToggleE2EE}
              className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
                isE2EEEnabled
                  ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-500/30'
                  : 'bg-white/10 text-gray-300 hover:bg-white/20'
              }`}
            >
              <Lock className="w-4 h-4" /> {isE2EEEnabled ? 'AES-256 E2EE Active' : 'Enable E2EE Shield'}
            </button>

            <button
              onClick={onClose}
              className="p-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-2 mb-4 border-b border-white/10 pb-3">
          {[
            { id: 'audit', label: 'SOC2 Audit Stream', icon: ShieldCheck },
            { id: 'sso', label: 'OAuth2 / SSO', icon: Key },
            { id: 'ip', label: 'IP Restriction', icon: Globe },
            { id: 'dlp', label: 'DLP & Revocation', icon: ShieldAlert },
          ].map((tab) => {
            const Icon = tab.icon;
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all cursor-pointer ${
                  active
                    ? 'bg-indigo-600 text-white shadow-md'
                    : 'bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white'
                }`}
              >
                <Icon className="w-4 h-4" /> {tab.label}
              </button>
            );
          })}
        </div>

        {/* Tab Contents */}
        <div className="flex-1 overflow-y-auto pr-1 space-y-3">
          {activeTab === 'audit' && (
            <div className="space-y-2">
              <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Recent SOC2 Compliance Events</h3>
              {auditLogs.length === 0 ? (
                <div className="text-center py-12 text-xs text-gray-400">No security audit logs recorded yet.</div>
              ) : (
                auditLogs.map((log) => (
                  <div key={log.id} className="p-3 rounded-xl bg-white/5 border border-white/10 flex items-center justify-between text-xs">
                    <div>
                      <span className="font-bold text-indigo-300">{log.event_type}</span>
                      <p className="text-gray-400 text-[11px] mt-0.5">Actor ID: {log.actor_id || 'System'} • IP: {log.ip_address || '127.0.0.1'}</p>
                    </div>
                    <span className="text-[10px] text-gray-500 font-mono">{new Date(log.timestamp).toLocaleTimeString()}</span>
                  </div>
                ))
              )}
            </div>
          )}

          {activeTab === 'sso' && (
            <div className="space-y-3">
              <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider">Enterprise Identity Providers</h3>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {ssoProviders.map((p) => (
                  <div key={p.provider_name} className="p-4 rounded-2xl bg-white/5 border border-white/10 text-center space-y-2">
                    <Key className="w-8 h-8 mx-auto text-indigo-400" />
                    <h4 className="text-sm font-bold text-white">{p.display_name}</h4>
                    <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 text-[10px] font-semibold">Active & Enabled</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'ip' && (
            <div className="space-y-4">
              <form onSubmit={handleAddIpRule} className="flex gap-2">
                <input
                  type="text"
                  value={newCidr}
                  onChange={(e) => setNewCidr(e.target.value)}
                  placeholder="Enter CIDR range (e.g. 10.0.0.0/16)"
                  className="flex-1 px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white text-xs placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                />
                <button
                  type="submit"
                  className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs cursor-pointer shadow-md"
                >
                  Add IP Rule
                </button>
              </form>

              <div className="space-y-2">
                {ipRules.map((r) => (
                  <div key={r.id} className="p-3 rounded-xl bg-white/5 border border-white/10 flex items-center justify-between text-xs">
                    <div>
                      <span className="font-bold text-white font-mono">{r.cidr_range}</span>
                      <p className="text-gray-400 text-[11px]">{r.description}</p>
                    </div>
                    <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 text-[10px] font-bold">ALLOWED</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'dlp' && (
            <div className="space-y-4">
              <div className="p-4 rounded-2xl bg-white/5 border border-white/10 space-y-3">
                <h4 className="text-xs font-bold text-rose-400 uppercase tracking-wider flex items-center gap-2">
                  <UserX className="w-4 h-4" /> Emergency User Session Revocation
                </h4>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={targetUserId}
                    onChange={(e) => setTargetUserId(e.target.value)}
                    placeholder="Enter target User UUID"
                    className="flex-1 px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white text-xs placeholder-gray-500 focus:outline-none focus:border-rose-500"
                  />
                  <button
                    onClick={handleRevokeSession}
                    disabled={revoking}
                    className="px-4 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-semibold text-xs cursor-pointer shadow-md"
                  >
                    Revoke Active Session
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SecurityAuditModal;
