import { ArrowClockwise, Warning } from "@phosphor-icons/react";
import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("ErrorBoundary caught:", error, errorInfo);
  }

  handleReload = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-bg-primary flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-bg-secondary border border-border rounded-[var(--radius-xl)] p-10 text-center shadow-[var(--shadow-lg)]">
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-accent-danger/10 mb-4">
              <Warning size={28} weight="bold" className="text-accent-danger" />
            </div>
            <h1 className="text-xl font-semibold tracking-tight text-text-primary mb-2">
              Something went wrong
            </h1>
            <p className="text-sm text-text-muted mb-6">
              An unexpected error occurred. Please try reloading the page.
            </p>
            {this.state.error && (
              <pre className="text-xs text-text-muted bg-bg-tertiary rounded p-3 mb-6 overflow-auto max-h-32 text-left">
                {this.state.error.message}
              </pre>
            )}
            <button
              onClick={this.handleReload}
              className="inline-flex items-center gap-2 px-4 py-2 bg-accent-primary text-white rounded-[var(--radius-md)] text-sm font-medium hover:bg-accent-primary/85 transition-[background-color,transform] duration-[var(--transition-fast)] active:translate-y-[1px]"
            >
              <ArrowClockwise size={14} weight="bold" />
              Reload Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
