import { useEffect, useState } from 'react';
import { RefreshCw, MessageSquare, Sparkles, AlertTriangle } from 'lucide-react';
import axios from 'axios';
import { getTodayBrief, generateBrief } from '../api/client';
import type { Brief, BriefSection } from '../types';

interface BriefPanelProps {
  /** Switch to the Chat tab and pre-load this text as the first message. */
  onChatAboutSection: (message: string) => void;
}

/** Colour the health score by band — green (healthy) → amber → red. */
function healthColor(score: number): string {
  if (score >= 70) return '#00D084';
  if (score >= 40) return '#FBBF24';
  return '#FF4757';
}

function sectionPrompt(section: BriefSection): string {
  const tickers = section.tickers.length ? ` (${section.tickers.join(', ')})` : '';
  return `Tell me more about this part of my daily brief — "${section.title}"${tickers}:\n\n${section.body}`;
}

export function BriefPanel({ onChatAboutSection }: BriefPanelProps) {
  const [brief, setBrief] = useState<Brief | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // On mount: fetch today's brief. A 404 simply means none exists yet.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const { data } = await getTodayBrief();
        if (!cancelled) setBrief(data);
      } catch (err) {
        if (cancelled) return;
        if (axios.isAxiosError(err) && err.response?.status === 404) {
          setBrief(null);
        } else {
          setError('Could not load your brief.');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const handleGenerate = async () => {
    setGenerating(true);
    setError(null);
    try {
      const { data } = await generateBrief();
      setBrief(data);
    } catch (err) {
      const detail =
        axios.isAxiosError(err) && typeof err.response?.data?.detail === 'string'
          ? err.response.data.detail
          : 'Brief generation failed. Please try again.';
      setError(detail);
    } finally {
      setGenerating(false);
    }
  };

  // ── Loading / generating state ──
  if (loading || generating) {
    return (
      <div className="flex-1 flex items-center justify-center bg-dark">
        <div className="text-center">
          <div className="flex gap-1.5 items-center justify-center mb-3">
            {[0, 1, 2].map((d) => (
              <span
                key={d}
                className="w-2 h-2 rounded-full bg-green animate-bounce"
                style={{ animationDelay: `${d * 150}ms` }}
              />
            ))}
          </div>
          <div className="text-sm text-muted">
            {generating ? 'Generating your brief… this can take ~a minute' : 'Loading your brief…'}
          </div>
        </div>
      </div>
    );
  }

  // ── Empty state — no brief yet ──
  if (!brief) {
    return (
      <div className="flex-1 flex items-center justify-center bg-dark px-6">
        <div className="text-center max-w-md">
          <div className="w-14 h-14 rounded-2xl bg-surface border border-surface2 flex items-center justify-center mx-auto mb-4">
            <Sparkles size={24} className="text-green" />
          </div>
          <h2 className="text-lg font-bold text-text mb-1.5">No brief yet today</h2>
          <p className="text-sm text-muted mb-5">
            Generate an AI-powered daily brief on your portfolio — health, key moves, news and alerts.
          </p>
          {error && <p className="text-sm text-red mb-4">{error}</p>}
          <button
            onClick={handleGenerate}
            className="inline-flex items-center gap-2 bg-green text-dark font-bold px-5 py-2.5 rounded-xl hover:bg-green-light transition-colors"
          >
            <Sparkles size={16} />
            Generate Brief
          </button>
        </div>
      </div>
    );
  }

  // ── Brief content ──
  const score = brief.portfolio_health;
  return (
    <div className="flex-1 overflow-y-auto bg-dark">
      <div className="max-w-3xl mx-auto px-6 py-6">
        {/* Header: health score + headline + refresh */}
        <div className="flex items-start justify-between gap-4 mb-6">
          <div className="flex items-center gap-4">
            <div className="flex flex-col items-center justify-center w-20 h-20 rounded-2xl bg-card border border-surface shrink-0">
              <span className="text-3xl font-black leading-none" style={{ color: healthColor(score) }}>
                {score}
              </span>
              <span className="text-[10px] text-muted2 mt-1">/ 100</span>
            </div>
            <div>
              <div className="text-[11px] font-semibold text-muted uppercase tracking-widest mb-1">
                Portfolio Health
              </div>
              <h1 className="text-lg font-bold text-text leading-snug">{brief.headline}</h1>
              <div className="text-xs text-muted2 mt-1">{brief.date}</div>
            </div>
          </div>
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="flex items-center gap-1.5 border border-surface text-muted text-xs px-3 py-2 rounded-xl hover:border-green hover:text-green transition-colors shrink-0"
            title="Regenerate brief"
          >
            <RefreshCw size={13} />
            Refresh
          </button>
        </div>

        {error && <p className="text-sm text-red mb-4">{error}</p>}

        {/* Alerts */}
        {brief.alerts.length > 0 && (
          <div className="space-y-2 mb-6">
            {brief.alerts.map((alert, i) => (
              <div
                key={i}
                className="flex items-start gap-2.5 bg-red/5 border border-red/25 rounded-xl px-4 py-3"
              >
                <AlertTriangle size={16} className="text-red shrink-0 mt-0.5" />
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-text">{alert.title}</span>
                    <span className="text-[10px] font-medium text-red bg-red/10 border border-red/25 px-1.5 py-0.5 rounded-full">
                      {alert.ticker}
                    </span>
                  </div>
                  <p className="text-[13px] text-muted mt-0.5 leading-relaxed">{alert.body}</p>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Sections */}
        <div className="space-y-4">
          {brief.sections.map((section, i) => (
            <div key={i} className="bg-card border border-surface rounded-2xl p-5">
              <div className="flex items-start justify-between gap-3 mb-2">
                <h3 className="text-sm font-bold text-text">{section.title}</h3>
                <button
                  onClick={() => onChatAboutSection(sectionPrompt(section))}
                  className="flex items-center gap-1.5 text-[11px] text-muted hover:text-green transition-colors shrink-0"
                  title="Discuss this in chat"
                >
                  <MessageSquare size={12} />
                  Chat about this
                </button>
              </div>
              {section.tickers.length > 0 && (
                <div className="flex flex-wrap gap-1 mb-2.5">
                  {section.tickers.map((t) => (
                    <span
                      key={t}
                      className="bg-green/8 border border-green/25 text-green text-[11px] font-medium px-2 py-0.5 rounded-full"
                    >
                      {t}
                    </span>
                  ))}
                </div>
              )}
              <p className="text-[13px] text-[#E0E6F0] leading-relaxed whitespace-pre-line">
                {section.body}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
