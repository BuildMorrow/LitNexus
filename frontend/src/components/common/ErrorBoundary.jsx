import React from 'react'
import { AlertTriangle } from 'lucide-react'

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    console.error('UI ErrorBoundary caught:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-6">
          <div className="max-w-md w-full rounded-2xl border border-rose-500/40 bg-slate-900 p-6 space-y-4">
            <div className="flex items-center gap-2 text-rose-400 font-semibold">
              <AlertTriangle className="h-5 w-5" />
              <span>Đã xảy ra lỗi hiển thị giao diện</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              {this.state.error?.message || 'Lỗi không xác định trong thành phần React.'}
            </p>
            <button
              onClick={() => window.location.reload()}
              className="w-full rounded-lg bg-indigo-600 py-2 text-xs font-semibold text-white hover:bg-indigo-500 transition"
            >
              Tải lại trang
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
