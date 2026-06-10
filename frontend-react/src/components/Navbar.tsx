interface NavbarProps {
  connected: boolean;
  onSignOut?: () => void;
}

export function Navbar({ connected, onSignOut }: NavbarProps) {
  return (
    <nav className="flex items-center justify-between px-6 h-14 bg-card border-b border-surface shrink-0 z-10">
      <div className="flex items-center gap-2">
        <span className="text-lg font-black text-green tracking-tight">STK</span>
        <span className="text-sm text-muted font-normal">Portfolio Assistant</span>
      </div>
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-xs text-muted">
          <span
            className={`w-2 h-2 rounded-full ${connected ? 'bg-green shadow-[0_0_6px_rgba(0,208,132,0.6)]' : 'bg-red'}`}
          />
          <span>{connected ? 'Connected' : 'Disconnected'}</span>
        </div>
        {onSignOut && (
          <button
            onClick={onSignOut}
            className="text-xs text-muted hover:text-text transition-colors px-2 py-1 rounded hover:bg-surface"
          >
            Sign out
          </button>
        )}
      </div>
    </nav>
  );
}
