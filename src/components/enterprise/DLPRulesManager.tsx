import React, { useState } from 'react';
import { ShieldAlert, Lock, AlertTriangle, Eye, RefreshCw, CheckCircle2 } from 'lucide-react';

interface DLPRule {
  id: string;
  name: string;
  category: 'PII' | 'PHI' | 'FINANCIAL' | 'CREDENTIAL';
  action: 'BLOCK' | 'REDACT' | 'AUDIT_ONLY';
  isEnabled: boolean;
}

export const DLPRulesManager: React.FC = () => {
  const [rules, setRules] = useState<DLPRule[]>([
    { id: '1', name: 'Social Security Numbers (SSN)', category: 'PII', action: 'REDACT', isEnabled: true },
    { id: '2', name: 'Credit Card & PCI-DSS Numbers', category: 'FINANCIAL', action: 'BLOCK', isEnabled: true },
    { id: '3', name: 'AWS & GCP API Access Keys', category: 'CREDENTIAL', action: 'BLOCK', isEnabled: true },
    { id: '4', name: 'Medical Health Records (ICD-10)', category: 'PHI', action: 'REDACT', isEnabled: false },
  ]);

  const toggleRule = (id: string) => {
    setRules(rules.map(r => r.id === id ? { ...r, isEnabled: !r.isEnabled } : r));
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-xl">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <ShieldAlert className="h-6 w-6 text-red-400" />
          <div>
            <h2 className="text-lg font-bold text-white">Data Loss Prevention (DLP) Rules</h2>
            <p className="text-xs text-slate-400">Automated scanning & redaction policies for chat and uploaded files</p>
          </div>
        </div>
        <button className="flex items-center gap-2 rounded-xl bg-red-500/20 px-4 py-2 text-xs font-semibold text-red-300 hover:bg-red-500/30">
          <RefreshCw className="h-4 w-4" /> Reset Defaults
        </button>
      </div>

      <div className="mt-6 space-y-3">
        {rules.map((rule) => (
          <div key={rule.id} className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/60 p-4 transition-all hover:border-slate-700">
            <div className="flex items-center gap-4">
              <div className={`rounded-lg p-2.5 ${rule.isEnabled ? 'bg-red-500/20 text-red-400' : 'bg-slate-800 text-slate-500'}`}>
                <Lock className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white">{rule.name}</h3>
                <span className="text-xs text-slate-400">Category: {rule.category} | Action: {rule.action}</span>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => toggleRule(rule.id)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${rule.isEnabled ? 'bg-cyan-500' : 'bg-slate-800'}`}
              >
                <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${rule.isEnabled ? 'translate-x-6' : 'translate-x-1'}`} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
