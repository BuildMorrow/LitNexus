export default function Header({ apiStatus, token, isDemoMode, onLogout }) {
  return (
    <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3.5">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-indigo-700 font-bold shadow-md shadow-indigo-500/20">
            LN
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-semibold tracking-tight text-white">LitNexus</h1>
              <span className="rounded bg-indigo-500/20 px-2 py-0.5 text-[10px] font-medium text-indigo-300 border border-indigo-500/30">
                SLR &amp; Conflict Engine
              </span>
              {isDemoMode && (
                <span className="rounded bg-amber-500/20 px-2 py-0.5 text-[10px] font-semibold text-amber-300 border border-amber-500/40">
                  Prototype Demo Mode
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400">
              Active Learning Systematic Review &bull; Zero-Hallucination Evidence Grounding
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 rounded-full border border-slate-800 bg-slate-900 px-3 py-1 text-xs">
            <span
              className={`h-2 w-2 rounded-full ${
                apiStatus === 'online' ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'
              }`}
            />
            <span className="text-slate-300">Backend: {apiStatus}</span>
          </div>

          {token && (
            <button
              onClick={onLogout}
              className="text-xs text-slate-400 hover:text-slate-200 transition underline underline-offset-4"
            >
              Đăng xuất
            </button>
          )}
        </div>
      </div>
    </header>
  )
}
