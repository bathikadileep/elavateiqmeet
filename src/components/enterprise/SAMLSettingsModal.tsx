import React, { useState } from 'react';
import { ShieldCheck, Server, Key, Copy, Check, Lock, AlertCircle } from 'lucide-react';

interface SAMLConfig {
  entityId: string;
  ssoUrl: string;
  x509Cert: string;
  attributeMapping: {
    email: string;
    firstName: string;
    lastName: string;
  };
}

export const SAMLSettingsModal: React.FC<{ isOpen: boolean; onClose: () => void }> = ({ isOpen, onClose }) => {
  const [config, setConfig] = useState<SAMLConfig>({
    entityId: 'https://idp.okta.com/exk12345',
    ssoUrl: 'https://idp.okta.com/app/sso',
    x509Cert: '-----BEGIN CERTIFICATE-----\nMIIC...=\n-----END CERTIFICATE-----',
    attributeMapping: {
      email: 'urn:oid:0.9.2342.19200300.100.1.3',
      firstName: 'urn:oid:2.5.4.42',
      lastName: 'urn:oid:2.5.4.4',
    },
  });

  const [copied, setCopied] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const spMetadataUrl = 'https://meet.elevateiq.com/saml/metadata';
  const acsUrl = 'https://meet.elevateiq.com/saml/acs';

  const handleCopyACS = () => {
    navigator.clipboard.writeText(acsUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSave = () => {
    setIsSaving(true);
    setTimeout(() => {
      setIsSaving(false);
      onClose();
    }, 800);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-md p-4">
      <div className="w-full max-w-2xl rounded-2xl border border-cyan-500/30 bg-slate-900/90 p-6 text-white shadow-2xl backdrop-blur-xl">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-3">
            <ShieldCheck className="h-6 w-6 text-cyan-400" />
            <h2 className="text-xl font-bold tracking-tight">SAML 2.0 Identity Provider Settings</h2>
          </div>
          <button onClick={onClose} className="rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-white">✕</button>
        </div>

        <div className="mt-6 space-y-5">
          <div className="rounded-xl border border-cyan-500/20 bg-cyan-950/20 p-4">
            <h3 className="text-sm font-semibold text-cyan-300">Service Provider (SP) Endpoints</h3>
            <div className="mt-3 grid gap-3 text-xs">
              <div>
                <span className="text-slate-400">ACS URL:</span>
                <div className="mt-1 flex items-center justify-between rounded-lg bg-slate-950 p-2 font-mono text-cyan-200">
                  <span>{acsUrl}</span>
                  <button onClick={handleCopyACS} className="flex items-center gap-1 rounded bg-cyan-500/20 px-2 py-1 text-cyan-300 hover:bg-cyan-500/30">
                    {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                    <span>{copied ? 'Copied' : 'Copy'}</span>
                  </button>
                </div>
              </div>
              <div>
                <span className="text-slate-400">Entity ID:</span>
                <div className="mt-1 rounded-lg bg-slate-950 p-2 font-mono text-slate-300">{spMetadataUrl}</div>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300">IdP Entity ID</label>
              <input
                type="text"
                value={config.entityId}
                onChange={(e) => setConfig({ ...config, entityId: e.target.value })}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300">IdP Single Sign-On (SSO) URL</label>
              <input
                type="text"
                value={config.ssoUrl}
                onChange={(e) => setConfig({ ...config, ssoUrl: e.target.value })}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300">X.509 Certificate (PEM Format)</label>
              <textarea
                rows={3}
                value={config.x509Cert}
                onChange={(e) => setConfig({ ...config, x509Cert: e.target.value })}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 p-3 font-mono text-xs text-slate-300 focus:border-cyan-500 focus:outline-none"
              />
            </div>
          </div>
        </div>

        <div className="mt-6 flex justify-end gap-3 border-t border-slate-800 pt-4">
          <button onClick={onClose} className="rounded-xl border border-slate-700 px-4 py-2 text-sm text-slate-300 hover:bg-slate-800">
            Cancel
          </button>
          <button onClick={handleSave} disabled={isSaving} className="flex items-center gap-2 rounded-xl bg-cyan-500 px-5 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400">
            {isSaving ? 'Saving...' : 'Save SAML Config'}
          </button>
        </div>
      </div>
    </div>
  );
};
