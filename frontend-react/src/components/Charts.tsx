import {
  PieChart, Pie, Cell, Tooltip as PieTooltip,
  BarChart, Bar, XAxis, YAxis, Tooltip as BarTooltip,
  ResponsiveContainer, ReferenceLine,
} from 'recharts';
import type { Holding } from '../types';

const TICKER_COLORS: Record<string, string> = {
  TSLA: '#00D084',
  AMZN: '#6366F1',
  NVDA: '#F59E0B',
  AAPL: '#EC4899',
  MSFT: '#3B82F6',
};
const FALLBACK_COLORS = ['#8B8FA8', '#A78BFA', '#34D399', '#FB7185', '#60A5FA', '#FBBF24', '#4ADE80', '#F472B6'];

function tickerColor(ticker: string, index: number): string {
  return TICKER_COLORS[ticker.toUpperCase()] ?? FALLBACK_COLORS[index % FALLBACK_COLORS.length];
}

const fmt$ = (v: number) =>
  '$' + v.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

interface ChartsProps {
  holdings: Holding[];
}

export function Charts({ holdings }: ChartsProps) {
  const donutData = holdings.map((h) => ({
    name: h.ticker,
    value: h.market_value,
  }));

  const barData = holdings.map((h) => ({
    ticker: h.ticker,
    pct: parseFloat(h.gain_loss_pct.toFixed(2)),
  }));

  return (
    <div className="flex flex-col gap-2">
      {/* ── Allocation donut ── */}
      <div>
        <p className="text-[11px] font-bold text-muted uppercase tracking-widest mb-1">Allocation</p>
        <ResponsiveContainer width="100%" height={180}>
          <PieChart>
            <Pie
              data={donutData}
              cx="40%"
              cy="50%"
              innerRadius={52}
              outerRadius={75}
              paddingAngle={2}
              dataKey="value"
            >
              {donutData.map((d, i) => (
                <Cell
                  key={i}
                  fill={tickerColor(d.name, i)}
                  stroke="transparent"
                />
              ))}
            </Pie>
            <PieTooltip
              formatter={(v) => [fmt$(Number(v)), 'Value']}
              contentStyle={{ background: '#111118', border: '1px solid #1E1E2E', borderRadius: 8, fontSize: 12 }}
              labelStyle={{ color: '#FFFFFF' }}
              itemStyle={{ color: '#8B8FA8' }}
            />
          </PieChart>
        </ResponsiveContainer>
        {/* Legend */}
        <div className="flex flex-wrap gap-x-3 gap-y-1 px-1">
          {donutData.map((d, i) => (
            <div key={d.name} className="flex items-center gap-1 text-xs text-muted">
              <span
                className="inline-block w-2 h-2 rounded-full"
                style={{ background: tickerColor(d.name, i) }}
              />
              {d.name}
            </div>
          ))}
        </div>
      </div>

      {/* ── Gain / Loss bar ── */}
      <div>
        <p className="text-[11px] font-bold text-muted uppercase tracking-widest mb-1 mt-2">Gain / Loss %</p>
        <ResponsiveContainer width="100%" height={160}>
          <BarChart data={barData} margin={{ top: 16, right: 8, left: -20, bottom: 0 }}>
            <XAxis
              dataKey="ticker"
              tick={{ fill: '#8B8FA8', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fill: '#8B8FA8', fontSize: 10 }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => `${v}%`}
            />
            <BarTooltip
              formatter={(v) => { const n = Number(v); return [`${n > 0 ? '+' : ''}${n}%`, 'G/L']; }}
              contentStyle={{ background: '#111118', border: '1px solid #1E1E2E', borderRadius: 8, fontSize: 12 }}
              labelStyle={{ color: '#FFFFFF' }}
              itemStyle={{ color: '#8B8FA8' }}
            />
            <ReferenceLine y={0} stroke="#2A2A3E" strokeWidth={1} />
            <Bar dataKey="pct" radius={[4, 4, 0, 0]}>
              {barData.map((d, i) => (
                <Cell key={i} fill={d.pct >= 0 ? '#00D084' : '#FF4757'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
