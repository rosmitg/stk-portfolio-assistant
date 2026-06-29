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

const BRIEF_CACHE_KEY = 'stk_today_brief';

/** Local YYYY-MM-DD — scopes the cached brief to "today". */
function localDateStr(d: Date = new Date()): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(
    d.getDate(),
  ).padStart(2, '0')}`;
}

/** Read the cached brief, but only if it was stored today; clear it otherwise. */
function readCachedBrief(): Brief | null {
  try {
    const raw = localStorage.getItem(BRIEF_CACHE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as { date: string; brief: Brief };
    if (parsed.date !== localDateStr()) {
      localStorage.removeItem(BRIEF_CACHE_KEY); // stale — past midnight
      return null;
    }
    return parsed.brief ?? null;
  } catch {
    return null;
  }
}

function writeCachedBrief(brief: Brief): void {
  try {
    localStorage.setItem(BRIEF_CACHE_KEY, JSON.stringify({ date: localDateStr(), brief }));
  } catch {
    /* storage full/unavailable — non-fatal */
  }
}

function clearCachedBrief(): void {
  try {
    localStorage.removeItem(BRIEF_CACHE_KEY);
  } catch {
    /* ignore */
  }
}

/** Milliseconds until just after the next local midnight. */
function msUntilMidnight(): number {
  const now = new Date();
  const next = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1, 0, 0, 5);
  return next.getTime() - now.getTime();
}

export default function App() {
  const { user, loading: authLoading, signOut } = useAuth();
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [portfolioLoading, setPortfolioLoading] = useState(false);
  const [connected, setConnected] = useState(true);
  const [initialChatMessage, setInitialChatMessage] = useState<string | undefined>();

  // Read the localStorage-cached brief exactly once on mount (valid only if it
  // was stored today). Showing it immediately avoids a loading flash; we then
  // re-fetch in the background and update if it changed.
  const cachedReadRef = useRef(false);
  const cachedOnMountRef = useRef<Brief | null>(null);
  if (!cachedReadRef.current) {
    cachedReadRef.current = true;
    cachedOnMountRef.current = readCachedBrief();
  }
  const cachedOnMount = cachedOnMountRef.current;

  // Today's brief, cached at the App level so switching tabs never re-fetches.
  const [brief, setBrief] = useState<Brief | null>(cachedOnMount);
  const [briefReady, setBriefReady] = useState<boolean>(cachedOnMount !== null);
  const [tab, setTab] = useState<Tab>(cachedOnMount ? 'brief' : 'chat');
  const [briefRefreshKey, setBriefRefreshKey] = useState(0);
  const briefFetchedRef = useRef(false);

  // Persist a brief (e.g. freshly generated in BriefPanel) to state + cache.
  const handleBriefChange = useCallback((b: Brief) => {
    setBrief(b);
    writeCachedBrief(b);
  }, []);

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
      clearCachedBrief();
    }
  }, [user, fetchPortfolio]);

  // Re-fetch today's brief in the background and update if it changed. A cached
  // brief (read on mount) is already shown, so this never blocks the UI; when
  // there's no cache, this also picks the default tab (Brief if one exists today,
  // else Chat). Re-runs after midnight via briefRefreshKey.
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
        if (cancelled) return;
        // Update only if the brief actually changed ("if newer").
        setBrief((prev) =>
          prev && JSON.stringify(prev) === JSON.stringify(data) ? prev : data,
        );
        writeCachedBrief(data);
        // Only auto-switch to Brief when we didn't already show a cached brief —
        // a background refresh shouldn't yank the user's current tab.
        if (!cachedOnMount) setTab('brief');
      } catch {
        if (cancelled) return;
        // No brief today (404) or network error. Keep a same-day cached brief if
        // we have one; otherwise default to Chat.
        if (!cachedOnMount) setTab('chat');
      } finally {
        if (!cancelled) setBriefReady(true);
      }
    })();
    return () => { cancelled = true; };
  }, [user, holdings.length, cachedOnMount, briefRefreshKey]);

  // Clear the cached brief at local midnight and re-fetch for the new day, so a
  // long-open session never keeps showing yesterday's brief.
  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;
    const schedule = () => {
      timer = setTimeout(() => {
        clearCachedBrief();
        setBrief(null);
        briefFetchedRef.current = false;
        setBriefRefreshKey((k) => k + 1);
        schedule(); // arm the following midnight
      }, msUntilMidnight());
    };
    schedule();
    return () => clearTimeout(timer);
  }, []);

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
                onBriefChange={handleBriefChange}
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
