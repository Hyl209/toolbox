import { Component, type ReactNode } from "react";

type State = { error: Error | null };

export class ToolErrorBoundary extends Component<{ children: ReactNode }, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  render() {
    const { error } = this.state;
    if (error) {
      return (
        <div className="tool-panel-error">
          <p className="eyebrow">工具崩溃</p>
          <h2>出了点问题</h2>
          <div className="error-box">{error.message}</div>
          <button
            className="ghost-button"
            onClick={() => this.setState({ error: null })}
            type="button"
          >
            重试
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
