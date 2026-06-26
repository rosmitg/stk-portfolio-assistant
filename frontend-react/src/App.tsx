import { useCallback, useEffect, useState } from 'react';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { ChatPanel } from './components/ChatPanel';
import { BriefPanel } from './components/BriefPanel';
import { Onboarding } from './components/Onboarding';
import { Auth } from './components/Auth';
import { useAuth } from './hooks/useAuth';
import { getPortfolio, getTodayBrief } from './api/client';
import type { Holding } from './types';
import './index.css';

type Tab = 'brief' | 'chat';

export default function App() {
  const { user, loading: authLoading, signOut } = useAuth();
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [portfolioLoading, setPortfolioLoading] = useState(false);
  const [connected, setConnected] = useState(true);
  const [tab, setTab] = useState<Tab>('chat');
  const [briefReady, setBriefReady] = useState(false);
  const [initialChatMessage, setInitialChatMessage] = useState<string | undefined>();

  const fetchPortfolio = useCallback(async () => {
    setPortfolioLoading(true);
    try {
      const { data } = await getPortfolio();
      setHoldings(data);
      setConnected(true);
    } catch {
      setConnected(false);
    } finally {
      setPortfolioLoading(false);
    }
  }, []);

  useEffect(() => {
    if (user) fetchPortfolio();
    else setHoldings([]);
  }, [user, fetchPortfolio]);

  // Pick the default tab once holdings are known: Brief if one exists today, else Chat.
  useEffect(() => {
    if (!user) return;
    if (holdings.length === 0) { setBriefReady(true); return; }
    let cancelled = false;
    (async () => {
      try {
        await getTodayBrief();
        if (!cancelled) setTab('brief');
      } catch {
        if (!cancelled) setTab('chat');
      } finally {
        if (!cancelled) setBriefReady(true);
      }
    })();
    return () => { cancelled = true; };
  }, [user, holdings.length]);

  const openChatWith = (message: string) => {
    setInitialChatMessage(message);
    setTab('chat');
  };

  if (authLoading) {
    return (
      <div className="h-screen flex items-center justify-center bg-dark">
        <div className="text-center">
          <div className="text-2xl font-bold text-green mb-2">STK</div>
          <div className="text-sm text-muted">Loading…</div>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Auth />;
  }

  if (portfolioLoading || (holdings.length > 0 && !briefReady)) {
    return (
      <div className="h-screen flex items-center justify-center bg-dark">
        <div className="text-center">
          <div className="text-2xl font-bold text-green mb-2">STK</div>
          <div className="text-sm text-muted">Loading portfolio…</div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-dark text-text overflow-hidden">
      <Navbar connected={connected} onSignOut={signOut} />
      {holdings.length === 0 ? (
        <Onboarding onComplete={fetchPortfolio} />
      ) : (
        <div className="flex flex-1 overflow-hidden">
          <Sidebar holdings={holdings} onUpdate={fetchPortfolio} />
          <div className="flex-1 flex flex-col overflow-hidden">
            {/* Tab switcher: Brief / Chat */}
            <div className="flex items-center gap-1 px-4 h-11 border-b border-surface bg-card shrink-0">
              {(['brief', 'chat'] as Tab[]).map((t) => (
                <button
                  key={t}
                  onClick={() => {
                    if (t === 'chat') setInitialChatMessage(undefined);
                    setTab(t);
                  }}
                  className={`px-3 py-1.5 text-sm font-semibold rounded-lg transition-colors ${
                    tab === t ? 'text-green bg-green/8' : 'text-muted hover:text-text'
                  }`}
                >
                  {t === 'brief' ? 'Brief' : 'Chat'}
                </button>
              ))}
            </div>

            {tab === 'brief' ? (
              <BriefPanel onChatAboutSection={openChatWith} />
            ) : (
              <ChatPanel
                holdings={holdings}
                initialMessage={initialChatMessage}
                onInitialConsumed={() => setInitialChatMessage(undefined)}
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
