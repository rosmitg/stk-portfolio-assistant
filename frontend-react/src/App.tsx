import { useCallback, useEffect, useRef, useState } from 'react';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { ChatPanel } from './components/ChatPanel';
import { BriefPanel } from './components/BriefPanel';
import { Onboarding } from './components/Onboarding';
import { Auth } from './components/Auth';
import { useAuth } from './hooks/useAuth';
import { getPortfolio, getTodayBrief } from './api/client';
import type { Holding, Brief } from './types';
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
  // Today's brief, cached at the App level so switching tabs never re-fetches.
  const [brief, setBrief] = useState<Brief | null>(null);
  const briefFetchedRef = useRef(false);

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
    if (user) {
      fetchPortfolio();
    } else {
      setHoldings([]);
      // Reset cached brief state on sign-out so the next user fetches fresh.
      setBrief(null);
      setBriefReady(false);
      briefFetchedRef.current = false;
    }
  }, [user, fetchPortfolio]);

  // Fetch today's brief once, cache it, and pick the default tab from the result:
  // Brief if one exists today, else Chat. Switching tabs reuses the cached value.
  useEffect(() => {
    if (!user || holdings.length === 0) {
      if (holdings.length === 0) setBriefReady(true);
      return;
    }
    if (briefFetchedRef.current) return;
    briefFetchedRef.current = true;
    let cancelled = false;
    (async () => {
      try {
        const { data } = await getTodayBrief();
        if (!cancelled) { setBrief(data); setTab('brief'); }
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

            {/* Both panels stay mounted; we toggle visibility so switching tabs
                never unmounts/remounts (and never re-fetches or re-renders from
                scratch). State — brief, chat history, scroll — is preserved. */}
            <div className={`flex-1 flex flex-col overflow-hidden ${tab === 'brief' ? '' : 'hidden'}`}>
              <BriefPanel
                brief={brief}
                onBriefChange={setBrief}
                onChatAboutSection={openChatWith}
              />
            </div>
            <div className={`flex-1 flex flex-col overflow-hidden ${tab === 'chat' ? '' : 'hidden'}`}>
              <ChatPanel
                holdings={holdings}
                initialMessage={initialChatMessage}
                onInitialConsumed={() => setInitialChatMessage(undefined)}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
