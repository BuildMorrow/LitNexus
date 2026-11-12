import { useState, useEffect } from 'react'
import { Filter, GitCompare, Search, Sparkles, CheckCircle2, AlertTriangle } from 'lucide-react'
import { apiRequest } from './services/api'

export default function App() {
  const [apiStatus, setApiStatus] = useState('checking')
  const [activeStage, setActiveStage] = useState('funnel')

  useEffect(() => {
    apiRequest('/health')
      .then(() => setApiStatus('online'))
      .catch(() => setApiStatus('offline'))
  }, [])

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-600 font-bold">
              LN
            </div>
            <div>
              <h1 className="text-lg font-semibold tracking-tight">LitNexus</h1>
              <p className="text-xs text-slate-400">
                Active-Learning SLR &amp; Cross-Paper Conflict Discovery
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 rounded-full border border-slate-800 bg-slate-900 px-3 py-1 text-xs">
            <span
              className={`h-2 w-2 rounded-full ${
                apiStatus === 'online'
                  ? 'bg-emerald-400'
                  : apiStatus === 'offline'
                  ? 'bg-rose-400'
                  : 'bg-amber-400'
              }`}
            />
            <span className="text-slate-300">API: {apiStatus}</span>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-8">
        <div className="mb-8 grid gap-4 md:grid-cols-2">
          <button
            onClick={() => setActiveStage('funnel')}
            className={`rounded-xl border p-5 text-left transition ${
              activeStage === 'funnel'
                ? 'border-indigo-500 bg-indigo-950/30'
                : 'border-slate-800 bg-slate-900/40 hover:border-slate-700'
            }`}
          >
            <div className="mb-2 flex items-center gap-2 text-indigo-400">
              <Filter className="h-5 w-5" />
              <span className="text-xs font-semibold uppercase tracking-wider">
                Stage 1 · Phễu lọc siêu tốc
              </span>
            </div>
            <h2 className="text-base font-semibold">Active Learning Hybrid Screener</h2>
            <p className="mt-1 text-sm text-slate-400">
              Thu thập hàng nghìn bài báo từ OpenAlex và dùng Uncertainty Sampling để cắt giảm 90%
              chi phí LLM token.
            </p>
          </button>

          <button
            onClick={() => setActiveStage('conflict')}
            className={`rounded-xl border p-5 text-left transition ${
              activeStage === 'conflict'
                ? 'border-rose-500 bg-rose-950/30'
                : 'border-slate-800 bg-slate-900/40 hover:border-slate-700'
            }`}
          >
            <div className="mb-2 flex items-center gap-2 text-rose-400">
              <GitCompare className="h-5 w-5" />
              <span className="text-xs font-semibold uppercase tracking-wider">
                Stage 2 · Đấu trường tranh biện
              </span>
            </div>
            <h2 className="text-base font-semibold">Cross-Paper Conflict &amp; Gap Engine</h2>
            <p className="mt-1 text-sm text-slate-400">
              Multi-Agent bóc tách luận điểm, đối chiếu mâu thuẫn thực nghiệm và đề xuất Research Gap
              mới.
            </p>
          </button>
        </div>

        <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
          {activeStage === 'funnel' ? (
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-slate-200">
                <Search className="h-5 w-5 text-indigo-400" />
                <h3 className="text-lg font-medium">Active Learning Screening Pipeline</h3>
              </div>
              <p className="text-sm text-slate-400">
                Khởi chạy Backend FastAPI tại <code className="text-indigo-300">localhost:8000</code>{' '}
                và đăng nhập để bắt đầu truy vấn OpenAlex và chạy vòng lặp Active Learning.
              </p>
              <div className="grid gap-3 pt-2 sm:grid-cols-3">
                <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-4">
                  <div className="text-xs text-slate-400">1. Cold Start</div>
                  <div className="mt-1 text-sm font-medium">Chấm 15-20 bài mẫu</div>
                </div>
                <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-4">
                  <div className="text-xs text-slate-400">2. Local ML Scoring</div>
                  <div className="mt-1 text-sm font-medium">TF-IDF + Logistic Regression</div>
                </div>
                <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-4">
                  <div className="text-xs text-slate-400">3. Selective LLM</div>
                  <div className="mt-1 text-sm font-medium">Chỉ hỏi LLM các bài phân vân</div>
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-slate-200">
                <Sparkles className="h-5 w-5 text-rose-400" />
                <h3 className="text-lg font-medium">Multi-Agent Conflict &amp; Gap Discovery</h3>
              </div>
              <div className="grid gap-3 pt-2 sm:grid-cols-2">
                <div className="flex items-start gap-3 rounded-lg border border-slate-800 bg-slate-950/60 p-4">
                  <AlertTriangle className="mt-0.5 h-5 w-5 text-rose-400" />
                  <div>
                    <div className="text-sm font-medium">Contradiction &amp; Assumption Mismatch</div>
                    <p className="mt-1 text-xs text-slate-400">
                      Phát hiện khi 2 bài báo cho kết quả trái ngược do khác biệt tập dữ liệu hoặc
                      giả định thực nghiệm.
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3 rounded-lg border border-slate-800 bg-slate-950/60 p-4">
                  <CheckCircle2 className="mt-0.5 h-5 w-5 text-emerald-400" />
                  <div>
                    <div className="text-sm font-medium">Actionable Research Gaps</div>
                    <p className="mt-1 text-xs text-slate-400">
                      Tự động tổng hợp xung đột thành đề xuất hướng nghiên cứu mới có điểm novelty.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </section>
      </main>
    </div>
  )
}
