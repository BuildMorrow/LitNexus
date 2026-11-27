import { Bot, GitCompare, Network, Sparkles } from 'lucide-react'

export default function ConflictGraphTab({
  isAnalyzingConflicts,
  onRunConflictAnalysis,
  isLoadingGraph,
  graphData,
}) {
  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 backdrop-blur flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-rose-400 font-semibold text-sm">
            <Network className="h-4 w-4" />
            <span>Đấu Trường Tranh Biện Học Thuật &bull; Phát Hiện Mâu Thuẫn Thực Nghiệm &amp; Đề Xuất Đề Tài Mới</span>
          </div>
          <p className="text-xs text-slate-300 mt-1 max-w-2xl leading-relaxed">
            Hệ thống 3-Agent đối chiếu biện chứng giữa các bài báo cốt lõi (Included) để phân loại các cạnh đối lập
            (<span className="text-rose-400 font-medium">Contradicts</span>,{' '}
            <span className="text-amber-400 font-medium">Assumption Mismatch</span>)
            và tổng hợp ra Top Khoảng trống nghiên cứu (Research Gaps) có tính mới cao.
          </p>
        </div>

        <button
          onClick={onRunConflictAnalysis}
          disabled={isAnalyzingConflicts}
          className="shrink-0 flex items-center justify-center gap-2 rounded-lg bg-rose-600 px-4 py-2 text-xs font-semibold text-white shadow-lg shadow-rose-600/30 hover:bg-rose-500 transition disabled:opacity-50"
        >
          <Bot className="h-4 w-4" />
          {isAnalyzingConflicts ? 'Đang phân tích 3-Agent...' : 'Chạy Phân Tích Mâu Thuẫn 3-Agent'}
        </button>
      </div>

      {isLoadingGraph ? (
        <div className="py-12 text-center text-xs text-slate-500">Đang tải đồ thị tranh biện...</div>
      ) : graphData.edges?.length === 0 ? (
        <div className="rounded-xl border border-slate-800 bg-slate-900/30 p-12 text-center text-xs text-slate-500">
          Chưa có mâu thuẫn nào được phân tích. Hãy nhấn &ldquo;Chạy Phân Tích Mâu Thuẫn 3-Agent&rdquo; ở trên (yêu cầu ít nhất 2 bài báo Included).
        </div>
      ) : (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
              <div className="text-xs text-slate-400">Tổng Luận Điểm Đã Bóc Tách</div>
              <div className="text-xl font-bold text-white mt-1">{graphData.total_nodes} nodes</div>
            </div>
            <div className="rounded-xl border border-rose-900/40 bg-rose-950/20 p-4">
              <div className="text-xs text-rose-400">Mâu Thuẫn Đối Lập Trực Tiếp</div>
              <div className="text-xl font-bold text-rose-300 mt-1">{graphData.contradiction_count} cạnh</div>
            </div>
            <div className="rounded-xl border border-indigo-900/40 bg-indigo-950/20 p-4">
              <div className="text-xs text-indigo-400">Tổng Số Cạnh Quan Hệ</div>
              <div className="text-xl font-bold text-indigo-300 mt-1">{graphData.total_edges} edges</div>
            </div>
          </div>

          <div className="space-y-3">
            <h4 className="text-sm font-semibold text-white flex items-center gap-2">
              <GitCompare className="h-4 w-4 text-rose-400" />
              Chi Tiết Các Cặp Luận Điểm Đối Lập &amp; Giả Thuyết Nguyên Nhân Gốc Rễ
            </h4>

            {graphData.edges.map((e, idx) => (
              <div
                key={idx}
                className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3 hover:border-slate-700 transition"
              >
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
                  <div className="flex items-center gap-2">
                    <span
                      className={`rounded px-2.5 py-0.5 text-xs font-bold uppercase ${
                        e.relation_type === 'contradicts'
                          ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                          : e.relation_type === 'assumption_mismatch'
                          ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                          : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                      }`}
                    >
                      {e.relation_type}
                    </span>
                    <span className="text-xs text-slate-400">
                      Độ tin cậy của Agent: <strong className="text-white">{(e.confidence * 100).toFixed(0)}%</strong>
                    </span>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="text-xs text-slate-200">
                    <span className="font-semibold text-indigo-300">Tóm tắt cuộc tranh biện:</span> {e.debate_summary}
                  </div>
                  {e.root_cause_hypothesis && (
                    <div className="text-xs text-amber-200/90 rounded-lg bg-amber-950/20 border border-amber-500/20 p-3 italic">
                      <span className="font-semibold not-italic">Nguyên nhân gốc rễ (Root Cause Hypothesis):</span>{' '}
                      {e.root_cause_hypothesis}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {graphData.research_gaps && graphData.research_gaps.length > 0 && (
            <div className="space-y-3 pt-4">
              <h4 className="text-sm font-semibold text-white flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-indigo-400" />
                Top Khoảng Trống Nghiên Cứu Đề Xuất (Novelty Ranked Research Gaps)
              </h4>

              <div className="grid gap-4 sm:grid-cols-2">
                {graphData.research_gaps.map((gap, idx) => (
                  <div
                    key={idx}
                    className="rounded-xl border border-indigo-500/30 bg-gradient-to-br from-indigo-950/30 to-slate-900/60 p-5 space-y-3"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <h5 className="text-sm font-bold text-white">{gap.title}</h5>
                      <span className="shrink-0 rounded-full bg-indigo-500/20 border border-indigo-500/40 px-2.5 py-0.5 text-[11px] font-bold text-indigo-300">
                        Novelty: {gap.novelty_score?.toFixed(2)}
                      </span>
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed">{gap.description}</p>
                    <div className="rounded-lg bg-slate-950/60 p-3 text-[11px] text-emerald-300 border border-emerald-500/20">
                      <span className="font-semibold">Hướng thực nghiệm gợi ý:</span> {gap.suggested_direction}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
