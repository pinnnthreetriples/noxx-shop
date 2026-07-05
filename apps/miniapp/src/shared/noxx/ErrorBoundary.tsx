import * as React from 'react'

type Props = { children: React.ReactNode }
type State = { error: Error | null }

export default class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { error: null }
  }
  static getDerivedStateFromError(error: Error): State {
    return { error }
  }
  componentDidCatch(error: Error, info: React.ErrorInfo) {
    // eslint-disable-next-line no-console
    console.error('NoxX render error:', error, info)
  }
  render() {
    if (this.state.error) {
      return (
        <div style={{ padding: 20, color: '#ff6b9d', font: '13px/1.5 monospace', whiteSpace: 'pre-wrap', overflow: 'auto', height: '100%' }}>
          <div style={{ fontWeight: 700, marginBottom: 8 }}>Screen render error</div>
          <div>{String(this.state.error && this.state.error.message)}</div>
          <div style={{ marginTop: 10, fontSize: 11, opacity: 0.7 }}>{String(this.state.error && this.state.error.stack).slice(0, 800)}</div>
        </div>
      )
    }
    return this.props.children
  }
}
