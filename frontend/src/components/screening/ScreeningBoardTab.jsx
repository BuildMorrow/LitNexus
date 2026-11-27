import { useState } from 'react'
import {
  AlertTriangle,
  Bot,
  CheckCircle2,
  FileText,
  GitBranch,
  History,
  Scale,
  Search,
  ShieldCheck,
  XCircle,
  Zap,
} from 'lucide-react'

export default function ScreeningBoardTab({
  searchQuery,
  setSearchQuery,
  searchLimit,
  setSearchLimit,
  yearFrom,
  setYearFrom,
  yearTo,
  setYearTo,
  openAccessOnly,
  setOpenAccessOnly,
  isSearching,
  onSearch,
  searchHistory,
  isRunningAL,
  onRunActiveLearning,
  isRunningLLM,
  onAutoLabelUncertain,
  isRunningDualPeer,
  onRunDualPeer,
  isSnowballing,
  onSnowball,
  qualityGate,
  papers,
  onLabelPaper,
  onHitlApprove,
  onIngestPdf,
  ingestingPaperId,
}) {
  const [expandedAuditId, setExpandedAuditId] = useState(null)
  const includedSeedCount = papers.filter((p) => p.screening_status === 'included').length

  return (
    <div className="space-y-6">
      {/* Quality Gate >= 80% Grounding Banner */}
      {qualityGate && (
        <div
          className={`rounded-xl border p-4 backdrop-blur flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
            qualityGate.passed
              ? 'border-emerald-500/40 bg-emerald-950/20 text-emerald-200'
              : 'border-amber-500/40 bg-amber-950/20 text-amber-200'
          }`}
        >
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider">
              {qualityGate.passed ? (
                <ShieldCheck className="h-4 w-4 text-emerald-400" />
              ) : (
                <AlertTriangle className="h-4 w-4 text-amber-400" />
              )}
              <span>
                Quality Gate (Evidence Grounding &ge; {(qualityGate.grounding_threshold * 100).toFixed(0)}%):{' '}
                {qualityGate.passed ? 'ĐẠT CHUẨN XUẤT BẢN' : 'CẦN RÀ SOÁT HITL'}
              </span>
            </div>
            {qualityGate.warnings && qualityGate.warnings.length > 0 && (
              <ul className="text-xs space-y-0.5 opacity-90 list-disc pl-5">
                {qualityGate.warnings.map((w, idx) => (
                  <li key={idx}>{w}</li>
                ))}
              </ul>
            )}
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <div className="rounded-lg bg-slate-950/70 border border-slate-800 px-3 py-1.5 text-center">
              <div className="text-[10px] text-slate-400">Grounding Precision</div>
              <div className="text-sm font-bold text-white">
                {(qualityGate.grounding_precision * 100).toFixed(0)}%
              </div>
            </div>
            <div className="rounded-lg bg-slate-950/70 border border-slate-800 px-3 py-1.5 text-center">
              <div className="text-[10px] text-slate-400">Included / Min</div>
              <div className="text-sm font-bold text-white">
                {qualityGate.included_count} / {qualityGate.min_papers}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Search & Ingestion Box */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 backdrop-blur space-y-3">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <Search className="h-4 w-4 text-indigo-400" />
          Tìm kiếm &amp; Nạp Bài báo Học thuật Miễn phí (OpenAlex &bull; SCImago SJR)
        </h3>
        <form onSubmit={onSearch} className="space-y-3">
          <div className="flex flex-col sm:flex-row gap-2">
            <input
              type="text"
              required
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="flex-1 rounded-lg border border-slate-700 bg-slate-950 px-4 py-2 text-sm text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
              placeholder="Nhập từ khóa học thuật (vd: wearable ECG 1D CNN arrhythmia)..."
            />
            <button
              type="submit"
              disabled={isSearching}
              className="inline-flex items-center justify-center gap-2 rounded-lg bg-indigo-600 px-5 py-2 text-sm font-semibold text-white hover:bg-indigo-500 disabled:opacity-50 transition"
            >
              {isSearching ? 'Đang truy vấn OpenAlex...' : 'Tìm & Nạp bài báo'}
            </button>
          </div>

          <div className="flex flex-wrap items-center gap-4 pt-1 text-xs text-slate-400">
            <div className="flex items-center gap-1.5">
              <span>Số bài nạp:</span>
              <select
                value={searchLimit}
                onChange={(e) => setSearchLimit(e.target.value)}
                className="rounded border border-slate-700 bg-slate-950 px-2 py-0.5 text-xs text-slate-200"
              >
                <option value={10}>10</option>
                <option value={25}>25</option>
                <option value={50}>50</option>
              </select>
            </div>

            <div className="flex items-center gap-1.5">
              <span>Từ năm:</span>
              <input
                type="number"
                placeholder="2020"
                value={yearFrom}
                onChange={(e) => setYearFrom(e.target.value)}
                className="w-16 rounded border border-slate-700 bg-slate-950 px-1.5 py-0.5 text-xs text-slate-200 text-center"
              />
            </div>

            <div className="flex items-center gap-1.5">
              <span>Đến năm:</span>
              <input
                type="number"
                placeholder="2026"
                value={yearTo}
                onChange={(e) => setYearTo(e.target.value)}
                className="w-16 rounded border border-slate-700 bg-slate-950 px-1.5 py-0.5 text-xs text-slate-200 text-center"
              />
            </div>

            <label className="flex items-center gap-1.5 cursor-pointer">
              <input
                type="checkbox"
                checked={openAccessOnly}
                onChange={(e) => setOpenAccessOnly(e.target.checked)}
                className="rounded border-slate-700 bg-slate-950 text-indigo-600 focus:ring-0"
              />
              <span>Chỉ lấy bài Open Access / Toàn văn miễn phí</span>
            </label>
          </div>
        </form>

        {searchHistory && searchHistory.length > 0 && (
          <div className="pt-2 border-t border-slate-800/80 flex flex-wrap items-center gap-2 text-[11px]">
            <span className="flex items-center gap-1 text-slate-400">
              <History className="h-3.5 w-3.5" />
              Lịch sử:
            </span>
            {searchHistory.slice(0, 5).map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => setSearchQuery(item.query_string)}
                className="rounded-full border border-slate-700 bg-slate-950 px-2.5 py-0.5 text-slate-300 hover:border-indigo-500/40 hover:text-indigo-300 transition"
              >
                {item.query_string} ({item.result_count})
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Action Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-800 bg-slate-900/60 p-4">
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-medium">Quy trình Phễu Sàng lọc:</span>
          <span className="text-xs text-slate-300">
            Active Learning lọc nhanh &rarr; Phản biện mù đôi (Inclusive vs Strict) cho bài phân vân.
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={onRunActiveLearning}
            disabled={isRunningAL}
            className="inline-flex items-center gap-1.5 rounded-lg border border-indigo-500/40 bg-indigo-600/20 px-3 py-1.5 text-xs font-semibold text-indigo-300 hover:bg-indigo-600/30 transition disabled:opacity-50"
          >
            <Zap className="h-4 w-4" />
            {isRunningAL ? 'Đang train ML...' : 'Active Learning'}
          </button>

          <button
            onClick={onRunDualPeer}
            disabled={isRunningDualPeer}
            className="inline-flex items-center gap-1.5 rounded-lg border border-amber-500/40 bg-amber-600/20 px-3 py-1.5 text-xs font-semibold text-amber-300 hover:bg-amber-600/30 transition disabled:opacity-50"
            title="Chạy song song Inclusive Reviewer vs Strict Reviewer + Trọng tài + Kiểm chứng trích dẫn"
          >
            <Scale className="h-4 w-4" />
            {isRunningDualPeer ? 'Đang phản biện...' : 'Phản biện Mù đôi (Dual-Peer)'}
          </button>

          <button
            onClick={onAutoLabelUncertain}
            disabled={isRunningLLM}
            className="inline-flex items-center gap-1.5 rounded-lg border border-emerald-500/40 bg-emerald-600/20 px-3 py-1.5 text-xs font-semibold text-emerald-300 hover:bg-emerald-600/30 transition disabled:opacity-50"
          >
            <Bot className="h-4 w-4" />
            {isRunningLLM ? 'LLM đang đọc...' : 'AI Batch (10 bài)'}
          </button>

          <button
            onClick={() => onSnowball()}
            disabled={isSnowballing || includedSeedCount === 0}
            className="inline-flex items-center gap-1.5 rounded-lg border border-cyan-500/40 bg-cyan-600/20 px-3 py-1.5 text-xs font-semibold text-cyan-300 hover:bg-cyan-600/30 transition disabled:opacity-50"
          >
            <GitBranch className="h-4 w-4" />
            {isSnowballing ? 'Đang Snowball...' : `Snowball (${includedSeedCount} seeds)`}
          </button>
        </div>
      </div>

      {/* Papers Review Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/40 overflow-hidden shadow-xl">
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-white">
            Danh sách Bài báo ({papers.length} bài) &bull; Tự động xếp bài có độ bất định cao nhất lên đầu
          </h3>
        </div>

        {papers.length === 0 ? (
          <div className="py-12 text-center text-sm text-slate-500">
            Chưa có bài báo nào trong project. Hãy nhập từ khóa tìm kiếm ở trên để nạp dữ liệu.
          </div>
        ) : (
          <div className="divide-y divide-slate-800/80">
            {papers.map((paper) => {
              const prob = paper.al_inclusion_prob
              const unc = paper.al_uncertainty_score
              const isUncertain = unc && unc >= 0.7
              const rationale = paper.screening_rationale || {}
              const hasOpinions = Array.isArray(rationale.opinions) && rationale.opinions.length > 0
              const gScore = rationale.grounding_score

              return (
                <div key={paper.id} className="p-5 hover:bg-slate-850/40 transition space-y-3">
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                    <div className="space-y-2 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        {paper.scopus_quartile && (
                          <span className="rounded bg-amber-500/10 border border-amber-500/30 px-2 py-0.5 text-[11px] font-bold text-amber-400">
                            {paper.scopus_quartile}
                          </span>
                        )}
                        {paper.discovery_source && paper.discovery_source !== 'keyword' && (
                          <span className="rounded bg-cyan-500/10 border border-cyan-500/30 px-2 py-0.5 text-[10px] font-semibold text-cyan-300">
                            {paper.discovery_source === 'backward_snowball'
                              ? 'Backward Snowball'
                              : 'Forward Snowball'}
                          </span>
                        )}
                        {paper.year && (
                          <span className="text-xs text-slate-400 font-medium">({paper.year})</span>
                        )}
                        {paper.journal && (
                          <span className="text-xs text-slate-400 italic">
                            &bull; {paper.journal}
                          </span>
                        )}
                        <span
                          className={`rounded px-2 py-0.5 text-[11px] font-medium border ${
                            paper.screening_status === 'included'
                              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                              : paper.screening_status === 'excluded'
                              ? 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                              : paper.screening_status === 'uncertain'
                              ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                              : 'bg-slate-800 text-slate-400 border-slate-700'
                          }`}
                        >
                          {paper.screening_status.toUpperCase()} ({paper.screening_source})
                        </span>

                        {gScore !== undefined && gScore !== null && (
                          <span
                            className={`rounded px-2 py-0.5 text-[10px] font-bold border ${
                              gScore >= 0.8
                                ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
                                : 'bg-rose-500/15 text-rose-300 border-rose-500/30'
                            }`}
                          >
                            Grounding: {(gScore * 100).toFixed(0)}%
                          </span>
                        )}

                        {rationale.hitl_approved && (
                          <span className="rounded bg-indigo-500/15 border border-indigo-500/30 px-2 py-0.5 text-[10px] font-semibold text-indigo-300">
                            HITL Verified
                          </span>
                        )}
                      </div>

                      <h4 className="text-base font-semibold text-white leading-snug">
                        {paper.title}
                      </h4>

                      {paper.authors && paper.authors.length > 0 && (
                        <p className="text-xs text-slate-400">
                          Tác giả: {paper.authors.slice(0, 4).join(', ')}
                          {paper.authors.length > 4 ? ' et al.' : ''}
                        </p>
                      )}

                      <p className="text-xs text-slate-300 line-clamp-3 leading-relaxed">
                        {paper.abstract || 'Không có đoạn tóm tắt khả dụng.'}
                      </p>

                      <div className="flex flex-wrap items-center gap-4 pt-1 text-[11px] text-slate-400">
                        {prob !== null && prob !== undefined && (
                          <>
                            <div>
                              Xác suất phù hợp (p):{' '}
                              <span className="font-semibold text-indigo-300">
                                {(prob * 100).toFixed(1)}%
                              </span>
                            </div>
                            <div>
                              Độ bất định (U):{' '}
                              <span
                                className={`font-semibold ${
                                  isUncertain ? 'text-amber-400' : 'text-slate-400'
                                }`}
                              >
                                {unc?.toFixed(2)}
                              </span>
                            </div>
                          </>
                        )}

                        {(hasOpinions || rationale.reason) && (
                          <button
                            type="button"
                            onClick={() =>
                              setExpandedAuditId(expandedAuditId === paper.id ? null : paper.id)
                            }
                            className="text-indigo-400 hover:text-indigo-300 underline"
                          >
                            {expandedAuditId === paper.id
                              ? 'Ẩn chi tiết Phản biện'
                              : 'Xem lập luận AI & Bằng chứng'}
                          </button>
                        )}
                      </div>
                    </div>

                    <div className="flex sm:flex-col items-center gap-2 shrink-0">
                      <button
                        onClick={() => onLabelPaper(paper.id, 'included')}
                        className="w-24 rounded-lg border border-emerald-500/40 bg-emerald-600/10 px-3 py-1.5 text-xs font-semibold text-emerald-400 hover:bg-emerald-600/20 transition flex items-center justify-center gap-1"
                      >
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        Include
                      </button>
                      <button
                        onClick={() => onLabelPaper(paper.id, 'excluded')}
                        className="w-24 rounded-lg border border-rose-500/40 bg-rose-600/10 px-3 py-1.5 text-xs font-semibold text-rose-400 hover:bg-rose-600/20 transition flex items-center justify-center gap-1"
                      >
                        <XCircle className="h-3.5 w-3.5" />
                        Exclude
                      </button>
                      <button
                        onClick={() => onIngestPdf(paper)}
                        disabled={ingestingPaperId === paper.id}
                        className="w-24 rounded-lg border border-indigo-500/40 bg-indigo-600/10 px-2 py-1.5 text-[11px] font-semibold text-indigo-300 hover:bg-indigo-600/20 transition flex items-center justify-center gap-1 disabled:opacity-50"
                        title="Bóc tách PDF toàn văn và phân đoạn semantic neo số trang"
                      >
                        <FileText className="h-3.5 w-3.5" />
                        {ingestingPaperId === paper.id ? 'Đang nạp...' : 'Nạp PDF'}
                      </button>
                    </div>
                  </div>

                  {/* Expandable Dual-Peer Audit & HITL Verification Drawer */}
                  {expandedAuditId === paper.id && (
                    <div className="rounded-lg border border-slate-800 bg-slate-950/70 p-4 space-y-3 text-xs">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <span className="font-semibold text-indigo-300">
                          Giải trình Sàng lọc &amp; Bằng chứng Xác minh
                        </span>
                        {!rationale.hitl_approved && (
                          <button
                            onClick={() => onHitlApprove(paper.id)}
                            className="rounded border border-emerald-500/40 bg-emerald-600/20 px-2.5 py-1 text-[11px] font-semibold text-emerald-300 hover:bg-emerald-600/30 transition"
                          >
                            Xác nhận HITL (Approve Verdict)
                          </button>
                        )}
                      </div>
                      {rationale.reason && (
                        <p className="text-slate-300 leading-relaxed">{rationale.reason}</p>
                      )}
                      {rationale.evidence_quote && (
                        <div className="rounded border-l-2 border-amber-500/60 bg-amber-950/20 p-2.5 italic text-amber-200/90">
                          &ldquo;{rationale.evidence_quote}&rdquo;
                        </div>
                      )}
                      {hasOpinions && (
                        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3 pt-1">
                          {rationale.opinions.map((op, idx) => (
                            <div
                              key={idx}
                              className="rounded border border-slate-800 bg-slate-900/70 p-2.5 space-y-1"
                            >
                              <div className="flex items-center justify-between">
                                <span className="font-bold uppercase text-[10px] text-cyan-300">
                                  {op.reviewer_role}
                                </span>
                                <span className="text-[10px] text-slate-300">
                                  {op.decision.toUpperCase()} ({(op.confidence * 100).toFixed(0)}%)
                                </span>
                              </div>
                              <p className="text-[11px] text-slate-300">{op.reason}</p>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
