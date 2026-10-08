import { Component } from 'react';

export class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidUpdate(previousProps) {
    if (this.state.error && previousProps.resetKey !== this.props.resetKey) {
      this.setState({ error: null });
    }
  }

  componentDidCatch(error, errorInfo) {
    console.error('AI Hub page error', error, errorInfo.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <main className="error-page" role="alert">
          <h1>Something went wrong</h1>
          <p>This page could not be displayed. Try loading it again.</p>
          <button type="button" onClick={() => this.setState({ error: null })}>
            Try again
          </button>
        </main>
      );
    }
    return this.props.children;
  }
}
