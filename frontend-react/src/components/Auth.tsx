import { useState } from 'react';
import { useAuth } from '../hooks/useAuth';

export function Auth() {
  const { signIn, signUp } = useAuth();
  const [mode, setMode] = useState<'login' | 'signup'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setMessage('');
    setLoading(true);
    try {
      if (mode === 'login') {
        const { error } = await signIn(email, password);
        if (error) setError(error.message);
      } else {
        const { error } = await signUp(email, password);
        if (error) {
          setError(error.message);
        } else {
          setMessage('Account created! Check your email to confirm, then sign in.');
        }
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-screen flex items-center justify-center bg-dark">
      <div className="w-full max-w-sm mx-4">
        <div className="text-center mb-8">
          <div className="text-3xl font-black text-green tracking-tight mb-1">STK</div>
          <div className="text-sm text-muted">Portfolio Assistant</div>
        </div>

        <div className="bg-card border border-surface rounded-xl p-6">
          <div className="flex mb-6 bg-surface rounded-lg p-1">
            <button
              type="button"
              onClick={() => { setMode('login'); setError(''); setMessage(''); }}
              className={`flex-1 py-1.5 text-sm font-medium rounded-md transition-colors ${
                mode === 'login' ? 'bg-surface2 text-text' : 'text-muted hover:text-text'
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => { setMode('signup'); setError(''); setMessage(''); }}
              className={`flex-1 py-1.5 text-sm font-medium rounded-md transition-colors ${
                mode === 'signup' ? 'bg-surface2 text-text' : 'text-muted hover:text-text'
              }`}
            >
              Sign Up
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs text-muted mb-1.5">Email</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
                placeholder="you@example.com"
                className="w-full bg-surface border border-surface2 rounded-lg px-3 py-2.5 text-sm text-text placeholder-muted2 focus:outline-none focus:border-green transition-colors"
              />
            </div>
            <div>
              <label className="block text-xs text-muted mb-1.5">Password</label>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                placeholder="••••••••"
                minLength={6}
                className="w-full bg-surface border border-surface2 rounded-lg px-3 py-2.5 text-sm text-text placeholder-muted2 focus:outline-none focus:border-green transition-colors"
              />
            </div>

            {error && (
              <div className="text-xs text-red bg-red/10 border border-red/20 rounded-lg px-3 py-2">
                {error}
              </div>
            )}
            {message && (
              <div className="text-xs text-green bg-green/10 border border-green/20 rounded-lg px-3 py-2">
                {message}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-green text-dark font-semibold py-2.5 rounded-lg text-sm hover:bg-green-light transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Loading…' : mode === 'login' ? 'Sign In' : 'Create Account'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
