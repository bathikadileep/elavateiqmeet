import React from 'react';
import { Globe, MapPin, ShieldCheck, AlertCircle } from 'lucide-react';

interface GeoLocationEntry {
  ip: string;
  country: string;
  city: string;
  isVpn: boolean;
  timestamp: string;
}

export const IPGeolocationMap: React.FC = () => {
  const entries: GeoLocationEntry[] = [
    { ip: '192.168.1.100', country: 'United States', city: 'San Francisco', isVpn: false, timestamp: '10:45 AM' },
    { ip: '10.0.4.15', country: 'United States', city: 'New York', isVpn: false, timestamp: '10:42 AM' },
    { ip: '185.220.101.4', country: 'Germany', city: 'Frankfurt', isVpn: true, timestamp: '10:30 AM' },
  ];

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-xl">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <Globe className="h-6 w-6 text-indigo-400" />
          <div>
            <h2 className="text-lg font-bold text-white">Geographic IP Access Map</h2>
            <p className="text-xs text-slate-400">Real-time geolocation & VPN/Proxy anomaly detection</p>
          </div>
        </div>
        <span className="rounded-full bg-indigo-500/20 px-3 py-1 text-xs font-semibold text-indigo-300">
          Geofence Active: US, CA, EU
        </span>
      </div>

      <div className="mt-6 space-y-3">
        {entries.map((item, i) => (
          <div key={i} className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/60 p-4">
            <div className="flex items-center gap-3">
              <MapPin className={`h-5 w-5 ${item.isVpn ? 'text-amber-400' : 'text-emerald-400'}`} />
              <div>
                <span className="font-mono text-sm font-semibold text-white">{item.ip}</span>
                <div className="text-xs text-slate-400">{item.city}, {item.country}</div>
              </div>
            </div>
            <div className="flex items-center gap-3 text-xs">
              {item.isVpn && (
                <span className="flex items-center gap-1 rounded bg-amber-500/20 px-2.5 py-1 text-amber-300">
                  <AlertCircle className="h-3.5 w-3.5" /> VPN / Proxy
                </span>
              )}
              <span className="text-slate-500">{item.timestamp}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
