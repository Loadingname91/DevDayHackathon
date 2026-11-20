import { Component, type ReactNode } from 'react';

/** Catches a render crash so the page is never blank: says so, shows the error text (for a screenshot) and offers Reload. */
export class CrashScreen extends Component<{ children: ReactNode }, { error: Error | null }> {
  state = { error: null as Error | null };
  static getDerivedStateFromError(error: Error) { return { error }; }
  componentDidCatch(error: Error) { console.error('Quilt crashed while drawing a screen:', error); }
  render() {
    const { error } = this.state;
    if (!error) return this.props.children;
    return (
      <div className="center" role="alert" style={{ minHeight: '100dvh', alignContent: 'center', gap: 12, padding: 24 }}>
        <h1>Something broke on this screen.</h1>
        <p className="muted">Your changes are saved. Reload to carry on.</p>
        <p className="muted small" style={{ wordBreak: 'break-word' }}>{error.message}</p>
        <button className="cta" onClick={() => { location.href = '/'; }}>Reload</button>
      </div>
    );
  }
}
