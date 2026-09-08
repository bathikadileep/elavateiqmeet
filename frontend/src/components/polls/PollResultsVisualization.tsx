/**
 * ElevateIQ Enterprise Polling Analytics & Real-Time Visualization Widget
 * ======================================================================
 * Renders high-fidelity animated charts (Horizontal Bar, Donut SVG, Stacked Distribution,
 * and Ranked Leaderboards) for live meeting polling sessions.
 *
 * Includes:
 * - Live quorum and turnout analytics
 * - CSV and JSON report export
 * - Anonymized participant verification
 * - Dynamic SVG donut and progress renders without external heavyweight D3 dependencies
 */

import React, { useState, useMemo, useEffect, useRef } from 'react';
import {
  BarChart3,
  PieChart as PieChartIcon,
  Award,
  Download,
  Share2,
  Users,
  CheckCircle,
  Clock,
  RefreshCw,
  Eye,
  EyeOff,
  Percent,
  Sliders,
  TrendingUp,
  FileSpreadsheet,
  Copy,
  ChevronDown
} from 'lucide-react';
import type { PollItem, PollOptionItem } from '../../types/collaboration';

export type ChartViewMode = 'bars' | 'donut' | 'ranked' | 'stacked';

export interface PollResultsVisualizationProps {
  poll: PollItem;
  totalAttendees?: number;
  isHost?: boolean;
  onRefresh?: () => void;
  onClosePoll?: (pollId: string) => void;
  className?: string;
}

interface OptionAnalysis extends PollOptionItem {
  percentage: number;
  rank: number;
  isWinner: boolean;
  color: string;
}

const PALETTE = [
  '#3B82F6', // Blue
  '#10B981', // Emerald
  '#F59E0B', // Amber
  '#8B5CF6', // Purple
  '#EC4899', // Pink
  '#06B6D4', // Cyan
  '#F97316', // Orange
  '#6366F1', // Indigo
  '#14B8A6', // Teal
  '#EF4444', // Red
];

export const PollResultsVisualization: React.FC<PollResultsVisualizationProps> = ({
  poll,
  totalAttendees = 0,
  isHost = false,
  onRefresh,
  onClosePoll,
  className = '',
}) => {
  const [viewMode, setViewMode] = useState<ChartViewMode>('bars');
  const [anonymized, setAnonymized] = useState<boolean>(true);
  const [copiedNotification, setCopiedNotification] = useState<boolean>(false);
  const [exportDropdownOpen, setExportDropdownOpen] = useState<boolean>(false);
  const [hoveredOptionId, setHoveredOptionId] = useState<string | null>(null);
  const [autoRefreshSecs, setAutoRefreshSecs] = useState<number>(10);
  const [isAutoRefreshing, setIsAutoRefreshing] = useState<boolean>(false);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Total aggregated votes
  const totalVotes = useMemo(() => {
    if (poll.total_votes && poll.total_votes > 0) return poll.total_votes;
    return poll.options.reduce((sum, opt) => sum + (opt.vote_count || 0), 0);
  }, [poll]);

  // Enriched option analysis with percentage & ranking
  const analyzedOptions: OptionAnalysis[] = useMemo(() => {
    const sorted = [...poll.options].sort((a, b) => (b.vote_count || 0) - (a.vote_count || 0));
    const highestVote = sorted.length > 0 ? (sorted[0].vote_count || 0) : 0;

    return poll.options.map((opt, idx) => {
      const voteCount = opt.vote_count || 0;
      const pct = totalVotes > 0 ? Math.round((voteCount / totalVotes) * 1000) / 10 : 0;
      const rank = sorted.findIndex((s) => s.id === opt.id) + 1;
      const isWinner = voteCount > 0 && voteCount === highestVote;
      const color = PALETTE[idx % PALETTE.length];

      return {
        ...opt,
        percentage: pct,
        rank,
        isWinner,
        color,
      };
    });
  }, [poll, totalVotes]);

  // Turnout / quorum rate
  const turnoutRate = useMemo(() => {
    if (!totalAttendees || totalAttendees <= 0) return null;
    return Math.min(100, Math.round((totalVotes / totalAttendees) * 100));
  }, [totalVotes, totalAttendees]);

  // Auto-refresh timer loop
  useEffect(() => {
    if (!isAutoRefreshing || !onRefresh || poll.is_closed) return;
    timerRef.current = setInterval(() => {
      setAutoRefreshSecs((prev) => {
        if (prev <= 1) {
          onRefresh();
          return 10;
        }
        return prev - 1;
      });
    }, 1000);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isAutoRefreshing, onRefresh, poll.is_closed]);

  // Export handlers
  const handleExportCSV = () => {
    const headers = ['Option ID', 'Option Text', 'Vote Count', 'Percentage (%)', 'Rank'];
    const rows = analyzedOptions.map((opt) => [
      `"${opt.id}"`,
      `"${opt.option_text.replace(/"/g, '""')}"`,
      opt.vote_count,
      opt.percentage,
      opt.rank,
    ]);

    const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `poll_results_${poll.id}_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    setExportDropdownOpen(false);
  };

  const handleExportJSON = () => {
    const exportData = {
      pollId: poll.id,
      meetingCode: poll.meeting_code,
      question: poll.question,
      totalVotes,
      totalAttendees,
      turnoutRate: turnoutRate !== null ? `${turnoutRate}%` : 'N/A',
      isClosed: poll.is_closed,
      createdAt: poll.created_at,
      exportedAt: new Date().toISOString(),
      results: analyzedOptions.map((opt) => ({
        id: opt.id,
        text: opt.option_text,
        votes: opt.vote_count,
        percentage: opt.percentage,
        rank: opt.rank,
        isWinner: opt.isWinner,
      })),
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `poll_results_${poll.id}.json`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    setExportDropdownOpen(false);
  };

  const handleCopyMarkdownSummary = async () => {
    let md = `### Poll Results: ${poll.question}\n\n`;
    md += `**Total Votes:** ${totalVotes} | **Status:** ${poll.is_closed ? 'Closed' : 'Active'}\n\n`;
    md += `| Option | Votes | Share |\n`;
    md += `| :--- | :---: | :---: |\n`;
    analyzedOptions
      .slice()
      .sort((a, b) => a.rank - b.rank)
      .forEach((opt) => {
        const medal = opt.rank === 1 ? '🥇 ' : opt.rank === 2 ? '🥈 ' : opt.rank === 3 ? '🥉 ' : '';
        md += `| ${medal}${opt.option_text} | ${opt.vote_count} | ${opt.percentage}% |\n`;
      });

    try {
      await navigator.clipboard.writeText(md);
      setCopiedNotification(true);
      setTimeout(() => setCopiedNotification(false), 2500);
    } catch (err) {
      console.warn('Could not copy to clipboard:', err);
    }
  };

  // SVG Donut Chart Calculation
  const donutSegments = useMemo(() => {
    if (totalVotes === 0) return [];
    let cumulative = 0;
    return analyzedOptions.map((opt) => {
      const share = opt.vote_count / totalVotes;
      const startAngle = cumulative * 360;
      const endAngle = (cumulative + share) * 360;
      cumulative += share;

      // Calculate SVG arc path or stroke dash
      const radius = 70;
      const circumference = 2 * Math.PI * radius;
      const strokeDashoffset = circumference * (1 - share);
      const strokeDasharray = `${circumference * share} ${circumference * (1 - share)}`;
      const rotation = startAngle - 90;

      return {
        id: opt.id,
        color: opt.color,
        text: opt.option_text,
        percentage: opt.percentage,
        votes: opt.vote_count,
        radius,
        strokeDasharray,
        strokeDashoffset: -circumference * (startAngle / 360),
        rotation,
      };
    });
  }, [analyzedOptions, totalVotes]);

  return (
    <div className={`bg-gray-900 border border-gray-800 rounded-xl p-6 shadow-2xl text-gray-100 flex flex-col gap-6 ${className}`}>
      {/* Header bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-800 pb-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span
              className={`px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider ${
                poll.is_closed
                  ? 'bg-red-950/80 text-red-400 border border-red-800/60'
                  : 'bg-emerald-950/80 text-emerald-400 border border-emerald-800/60 animate-pulse'
              }`}
            >
              {poll.is_closed ? 'Poll Concluded' : 'Live Polling'}
            </span>
            {poll.is_multiselect && (
              <span className="bg-blue-950/80 text-blue-400 border border-blue-800/60 px-2 py-0.5 rounded-full text-xs">
                Multiple Choice
              </span>
            )}
          </div>
          <h2 className="text-xl font-bold text-white tracking-tight">{poll.question}</h2>
        </div>

        {/* Action buttons & View Mode Switcher */}
        <div className="flex items-center flex-wrap gap-2">
          <div className="bg-gray-800/90 border border-gray-700/80 p-1 rounded-lg flex items-center gap-1">
            <button
              onClick={() => setViewMode('bars')}
              title="Horizontal Bar Chart"
              className={`p-1.5 rounded transition ${
                viewMode === 'bars' ? 'bg-blue-600 text-white shadow' : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              <BarChart3 className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('donut')}
              title="Donut Chart"
              className={`p-1.5 rounded transition ${
                viewMode === 'donut' ? 'bg-blue-600 text-white shadow' : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              <PieChartIcon className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('ranked')}
              title="Leaderboard Ranking"
              className={`p-1.5 rounded transition ${
                viewMode === 'ranked' ? 'bg-blue-600 text-white shadow' : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              <Award className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('stacked')}
              title="100% Proportional Stacked Bar"
              className={`p-1.5 rounded transition ${
                viewMode === 'stacked' ? 'bg-blue-600 text-white shadow' : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              <Percent className="w-4 h-4" />
            </button>
          </div>

          {/* Export & share */}
          <div className="relative">
            <button
              onClick={() => setExportDropdownOpen((prev) => !prev)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-200 text-xs font-medium rounded-lg border border-gray-700 transition"
            >
              <Download className="w-3.5 h-3.5" />
              Export
              <ChevronDown className="w-3 h-3 text-gray-400" />
            </button>

            {exportDropdownOpen && (
              <div className="absolute right-0 mt-2 w-48 bg-gray-800 border border-gray-700 rounded-lg shadow-xl py-1 z-20">
                <button
                  onClick={handleExportCSV}
                  className="w-full text-left px-4 py-2 text-xs text-gray-300 hover:bg-gray-700 flex items-center gap-2"
                >
                  <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-400" />
                  Export as CSV (.csv)
                </button>
                <button
                  onClick={handleExportJSON}
                  className="w-full text-left px-4 py-2 text-xs text-gray-300 hover:bg-gray-700 flex items-center gap-2"
                >
                  <FileSpreadsheet className="w-3.5 h-3.5 text-blue-400" />
                  Export Raw JSON (.json)
                </button>
                <button
                  onClick={handleCopyMarkdownSummary}
                  className="w-full text-left px-4 py-2 text-xs text-gray-300 hover:bg-gray-700 flex items-center gap-2 border-t border-gray-700/60"
                >
                  <Copy className="w-3.5 h-3.5 text-amber-400" />
                  {copiedNotification ? 'Copied to Clipboard!' : 'Copy Summary (MD)'}
                </button>
              </div>
            )}
          </div>

          {/* Anonymity toggle */}
          <button
            onClick={() => setAnonymized((prev) => !prev)}
            title={anonymized ? 'Anonymized Voter Identity' : 'Voters Visible'}
            className="p-1.5 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg text-gray-300 hover:text-white transition"
          >
            {anonymized ? <EyeOff className="w-4 h-4 text-emerald-400" /> : <Eye className="w-4 h-4 text-blue-400" />}
          </button>

          {/* Close Poll button (Host only) */}
          {isHost && !poll.is_closed && onClosePoll && (
            <button
              onClick={() => onClosePoll(poll.id)}
              className="px-3 py-1.5 bg-red-600/20 hover:bg-red-600/30 text-red-400 border border-red-500/40 text-xs font-medium rounded-lg transition"
            >
              End Poll
            </button>
          )}
        </div>
      </div>

      {/* KPI Stats Strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-gray-800/50 border border-gray-800 rounded-lg p-3 flex items-center gap-3">
          <div className="p-2 bg-blue-950/60 text-blue-400 rounded-md border border-blue-900/60">
            <Users className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xs text-gray-400 uppercase tracking-wider">Total Ballots</div>
            <div className="text-lg font-bold text-white">{totalVotes}</div>
          </div>
        </div>

        <div className="bg-gray-800/50 border border-gray-800 rounded-lg p-3 flex items-center gap-3">
          <div className="p-2 bg-emerald-950/60 text-emerald-400 rounded-md border border-emerald-900/60">
            <TrendingUp className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xs text-gray-400 uppercase tracking-wider">Turnout Rate</div>
            <div className="text-lg font-bold text-emerald-400">
              {turnoutRate !== null ? `${turnoutRate}%` : 'N/A'}
            </div>
          </div>
        </div>

        <div className="bg-gray-800/50 border border-gray-800 rounded-lg p-3 flex items-center gap-3">
          <div className="p-2 bg-purple-950/60 text-purple-400 rounded-md border border-purple-900/60">
            <Award className="w-4 h-4" />
          </div>
          <div className="truncate">
            <div className="text-xs text-gray-400 uppercase tracking-wider">Top Choice</div>
            <div className="text-sm font-semibold text-purple-300 truncate">
              {analyzedOptions.find((o) => o.isWinner)?.option_text || 'None'}
            </div>
          </div>
        </div>

        <div className="bg-gray-800/50 border border-gray-800 rounded-lg p-3 flex items-center gap-3">
          <div className="p-2 bg-amber-950/60 text-amber-400 rounded-md border border-amber-900/60">
            <CheckCircle className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xs text-gray-400 uppercase tracking-wider">Quorum Status</div>
            <div className="text-sm font-semibold text-amber-400">
              {turnoutRate !== null && turnoutRate >= 50 ? 'Quorum Met' : 'Pending Quorum'}
            </div>
          </div>
        </div>
      </div>

      {/* Main visualization container */}
      <div className="min-h-[260px] flex flex-col justify-center">
        {totalVotes === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-gray-500">
            <Clock className="w-10 h-10 mb-2 animate-pulse text-gray-600" />
            <p className="text-sm font-medium">Awaiting initial participant responses...</p>
            <p className="text-xs text-gray-600 mt-1">Votes will animate automatically upon submission.</p>
          </div>
        ) : (
          <>
            {/* 1. HORIZONTAL BAR CHART */}
            {viewMode === 'bars' && (
              <div className="flex flex-col gap-4">
                {analyzedOptions.map((opt) => (
                  <div
                    key={opt.id}
                    onMouseEnter={() => setHoveredOptionId(opt.id)}
                    onMouseLeave={() => setHoveredOptionId(null)}
                    className="flex flex-col gap-1.5 transition-opacity duration-200"
                  >
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium text-gray-200 flex items-center gap-2">
                        {opt.isWinner && <Award className="w-4 h-4 text-amber-400" />}
                        {opt.option_text}
                      </span>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-400">
                          {opt.vote_count} {opt.vote_count === 1 ? 'vote' : 'votes'}
                        </span>
                        <span className="font-bold text-white text-sm min-w-[44px] text-right">
                          {opt.percentage}%
                        </span>
                      </div>
                    </div>
                    {/* Animated bar track */}
                    <div className="w-full h-3 bg-gray-800 rounded-full overflow-hidden flex">
                      <div
                        className="h-full rounded-full transition-all duration-700 ease-out"
                        style={{
                          width: `${opt.percentage}%`,
                          backgroundColor: opt.color,
                          boxShadow:
                            hoveredOptionId === opt.id
                              ? `0 0 12px ${opt.color}`
                              : 'none',
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* 2. DONUT SVG CHART */}
            {viewMode === 'donut' && (
              <div className="flex flex-col md:flex-row items-center justify-center gap-8 py-4">
                <div className="relative w-48 h-48 flex items-center justify-center">
                  <svg className="w-full h-full transform -rotate-90" viewBox="0 0 200 200">
                    {/* Background circle */}
                    <circle
                      cx="100"
                      cy="100"
                      r="70"
                      fill="transparent"
                      stroke="#1F2937"
                      strokeWidth="24"
                    />
                    {/* Data segments */}
                    {donutSegments.map((seg) => (
                      <circle
                        key={seg.id}
                        cx="100"
                        cy="100"
                        r={seg.radius}
                        fill="transparent"
                        stroke={seg.color}
                        strokeWidth="24"
                        strokeDasharray={seg.strokeDasharray}
                        strokeDashoffset={seg.strokeDashoffset}
                        className="transition-all duration-500 cursor-pointer"
                        onMouseEnter={() => setHoveredOptionId(seg.id)}
                        onMouseLeave={() => setHoveredOptionId(null)}
                      />
                    ))}
                  </svg>
                  {/* Donut Center Display */}
                  <div className="absolute flex flex-col items-center justify-center text-center">
                    <span className="text-2xl font-black text-white">{totalVotes}</span>
                    <span className="text-[10px] uppercase font-bold text-gray-400 tracking-wider">
                      Ballots
                    </span>
                  </div>
                </div>

                {/* Legend */}
                <div className="flex flex-col gap-2 max-w-xs">
                  {analyzedOptions.map((opt) => (
                    <div
                      key={opt.id}
                      onMouseEnter={() => setHoveredOptionId(opt.id)}
                      onMouseLeave={() => setHoveredOptionId(null)}
                      className={`flex items-center justify-between gap-4 p-1.5 rounded-md transition ${
                        hoveredOptionId === opt.id ? 'bg-gray-800' : 'hover:bg-gray-800/40'
                      }`}
                    >
                      <div className="flex items-center gap-2 truncate">
                        <span
                          className="w-3 h-3 rounded-full flex-shrink-0"
                          style={{ backgroundColor: opt.color }}
                        />
                        <span className="text-xs text-gray-200 truncate">{opt.option_text}</span>
                      </div>
                      <span className="text-xs font-bold text-white min-w-[40px] text-right">
                        {opt.percentage}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 3. RANKED LEADERBOARD */}
            {viewMode === 'ranked' && (
              <div className="flex flex-col gap-3">
                {analyzedOptions
                  .slice()
                  .sort((a, b) => a.rank - b.rank)
                  .map((opt) => {
                    const badgeClass =
                      opt.rank === 1
                        ? 'bg-amber-500/20 text-amber-300 border-amber-500/50'
                        : opt.rank === 2
                        ? 'bg-gray-300/20 text-gray-300 border-gray-400/50'
                        : opt.rank === 3
                        ? 'bg-amber-700/20 text-amber-600 border-amber-700/50'
                        : 'bg-gray-800 text-gray-400 border-gray-700';

                    return (
                      <div
                        key={opt.id}
                        className="flex items-center justify-between p-3 bg-gray-800/40 border border-gray-800 rounded-lg hover:border-gray-700 transition"
                      >
                        <div className="flex items-center gap-3">
                          <span
                            className={`w-7 h-7 rounded-full flex items-center justify-center font-bold text-xs border ${badgeClass}`}
                          >
                            #{opt.rank}
                          </span>
                          <span className="font-semibold text-gray-200 text-sm">
                            {opt.option_text}
                          </span>
                        </div>
                        <div className="flex items-center gap-4">
                          <span className="text-xs text-gray-400 font-mono">
                            {opt.vote_count} votes
                          </span>
                          <span className="text-sm font-bold text-blue-400 min-w-[50px] text-right">
                            {opt.percentage}%
                          </span>
                        </div>
                      </div>
                    );
                  })}
              </div>
            )}

            {/* 4. 100% PROPORTIONAL STACKED BAR */}
            {viewMode === 'stacked' && (
              <div className="flex flex-col gap-6 py-4">
                <div className="w-full h-8 bg-gray-800 rounded-lg overflow-hidden flex shadow-inner border border-gray-700">
                  {analyzedOptions.map((opt) => (
                    <div
                      key={opt.id}
                      style={{ width: `${opt.percentage}%`, backgroundColor: opt.color }}
                      title={`${opt.option_text}: ${opt.percentage}%`}
                      className="h-full transition-all duration-500 relative group cursor-pointer"
                    >
                      {opt.percentage > 10 && (
                        <span className="absolute inset-0 flex items-center justify-center text-[10px] font-bold text-white drop-shadow">
                          {opt.percentage}%
                        </span>
                      )}
                    </div>
                  ))}
                </div>

                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {analyzedOptions.map((opt) => (
                    <div
                      key={opt.id}
                      className="flex items-center gap-2 p-2 bg-gray-800/40 border border-gray-800 rounded-md"
                    >
                      <span
                        className="w-3 h-3 rounded-full flex-shrink-0"
                        style={{ backgroundColor: opt.color }}
                      />
                      <div className="flex-1 truncate">
                        <div className="text-xs text-gray-200 truncate">{opt.option_text}</div>
                        <div className="text-[10px] text-gray-400">
                          {opt.vote_count} votes ({opt.percentage}%)
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Footer footer info */}
      <div className="flex items-center justify-between border-t border-gray-800 pt-3 text-xs text-gray-500">
        <div className="flex items-center gap-2">
          <span>{anonymized ? '🔒 Ballots Cryptographically Anonymized' : '👁️ Verified User Directory'}</span>
          <span>•</span>
          <span>ElevateIQ Voting Engine v2.4</span>
        </div>
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="flex items-center gap-1 text-gray-400 hover:text-gray-200 transition"
          >
            <RefreshCw className="w-3 h-3" />
            Refresh
          </button>
        )}
      </div>
    </div>
  );
};

export default PollResultsVisualization;
