import { X } from 'lucide-react';
import { deleteHolding } from '../api/client';
import type { Holding } from '../types';

interface HoldingsProps {
  holdings: Holding[];
  onUpdate: () => void;
}

export function Holdings({ holdings, onUpdate }: HoldingsProps) {
  const handleDelete = async (ticker: string) => {
    try {
      await deleteHolding(ticker);
      onUpdate();
    } catch (e) {
      console.error('Delete failed', e);
    }
  };

  return (
    <div className="flex flex-col gap-0.5">
      {holdings.map((h, i) => {
        const isPositive = h.gain_loss_pct >= 0;
        const glColor = isPositive ? 'text-green' : 'text-red';
        const arrow = isPositive ? '▲' : '▼';

        return (
          <div key={h.ticker}>
            <div className="flex items-center justify-between px-3 py-2.5 rounded-lg hover:bg-hover transition-colors group">
              {/* Left: ticker + name */}
              <div className="min-w-0 w-[110px]">
                <div className="text-sm font-bold text-text truncate">{h.ticker}</div>
                <div className="text-xs text-muted truncate">{h.name}</div>
              </div>

              {/* Mid: shares */}
              <div className="text-xs text-muted w-16 text-center">
                {h.shares % 1 === 0 ? h.shares : h.shares.toFixed(4).replace(/\.?0+$/, '')} sh
              </div>

              {/* Right: value + pct */}
              <div className="text-right">
                <div className="text-sm font-bold text-text">
                  ${h.market_value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </div>
                <div className={`text-xs font-semibold ${glColor}`}>
                  {arrow} {Math.abs(h.gain_loss_pct).toFixed(2)}%
                </div>
              </div>

              {/* Delete */}
              <button
                onClick={() => handleDelete(h.ticker)}
                className="ml-2 p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-red/10 hover:text-red text-muted transition-all"
                aria-label={`Remove ${h.ticker}`}
              >
                <X size={13} />
              </button>
            </div>

            {/* Gradient divider */}
            {i < holdings.length - 1 && (
              <div className="h-px mx-3 bg-gradient-to-r from-transparent via-green to-transparent opacity-10" />
            )}
          </div>
        );
      })}
    </div>
  );
}
