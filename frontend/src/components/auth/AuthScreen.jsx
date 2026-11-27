import { ShieldCheck, Sparkles } from 'lucide-react'

export default function AuthScreen({
  isRegister,
  setIsRegister,
  authName,
  setAuthName,
  authEmail,
  setAuthEmail,
  authPassword,
  setAuthPassword,
  authError,
  onSubmit,
  onEnterDemo,
}) {
  return (
    <div className="mx-auto max-w-md px-6 py-20">
      <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-8 shadow-2xl backdrop-blur">
        <div className="mb-6 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 mb-3">
            <ShieldCheck className="h-6 w-6" />
          </div>
          <h2 className="text-xl font-bold text-white">
            {isRegister ? 'Tạo Tài khoản Nghiên cứu' : 'Đăng nhập LitNexus'}
          </h2>
          <p className="mt-1 text-xs text-slate-400">
            Bảo vệ đa người dùng và cô lập dữ liệu nghiên cứu theo chuẩn an toàn
          </p>
        </div>

        {authError && (
          <div className="mb-4 rounded-lg border border-rose-500/40 bg-rose-950/40 p-3 text-xs text-rose-300">
            {authError}
          </div>
        )}

        <form onSubmit={onSubmit} className="space-y-4">
          {isRegister && (
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Họ và tên</label>
              <input
                type="text"
                required
                value={authName}
                onChange={(e) => setAuthName(e.target.value)}
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
                placeholder="TS. Nguyễn Văn A"
              />
            </div>
          )}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Email Học thuật</label>
            <input
              type="email"
              required
              value={authEmail}
              onChange={(e) => setAuthEmail(e.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
              placeholder="researcher@university.edu"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Mật khẩu</label>
            <input
              type="password"
              required
              value={authPassword}
              onChange={(e) => setAuthPassword(e.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            className="w-full rounded-lg bg-indigo-600 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-600/30 hover:bg-indigo-500 transition"
          >
            {isRegister ? 'Đăng ký Tài khoản' : 'Đăng nhập vào Hệ thống'}
          </button>
        </form>

        <div className="mt-4 pt-4 border-t border-slate-800">
          <button
            type="button"
            onClick={onEnterDemo}
            className="w-full flex items-center justify-center gap-2 rounded-lg border border-indigo-500/40 bg-indigo-950/40 py-2 text-xs font-semibold text-indigo-300 hover:bg-indigo-900/40 transition"
          >
            <Sparkles className="h-4 w-4 text-indigo-400" />
            Vào xem Prototype &bull; Trải nghiệm Dữ liệu Mẫu (Demo Mode)
          </button>
          <p className="mt-1.5 text-center text-[11px] text-slate-500">
            Xem ngay giao diện Active Screening, Ma trận Bằng chứng và KPI mà không cần nạp DB
          </p>
        </div>

        <div className="mt-6 text-center text-xs text-slate-400">
          {isRegister ? 'Đã có tài khoản?' : 'Chưa có tài khoản nghiên cứu?'}{' '}
          <button
            onClick={() => setIsRegister(!isRegister)}
            className="font-medium text-indigo-400 hover:text-indigo-300 underline"
          >
            {isRegister ? 'Đăng nhập' : 'Tạo mới ngay'}
          </button>
        </div>
      </div>
    </div>
  )
}
