import { CheckCircle2, Clock, Filter, HelpCircle, XCircle, Zap } from 'lucide-react'

export default function KpiDashboard({ kpiMetrics }) {
  if (!kpiMetrics) return null

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-6">
      <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-3.5">
        <div className="flex items-center justify-between text-slate-400 text-xs">
          <span>Tổng bài nạp</span>
          <Filter className="h-4 w-4 text-slate-500" />
        </div>
        <div className="mt-1 text-2xl font-bold text-white">{kpiMetrics.total_papers}</div>
        <div className="text-[11px] text-slate-500 mt-0.5">Trong cơ sở dữ liệu</div>
      </div>

      <div className="rounded-xl border border-emerald-900/40 bg-emerald-950/20 p-3.5">
        <div className="flex items-center justify-between text-emerald-400 text-xs">
          <span>Included</span>
          <CheckCircle2 className="h-4 w-4 text-emerald-400" />
        </div>
        <div className="mt-1 text-2xl font-bold text-emerald-300">{kpiMetrics.included_count}</div>
        <div className="text-[11px] text-emerald-500/80 mt-0.5">Bài nghiên cứu cốt lõi</div>
      </div>

      <div className="rounded-xl border border-rose-900/40 bg-rose-950/20 p-3.5">
        <div className="flex items-center justify-between text-rose-400 text-xs">
          <span>Excluded</span>
          <XCircle className="h-4 w-4 text-rose-400" />
        </div>
        <div className="mt-1 text-2xl font-bold text-rose-300">{kpiMetrics.excluded_count}</div>
        <div className="text-[11px] text-rose-500/80 mt-0.5">Đã loại trừ</div>
      </div>

      <div className="rounded-xl border border-amber-900/40 bg-amber-950/20 p-3.5">
        <div className="flex items-center justify-between text-amber-400 text-xs">
          <span>Cần rà soát (HITL)</span>
          <HelpCircle className="h-4 w-4 text-amber-400" />
        </div>
        <div className="mt-1 text-2xl font-bold text-amber-300">{kpiMetrics.uncertain_count}</div>
        <div className="text-[11px] text-amber-500/80 mt-0.5">Độ bất định U(p) cao</div>
      </div>

      <div className="rounded-xl border border-indigo-900/40 bg-indigo-950/20 p-3.5">
        <div className="flex items-center justify-between text-indigo-400 text-xs">
          <span>Tiết kiệm Token</span>
          <Zap className="h-4 w-4 text-indigo-400" />
        </div>
        <div className="mt-1 text-2xl font-bold text-indigo-300">
          {kpiMetrics.token_savings_percentage}%
        </div>
        <div className="text-[11px] text-indigo-400/80 mt-0.5">Nhờ Active Learning</div>
      </div>

      <div className="rounded-xl border border-cyan-900/40 bg-cyan-950/20 p-3.5">
        <div className="flex items-center justify-between text-cyan-400 text-xs">
          <span>Giờ đọc tiết kiệm</span>
          <Clock className="h-4 w-4 text-cyan-400" />
        </div>
        <div className="mt-1 text-2xl font-bold text-cyan-300">
          {kpiMetrics.estimated_hours_saved}h
        </div>
        <div className="text-[11px] text-cyan-400/80 mt-0.5">&ge; 50% mục tiêu ĐH X</div>
      </div>
    </div>
  )
}
