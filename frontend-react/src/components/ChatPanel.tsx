import { useEffect, useRef, useState } from 'react';
import { Send, Trash2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { streamChat } from '../api/client';
import type { ChatHolding } from '../api/client';
import type { ChatMessage, Holding } from '../types';

const SUGGESTIONS = [
  { label: 'Analyse my risk',     prompt: 'Analyse my risk exposure and portfolio diversification' },
  { label: 'Best performer?',     prompt: 'What is my best performing holding and why?' },
  { label: 'Latest news',         prompt: 'What is the latest news on my holdings?' },
  { label: 'Should I rebalance?', prompt: 'Should I rebalance my portfolio? What changes would you suggest?' },
];

function buildContext(holdings: Holding[]): ChatHolding[] {
  return holdings.map(({ ticker, shares, avg_cost }) => ({
    ticker,
    quantity: shares,
    avg_buy_price: avg_cost,
  }));
}

function buildWelcome(holdings: Holding[]): ChatMessage {
  const preview = holdings
    .slice(0, 4)
    .map((h) => `${h.ticker} (${h.shares % 1 === 0 ? h.shares : h.shares.toFixed(2)} sh)`)
    .join(', ');
  const extra = holdings.length > 4 ? ` +${holdings.length - 4} more` : '';
  return {
    role: 'assistant',
    content: `Portfolio loaded: ${preview}${extra}.\n\nAsk me anything about your holdings — performance, risk, news, or strategy.`,
    sources: [],
  };
}

function MarkdownText({ text }: { text: string }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        p:      ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
        h1:     ({ children }) => <p className="font-bold text-text text-sm mt-3 mb-1 first:mt-0">{children}</p>,
        h2:     ({ children }) => <p className="font-bold text-text text-sm mt-3 mb-1 first:mt-0">{children}</p>,
        h3:     ({ children }) => <p className="font-bold text-text text-sm mt-2 mb-1 first:mt-0">{children}</p>,
        ul:     ({ children }) => <ul className="list-disc pl-4 my-1 space-y-0.5">{children}</ul>,
        ol:     ({ children }) => <ol className="list-decimal pl-4 my-1 space-y-0.5">{children}</ol>,
        li:     ({ children }) => <li className="text-[#E0E6F0]">{children}</li>,
        strong: ({ children }) => <strong className="font-bold text-text">{children}</strong>,
        em:     ({ children }) => <em className="italic text-[#C0C7D6]">{children}</em>,
        code:   ({ children, className }) =>
          className
            ? <code className="block bg-surface rounded-lg px-3 py-2 my-1.5 font-mono text-[12px] text-[#E0E6F0] overflow-x-auto">{children}</code>
            : <code className="bg-surface text-green text-[12px] px-1.5 py-0.5 rounded font-mono">{children}</code>,
        blockquote: ({ children }) => (
          <blockquote className="border-l-2 border-green pl-3 my-1.5 text-muted italic">{children}</blockquote>
        ),
        table: ({ children }) => (
          <div className="overflow-x-auto my-2">
            <table className="w-full text-[12px] border-collapse">{children}</table>
          </div>
        ),
        thead: ({ children }) => <thead style={{ background: '#1a1a2e' }}>{children}</thead>,
        th: ({ children }) => (
          <th className="text-left font-semibold text-white px-3 py-2" style={{ border: '1px solid #1E1E2E' }}>
            {children}
          </th>
        ),
        td: ({ children }) => (
          <td className="text-[#8B8FA8] px-3 py-1.5" style={{ border: '1px solid #1E1E2E' }}>
            {children}
          </td>
        ),
        tr: ({ children, ...props }) => (
          <tr
            {...props}
            style={{
              background: (props as React.HTMLAttributes<HTMLTableRowElement> & { 'data-odd'?: boolean })?.['data-odd']
                ? 'rgba(255,255,255,0.02)'
                : 'transparent',
            }}
          >
            {children}
          </tr>
        ),
        a: ({ href, children }) => (
          <a href={href} className="text-green hover:underline" target="_blank" rel="noreferrer">{children}</a>
        ),
      }}
    >
      {text}
    </ReactMarkdown>
  );
}

interface ChatPanelProps {
  holdings: Holding[];
}

export function ChatPanel({ holdings }: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>(() => [buildWelcome(holdings)]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const send = async (text: string) => {
    if (!text.trim() || loading) return;
    const context = buildContext(holdings);
    setMessages((prev) => [
      ...prev,
      { role: 'user', content: text.trim() },
      { role: 'assistant', content: '', sources: [] },
    ]);
    setInput('');
    setLoading(true);

    await streamChat(
      text.trim(),
      context,
      (token) => {
        setMessages((prev) => {
          const next = [...prev];
          const last = next[next.length - 1];
          next[next.length - 1] = { ...last, content: last.content + token };
          return next;
        });
      },
      (sources) => {
        setMessages((prev) => {
          const next = [...prev];
          next[next.length - 1] = { ...next[next.length - 1], sources };
          return next;
        });
      },
      (errorMsg) => {
        setMessages((prev) => {
          const next = [...prev];
          next[next.length - 1] = { ...next[next.length - 1], content: `⚠ ${errorMsg}` };
          return next;
        });
      },
    );

    setLoading(false);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    send(input);
  };

  const handleClear = () => {
    setMessages([buildWelcome(holdings)]);
  };

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-dark">
      {/* ── Message history ── */}
      <div className="flex-1 overflow-y-auto px-6 py-5 space-y-4">
        {messages.map((msg, i) => (
          msg.role === 'user' ? (
            <div key={i} className="flex justify-end">
              <div className="bg-green text-dark font-medium text-[13px] leading-relaxed px-4 py-2.5 rounded-[18px_18px_4px_18px] max-w-[72%] break-words">
                {msg.content}
              </div>
            </div>
          ) : (
            <div key={i} className="flex justify-start gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-surface border border-surface2 flex items-center justify-center text-[11px] font-black text-green shrink-0 mt-0.5">
                STK
              </div>
              <div
                className="border border-surface text-text text-[13px] leading-relaxed px-4 py-2.5 rounded-[4px_18px_18px_18px] max-w-[74%] break-words select-none"
                style={{ background: '#111118' }}
              >
                <MarkdownText text={msg.content} />
                {msg.sources && msg.sources.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {msg.sources.map((s, j) => (
                      <span key={j} className="bg-green/8 border border-green/25 text-green text-[11px] font-medium px-2 py-0.5 rounded-full">
                        {s}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )
        ))}

        {/* Thinking indicator */}
        {loading && (
          <div className="flex justify-start gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-surface border border-surface2 flex items-center justify-center text-[11px] font-black text-green shrink-0 mt-0.5">
              STK
            </div>
            <div className="bg-card border border-surface px-4 py-3 rounded-[4px_18px_18px_18px]">
              <div className="flex gap-1 items-center">
                {[0, 1, 2].map((d) => (
                  <span
                    key={d}
                    className="w-1.5 h-1.5 rounded-full bg-muted animate-bounce"
                    style={{ animationDelay: `${d * 150}ms` }}
                  />
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Suggested prompts — only shown before any user message */}
        {messages.length === 1 && !loading && (
          <div className="pt-2">
            <p className="text-[11px] font-semibold text-muted uppercase tracking-widest mb-2">Try asking:</p>
            <div className="grid grid-cols-2 gap-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s.label}
                  onClick={() => send(s.prompt)}
                  className="text-left text-xs text-muted border border-surface rounded-xl px-3 py-2.5 hover:border-green hover:text-green hover:bg-green/4 transition-all"
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* ── Input bar ── */}
      <div className="border-t border-surface px-6 py-4">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            className="flex-1 bg-card border border-surface rounded-xl px-4 py-2.5 text-sm text-text placeholder-muted focus:outline-none focus:border-green transition-colors"
            placeholder="Ask about your portfolio…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="bg-green text-dark font-bold px-4 py-2.5 rounded-xl hover:bg-green-light disabled:opacity-40 transition-colors flex items-center gap-1.5"
          >
            <Send size={14} />
            <span className="text-sm">Send</span>
          </button>
          {messages.length > 1 && (
            <button
              type="button"
              onClick={handleClear}
              className="border border-surface text-muted px-3 py-2.5 rounded-xl hover:border-muted hover:text-text transition-colors"
              title="Clear chat"
            >
              <Trash2 size={14} />
            </button>
          )}
        </form>
      </div>
    </div>
  );
}
