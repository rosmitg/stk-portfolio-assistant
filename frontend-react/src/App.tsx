import { useCallback, useEffect, useState } from 'react';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { ChatPanel } from './components/ChatPanel';
import { Onboarding } from './components/Onboarding';
import { Auth } from './components/Auth';
import { useAuth } from './hooks/useAuth';
import { getPortfolio } from './api/client';
import type { Holding } from './types';
import './index.css';

export default function App() {
  const { user, loading: authLoading, signOut } = useAuth();
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [portfolioLoading, setPortfolioLoading] = useState(false);
  const [connected, setConnected] = useState(true);

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

  if (portfolioLoading) {
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
          <ChatPanel holdings={holdings} />
        </div>
      )}
    </div>
  );
}
