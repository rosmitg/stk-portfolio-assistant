import { useRef, useState } from 'react';
import { Zap, Upload, PenLine } from 'lucide-react';
import { addHolding, syncAlpaca, uploadCsv } from '../api/client';

type Panel = null | 'csv' | 'manual';

interface OnboardingProps {
  onComplete: () => void;
}

export function Onboarding({ onComplete }: OnboardingProps) {
  const [panel, setPanel] = useState<Panel>(null);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState('');
  const [added, setAdded] = useState<string[]>([]);

  // Manual form
  const [ticker, setTicker] = useState('');
  const [shares, setShares] = useState('');
  const [avgCost, setAvgCost] = useState('');

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleAlpaca = async () => {
    setSyncing(true);
    setError('');
    try {
      await syncAlpaca();
      onComplete();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Sync failed');
    } finally {
      setSyncing(false);
    }
  };

  const handleCsv = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setError('');
    try {
      await uploadCsv(file);
      onComplete();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Upload failed');
    }
  };

  const handleManualAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ticker.trim()) return;
    setError('');
    try {
      const { data } = await addHolding({
        ticker: ticker.trim().toUpperCase(),
        name: ticker.trim().toUpperCase(),
        shares: parseFloat(shares),
        avg_cost: parseFloat(avgCost),
      });
      setAdded((prev) => [...prev, `${data.ticker} — ${shares} shares @ $${avgCost}`]);
      setTicker(''); setShares(''); setAvgCost('');
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to add');
    }
  };

  const cards = [
    {
      id: 'alpaca' as const,
      icon: <Zap size={28} className="text-green" />,
      title: 'Connect Alpaca',
      desc: 'Pull live positions from your Alpaca paper trading account in one click.',
      action: (
        <button
          onClick={handleAlpaca}
          disabled={syncing}
          className="w-full bg-green text-dark font-bold text-sm py-2.5 rounded-xl hover:bg-green-light disabled:opacity-50 transition-colors mt-4"
        >
          {syncing ? 'Syncing…' : 'Sync Alpaca'}
        </button>
      ),
    },
    {
      id: 'csv' as const,
      icon: <Upload size={28} className="text-green" />,
      title: 'Upload CSV',
      desc: 'Import holdings from a CSV with columns: ticker, shares, avg_cost.',
      action: (
        <button
          onClick={() => setPanel(panel === 'csv' ? null : 'csv')}
          className="w-full bg-green text-dark font-bold text-sm py-2.5 rounded-xl hover:bg-green-light transition-colors mt-4"
        >
          Upload CSV
        </button>
      ),
    },
    {
      id: 'manual' as const,
      icon: <PenLine size={28} className="text-green" />,
      title: 'Add Manually',
      desc: 'Enter each holding by ticker, share count, and average cost.',
      action: (
        <button
          onClick={() => setPanel(panel === 'manual' ? null : 'manual')}
          className="w-full bg-green text-dark font-bold text-sm py-2.5 rounded-xl hover:bg-green-light transition-colors mt-4"
        >
          Add Manually
        </button>
      ),
    },
  ];

  return (
    <div className="flex-1 overflow-y-auto bg-dark flex flex-col items-center px-6 py-12">
      {/* Hero */}
      <p className="text-[11px] font-bold uppercase tracking-[0.14em] text-green mb-4">
        AI-Powered Portfolio Intelligence
      </p>
      <h1 className="text-5xl font-black text-text tracking-tight text-center leading-tight mb-3">
        Your portfolio.<br />Explained by AI.
      </h1>
      <p className="text-base text-muted mb-12 text-center">
        Connect your holdings and ask anything
      </p>

      {error && (
        <p className="text-sm text-red bg-red/8 border border-red/20 rounded-xl px-4 py-3 mb-6 max-w-lg w-full text-center">
          {error}
        </p>
      )}

      {/* Cards */}
      <div className="grid grid-cols-3 gap-5 max-w-2xl w-full">
        {cards.map((card) => (
          <div
            key={card.id}
            className={`bg-card border rounded-2xl p-6 text-center transition-all duration-150 ${
              panel === card.id
                ? 'border-green bg-green/4'
                : 'border-surface hover:border-green/60 hover:-translate-y-0.5'
            }`}
          >
            <div className="flex justify-center mb-3">{card.icon}</div>
            <h2 className="text-sm font-bold text-text mb-1">{card.title}</h2>
            <p className="text-xs text-muted leading-relaxed">{card.desc}</p>
            {card.action}
          </div>
        ))}
      </div>

      {/* Expansion panel */}
      {panel && (
        <div className="mt-8 max-w-lg w-full bg-card border border-surface rounded-2xl p-6">
          {/* CSV */}
          {panel === 'csv' && (
            <>
              <h3 className="text-sm font-bold text-text mb-1">Upload your CSV file</h3>
              <p className="text-xs text-muted mb-4">
                Required columns:{' '}
                {['ticker', 'shares', 'avg_cost'].map((c) => (
                  <code key={c} className="bg-surface text-green px-1.5 py-0.5 rounded text-[11px] mx-0.5">{c}</code>
                ))}
              </p>
              <label className="flex items-center justify-center w-full border-2 border-dashed border-surface rounded-xl py-8 cursor-pointer hover:border-green/60 transition-colors text-muted text-sm">
                <span>Click to choose CSV file</span>
                <input ref={fileInputRef} type="file" accept=".csv" className="hidden" onChange={handleCsv} />
              </label>
            </>
          )}

          {/* Manual */}
          {panel === 'manual' && (
            <>
              <h3 className="text-sm font-bold text-text mb-1">Add holdings manually</h3>
              <p className="text-xs text-muted mb-4">Add as many as you like, then click Done.</p>

              {added.map((note, i) => (
                <p key={i} className="text-xs text-green bg-green/8 border border-green/20 rounded-lg px-3 py-1.5 mb-2">
                  ✓ {note}
                </p>
              ))}

              <form onSubmit={handleManualAdd} className="space-y-2.5">
                <input
                  className="w-full bg-dark border border-surface rounded-xl px-4 py-2.5 text-sm text-text placeholder-muted focus:outline-none focus:border-green transition-colors"
                  placeholder="Ticker (e.g. AAPL)"
                  value={ticker}
                  onChange={(e) => setTicker(e.target.value)}
                  required
                />
                <div className="flex gap-2">
                  <input
                    className="flex-1 bg-dark border border-surface rounded-xl px-4 py-2.5 text-sm text-text placeholder-muted focus:outline-none focus:border-green transition-colors"
                    placeholder="Shares"
                    type="number" min="0.0001" step="any"
                    value={shares}
                    onChange={(e) => setShares(e.target.value)}
                    required
                  />
                  <input
                    className="flex-1 bg-dark border border-surface rounded-xl px-4 py-2.5 text-sm text-text placeholder-muted focus:outline-none focus:border-green transition-colors"
                    placeholder="Avg cost ($)"
                    type="number" min="0.01" step="any"
                    value={avgCost}
                    onChange={(e) => setAvgCost(e.target.value)}
                    required
                  />
                </div>
                <button
                  type="submit"
                  className="w-full bg-green text-dark font-bold text-sm py-2.5 rounded-xl hover:bg-green-light transition-colors"
                >
                  Add Holding
                </button>
              </form>

              {added.length > 0 && (
                <button
                  onClick={onComplete}
                  className="w-full mt-3 border border-green/40 text-green font-semibold text-sm py-2.5 rounded-xl hover:bg-green/8 transition-colors"
                >
                  Done — View Portfolio →
                </button>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
