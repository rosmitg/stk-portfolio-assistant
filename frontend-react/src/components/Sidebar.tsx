import { useState } from 'react';
import { Plus, X } from 'lucide-react';
import { Holdings } from './Holdings';
import { Charts } from './Charts';
import { addHolding, syncAlpaca, uploadCsv } from '../api/client';
import type { Holding } from '../types';

interface SidebarProps {
  holdings: Holding[];
  onUpdate: () => void;
}

type AddTab = 'manual' | 'alpaca' | 'csv';

export function Sidebar({ holdings, onUpdate }: SidebarProps) {
  const [showAdd, setShowAdd] = useState(false);
  const [addTab, setAddTab] = useState<AddTab>('manual');
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState('');

  // Manual form state
  const [ticker, setTicker] = useState('');
  const [shares, setShares] = useState('');
  const [avgCost, setAvgCost] = useState('');

  const totalValue = holdings.reduce((s, h) => s + h.market_value, 0);
  const totalGain  = holdings.reduce((s, h) => s + h.gain_loss, 0);
  const totalCost  = holdings.reduce((s, h) => s + h.avg_cost * h.shares, 0);
  const totalGainPct = totalCost ? (totalGain / totalCost) * 100 : 0;
  const isPositive = totalGain >= 0;

  const handleManualAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ticker.trim()) return;
    try {
      await addHolding({
        ticker: ticker.trim().toUpperCase(),
        name: ticker.trim().toUpperCase(),
        shares: parseFloat(shares),
        avg_cost: parseFloat(avgCost),
      });
      setTicker(''); setShares(''); setAvgCost('');
      setError('');
      onUpdate();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to add holding');
    }
  };

  const handleAlpaca = async () => {
    setSyncing(true);
    try {
      await syncAlpaca();
      setError('');
      onUpdate();
      setShowAdd(false);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Sync failed');
    } finally {
      setSyncing(false);
    }
  };

  const handleCsv = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      await uploadCsv(file);
      setError('');
      onUpdate();
      setShowAdd(false);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Upload failed');
    }
  };

  const fmt$ = (v: number) =>
    '$' + v.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  return (
    <aside className="w-[35%] min-w-[280px] max-w-[420px] bg-card border-r border-surface flex flex-col overflow-hidden">
      <div className="flex-1 overflow-y-auto px-4 py-5 space-y-4">

        {/* ── Portfolio value hero ── */}
        <div className="pb-4 border-b border-surface">
          <p className="text-[11px] font-semibold text-muted uppercase tracking-widest mb-1">Portfolio Value</p>
          <p className="text-3xl font-black text-text tracking-tight">{fmt$(totalValue)}</p>
          <p className={`text-sm font-semibold mt-1 ${isPositive ? 'text-green' : 'text-red'}`}>
            {isPositive ? '▲' : '▼'} {fmt$(Math.abs(totalGain))}
            <span className="ml-1">({totalGainPct >= 0 ? '+' : ''}{totalGainPct.toFixed(2)}%)</span>
            <span className="ml-1 text-muted font-normal text-xs">all time</span>
          </p>
        </div>

        {/* ── Holdings ── */}
        <div>
          <p className="text-[11px] font-bold text-muted uppercase tracking-widest mb-2">Holdings</p>
          <Holdings holdings={holdings} onUpdate={onUpdate} />
        </div>

        {/* ── Charts ── */}
        <Charts holdings={holdings} />

        {/* ── Add holdings ── */}
        <div>
          <button
            onClick={() => setShowAdd((v) => !v)}
            className="flex items-center gap-1.5 text-xs font-semibold text-green border border-green/40 rounded-lg px-3 py-1.5 hover:bg-green/8 transition-colors w-full justify-center"
          >
            {showAdd ? <X size={13} /> : <Plus size={13} />}
            {showAdd ? 'Close' : 'Add Holdings'}
          </button>

          {showAdd && (
            <div className="mt-3 bg-dark border border-surface rounded-xl p-4">
              {/* Tabs */}
              <div className="flex bg-card border border-surface rounded-lg p-0.5 mb-4">
                {(['manual', 'alpaca', 'csv'] as AddTab[]).map((t) => (
                  <button
                    key={t}
                    onClick={() => setAddTab(t)}
                    className={`flex-1 text-xs font-semibold py-1.5 rounded-md capitalize transition-all ${
                      addTab === t
                        ? 'bg-green text-dark'
                        : 'text-muted hover:text-text'
                    }`}
                  >
                    {t === 'alpaca' ? 'Alpaca' : t.charAt(0).toUpperCase() + t.slice(1)}
                  </button>
                ))}
              </div>

              {error && (
                <p className="text-xs text-red bg-red/8 border border-red/20 rounded-lg px-3 py-2 mb-3">{error}</p>
              )}

              {/* Manual */}
              {addTab === 'manual' && (
                <form onSubmit={handleManualAdd} className="space-y-2.5">
                  <input
                    className="w-full bg-card border border-surface rounded-lg px-3 py-2 text-sm text-text placeholder-muted focus:outline-none focus:border-green transition-colors"
                    placeholder="Ticker (e.g. AAPL)"
                    value={ticker}
                    onChange={(e) => setTicker(e.target.value)}
                    required
                  />
                  <div className="flex gap-2">
                    <input
                      className="flex-1 bg-card border border-surface rounded-lg px-3 py-2 text-sm text-text placeholder-muted focus:outline-none focus:border-green transition-colors"
                      placeholder="Shares"
                      type="number"
                      min="0.0001"
                      step="any"
                      value={shares}
                      onChange={(e) => setShares(e.target.value)}
                      required
                    />
                    <input
                      className="flex-1 bg-card border border-surface rounded-lg px-3 py-2 text-sm text-text placeholder-muted focus:outline-none focus:border-green transition-colors"
                      placeholder="Avg cost ($)"
                      type="number"
                      min="0.01"
                      step="any"
                      value={avgCost}
                      onChange={(e) => setAvgCost(e.target.value)}
                      required
                    />
                  </div>
                  <button
                    type="submit"
                    className="w-full bg-green text-dark font-bold text-sm py-2 rounded-lg hover:bg-green-light transition-colors"
                  >
                    Add Holding
                  </button>
                </form>
              )}

              {/* Alpaca */}
              {addTab === 'alpaca' && (
                <div className="space-y-3">
                  <p className="text-xs text-muted">Sync live positions from your Alpaca paper trading account.</p>
                  <button
                    onClick={handleAlpaca}
                    disabled={syncing}
                    className="w-full bg-green text-dark font-bold text-sm py-2 rounded-lg hover:bg-green-light disabled:opacity-50 transition-colors"
                  >
                    {syncing ? 'Syncing…' : 'Sync from Alpaca'}
                  </button>
                </div>
              )}

              {/* CSV */}
              {addTab === 'csv' && (
                <div className="space-y-2">
                  <p className="text-xs text-muted">
                    Upload a CSV with columns: <code className="bg-surface text-green px-1 rounded text-[11px]">ticker</code>{' '}
                    <code className="bg-surface text-green px-1 rounded text-[11px]">shares</code>{' '}
                    <code className="bg-surface text-green px-1 rounded text-[11px]">avg_cost</code>
                  </p>
                  <label className="flex items-center justify-center w-full border border-dashed border-surface rounded-lg py-6 cursor-pointer hover:border-green transition-colors text-muted text-xs">
                    <span>Click to choose CSV file</span>
                    <input type="file" accept=".csv" className="hidden" onChange={handleCsv} />
                  </label>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}
