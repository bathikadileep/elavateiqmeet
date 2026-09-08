import React, { useState } from 'react';

export const BillingDashboardPage: React.FC = () => {
  const [currentPlan] = useState('Enterprise Pro');
  const [billingCycle] = useState('Monthly');
  const [usageStats] = useState({
    meetingMinutes: 14200,
    storageGb: 450,
    aiTranscriptsMinutes: 2800,
    activeSeats: 142,
  });

  return (
    <div className="min-h-screen bg-[#080911] text-white p-8">
      <div className="max-w-5xl mx-auto space-y-8">
        <div>
          <h1 className="text-2xl font-bold text-cyan-400">💳 Billing, Subscription & Usage Metering</h1>
          <p className="text-sm text-gray-400 mt-1">Monitor tenant resource consumption, meeting minute quotas, and downloadable invoices.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="p-5 bg-[#121422] border border-cyan-500/20 rounded-2xl">
            <p className="text-xs text-gray-400">Active Plan</p>
            <p className="text-xl font-bold text-cyan-300 mt-1">{currentPlan}</p>
          </div>
          <div className="p-5 bg-[#121422] border border-cyan-500/20 rounded-2xl">
            <p className="text-xs text-gray-400">Meeting Minutes Used</p>
            <p className="text-xl font-bold text-cyan-300 mt-1">{usageStats.meetingMinutes.toLocaleString()} min</p>
          </div>
          <div className="p-5 bg-[#121422] border border-cyan-500/20 rounded-2xl">
            <p className="text-xs text-gray-400">Cloud Storage</p>
            <p className="text-xl font-bold text-cyan-300 mt-1">{usageStats.storageGb} GB / 1,000 GB</p>
          </div>
          <div className="p-5 bg-[#121422] border border-cyan-500/20 rounded-2xl">
            <p className="text-xs text-gray-400">Active Seats</p>
            <p className="text-xl font-bold text-cyan-300 mt-1">{usageStats.activeSeats} Users</p>
          </div>
        </div>

        <div className="p-6 bg-[#121422] border border-cyan-500/20 rounded-2xl space-y-4">
          <h2 className="text-lg font-semibold text-cyan-300">📄 Recent Invoices</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-gray-300">
              <thead className="bg-[#1a1d30] text-cyan-400 uppercase">
                <tr>
                  <th className="p-3">Invoice ID</th>
                  <th className="p-3">Billing Period</th>
                  <th className="p-3">Amount (USD)</th>
                  <th className="p-3">Status</th>
                  <th className="p-3">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                <tr>
                  <td className="p-3 font-mono">INV-2026-08-001</td>
                  <td className="p-3">Aug 1, 2026 - Aug 31, 2026</td>
                  <td className="p-3">$49.00</td>
                  <td className="p-3"><span className="px-2 py-0.5 bg-green-950 text-green-400 rounded-full font-semibold">Paid</span></td>
                  <td className="p-3"><button className="text-cyan-400 hover:underline">Download PDF</button></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
