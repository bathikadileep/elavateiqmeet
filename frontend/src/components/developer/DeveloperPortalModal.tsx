import React, { useState, useEffect, useCallback } from 'react';
import { X, Code, Key, Webhook, Send, Trash2, Plus, Copy, Check, Activity, Shield } from 'lucide-react';
import client from '../../api/client';
import type { APIKeyItem, WebhookItem, WebhookLogItem } from '../../types/developer';

export interface DeveloperPortalModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const DeveloperPortalModal: React.FC<DeveloperPortalModalProps> = ({ isOpen, onClose }) => {
  const [activeTab, setActiveTab] = useState<'keys' | 'webhooks' | 'logs'>('keys');
  const [apiKeys, setApiKeys] = useState<APIKeyItem[]>([]);
  const [webhooks, setWebhooks] = useState<WebhookItem[]>([]);
  const [deliveryLogs, setDeliveryLogs] = useState<WebhookLogItem[]>([]);
  
  // Forms
  const [keyName, setKeyName] = useState('');
  const [rateLimit, setRateLimit] = useState(100);
  const [newRawKey, setNewRawKey] = useState<string | null>(null);
  
  const [targetUrl, setTargetUrl] = useState('');
  const [selectedEvents, setSelectedEvents] = useState<string[]>(['meeting.created', 'recording.ready']);
  const [newWebhookSecret, setNewWebhookSecret] = useState<string | null>(null);
  
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchDeveloperData = useCallback(async () => {
    try {
      setLoading(true);
      const [keysRes, whRes] = await Promise.all([
        client.get<APIKeyItem[]>('/api/developer/keys'),
        client.get<{ subscriptions: WebhookItem[]; delivery_logs: WebhookLogItem[] }>('/api/developer/webhooks'),
      ]);
      setApiKeys(keysRes.data);
      setWebhooks(whRes.data.subscriptions);
      setDeliveryLogs(whRes.data.delivery_logs);
    } catch (err) {
      console.warn('Failed fetching developer data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isOpen) {
      fetchDeveloperData();
    }
  }, [isOpen, fetchDeveloperData]);

  if (!isOpen) return null;

  const handleCreateKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!keyName.trim()) return;
    try {
      const res = await client.post<APIKeyItem>('/api/developer/keys', {
        key_name: keyName.trim(),
        rate_limit: rateLimit,
      });
      setKeyName('');
      if (res.data.raw_api_key) {
        setNewRawKey(res.data.raw_api_key);
      }
      fetchDeveloperData();
    } catch (err) {
      console.warn('Failed creating API key:', err);
    }
  };

  const handleRevokeKey = async (id: string) => {
    try {
      await client.delete(`/api/developer/keys/${id}`);
      fetchDeveloperData();
    } catch (err) {
      console.warn('Failed revoking API key:', err);
    }
  };

  const handleRegisterWebhook = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetUrl.trim()) return;
    try {
      const res = await client.post<WebhookItem>('/api/developer/webhooks', {
        target_url: targetUrl.trim(),
        events: selectedEvents,
      });
      setTargetUrl('');
      if (res.data.secret_token) {
        setNewWebhookSecret(res.data.secret_token);
      }
      fetchDeveloperData();
    } catch (err) {
      console.warn('Failed registering webhook:', err);
    }
  };

  const handleTestWebhook = async () => {
    try {
      await client.post('/api/developer/webhooks/test', { event: 'meeting.created' });
      fetchDeveloperData();
    } catch (err) {
      console.warn('Failed triggering test webhook:', err);
    }
  };

  const copyToClipboard = (str: string, id: string) => {
    navigator.clipboard.writeText(str);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-4xl max-h-[90vh] rounded-3xl glass-card border border-white/10 bg-[#080911]/95 p-6 text-white shadow-2xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-white/10 mb-4">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-2xl bg-cyan-500/20 border border-cyan-500/30 text-cyan-400">
              <Code className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white tracking-tight">Developer API Gateway & Webhooks</h2>
              <p className="text-xs text-gray-400">Token Bucket Rate Limiting, Scoped API Keys & HMAC-SHA256 Outbound Webhooks</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation */}
        <div className="flex items-center gap-2 mb-4 border-b border-white/10 pb-3">
          {[
            { id: 'keys', label: 'API Keys', icon: Key },
            { id: 'webhooks', label: 'Outbound Webhooks', icon: Webhook },
            { id: 'logs', label: 'Delivery Logs', icon: Activity },
          ].map((tab) => {
            const Icon = tab.icon;
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all cursor-pointer ${
                  active
                    ? 'bg-cyan-600 text-white shadow-md'
                    : 'bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white'
                }`}
              >
                <Icon className="w-4 h-4" /> {tab.label}
              </button>
            );
          })}
        </div>

        {/* Tab Contents */}
        <div className="flex-1 overflow-y-auto pr-1 space-y-4">
          {activeTab === 'keys' && (
            <div className="space-y-4">
              {newRawKey && (
                <div className="p-4 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 text-xs space-y-2">
                  <div className="font-bold flex items-center justify-between">
                    <span>⚠️ Save your API Key secret now (it won't be shown again!):</span>
                    <button
                      onClick={() => copyToClipboard(newRawKey, 'raw-key')}
                      className="flex items-center gap-1 text-[11px] hover:underline"
                    >
                      {copiedId === 'raw-key' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      Copy Secret
                    </button>
                  </div>
                  <code className="block p-2 rounded-lg bg-black/50 font-mono text-cyan-200 break-all">{newRawKey}</code>
                </div>
              )}

              <form onSubmit={handleCreateKey} className="flex gap-2">
                <input
                  type="text"
                  value={keyName}
                  onChange={(e) => setKeyName(e.target.value)}
                  placeholder="Key Name (e.g. Production Backend)"
                  className="flex-1 px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white text-xs placeholder-gray-500 focus:outline-none focus:border-cyan-500"
                />
                <button
                  type="submit"
                  className="px-4 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs cursor-pointer shadow-md flex items-center gap-1.5"
                >
                  <Plus className="w-4 h-4" /> Generate Key
                </button>
              </form>

              <div className="space-y-2">
                {apiKeys.map((key) => (
                  <div key={key.id} className="p-3.5 rounded-xl bg-white/5 border border-white/10 flex items-center justify-between text-xs">
                    <div>
                      <h4 className="font-bold text-white">{key.key_name}</h4>
                      <p className="text-gray-400 text-[11px] mt-0.5">Prefix: <code className="font-mono text-cyan-400">{key.key_prefix}...</code> • Rate Limit: {key.rate_limit} req/min</p>
                    </div>
                    <button
                      onClick={() => handleRevokeKey(key.id)}
                      className="p-2 rounded-lg bg-rose-500/20 text-rose-400 hover:bg-rose-500/30 transition-colors cursor-pointer"
                      title="Revoke Key"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'webhooks' && (
            <div className="space-y-4">
              {newWebhookSecret && (
                <div className="p-4 rounded-2xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs space-y-2">
                  <div className="font-bold flex items-center justify-between">
                    <span>🔐 HMAC Secret Token generated:</span>
                    <button
                      onClick={() => copyToClipboard(newWebhookSecret, 'wh-secret')}
                      className="flex items-center gap-1 text-[11px] hover:underline"
                    >
                      {copiedId === 'wh-secret' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      Copy Token
                    </button>
                  </div>
                  <code className="block p-2 rounded-lg bg-black/50 font-mono text-indigo-200 break-all">{newWebhookSecret}</code>
                </div>
              )}

              <form onSubmit={handleRegisterWebhook} className="space-y-3">
                <div className="flex gap-2">
                  <input
                    type="url"
                    value={targetUrl}
                    onChange={(e) => setTargetUrl(e.target.value)}
                    placeholder="Webhook Target URL (https://api.yourcompany.com/webhooks)"
                    className="flex-1 px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white text-xs placeholder-gray-500 focus:outline-none focus:border-cyan-500"
                  />
                  <button
                    type="submit"
                    className="px-4 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs cursor-pointer shadow-md"
                  >
                    Subscribe Endpoint
                  </button>
                </div>
              </form>

              <div className="flex items-center justify-between pt-2 border-t border-white/10">
                <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider">Active Webhook Subscriptions</h4>
                <button
                  onClick={handleTestWebhook}
                  className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center gap-1 cursor-pointer"
                >
                  <Send className="w-3.5 h-3.5" /> Trigger Test Webhook
                </button>
              </div>

              <div className="space-y-2">
                {webhooks.map((wh) => (
                  <div key={wh.id} className="p-3.5 rounded-xl bg-white/5 border border-white/10 text-xs space-y-1">
                    <div className="font-bold text-white font-mono">{wh.target_url}</div>
                    <div className="flex items-center gap-2 text-gray-400 text-[11px]">
                      <span>Events: {wh.events.join(', ')}</span>
                      <span>•</span>
                      <span className="text-emerald-400 font-semibold">HMAC-SHA256 Signed</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'logs' && (
            <div className="space-y-2">
              <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Outbound Delivery Logs</h3>
              {deliveryLogs.length === 0 ? (
                <div className="text-center py-12 text-xs text-gray-400">No webhook delivery logs recorded yet.</div>
              ) : (
                deliveryLogs.map((log) => (
                  <div key={log.id} className="p-3 rounded-xl bg-white/5 border border-white/10 flex items-center justify-between text-xs">
                    <div>
                      <span className="font-bold text-cyan-300">{log.event_type}</span>
                      <p className="text-gray-400 text-[11px] mt-0.5">Status: {log.status_code || 200} • Attempts: {log.attempts}</p>
                    </div>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${log.is_success ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'}`}>
                      {log.is_success ? 'DELIVERED' : 'FAILED'}
                    </span>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DeveloperPortalModal;
