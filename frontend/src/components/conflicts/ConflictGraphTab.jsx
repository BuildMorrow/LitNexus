import { useMemo, useState } from 'react'
import { Background, Controls, MarkerType, ReactFlow } from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { Bot, GitCompare, Network, Sparkles } from 'lucide-react'

const EDGE_COLORS = {
  contradicts: '#f43f5e',
  assumption_mismatch: '#f59e0b',
  refines: '#38bdf8',
  supports: '#10b981',
}

export default function ConflictGraphTab({
  isAnalyzingConflicts,
  onRunConflictAnalysis,
  isLoadingGraph,
  graphData,
}) {
  const [selectedEdgeId, setSelectedEdgeId] = useState(null)

  const { flowNodes, flowEdges } = useMemo(() => {
    const nodes = graphData.nodes || []
    const edges = graphData.edges || []

    const computedNodes = nodes.map((n, idx) => {
      const col = idx % 3
      const row = Math.floor(idx / 3)
      const qColor =
        n.quartile === 'Q1'
          ? '#f59e0b'
          : n.quartile === 'Q2'
          ? '#38bdf8'
          : '#818cf8'
      return {
        id: String(n.id),
        position: { x: 40 + col * 290, y: 30 + row * 165 },
        data: {
          label: (
            <div className="text-left space-y-1">
              <div className="flex items-center justify-between gap-2 text-[10px] font-bold">
                <span style={{ color: qColor }}>{n.quartile || 'Scholar'}</span>
                <span className="text-slate-400">{n.year || ''}</span>
              </div>
              <div className="text-[11px] font-semibold text-white leading-snug line-clamp-2">
                {n.paper_title}
              </div>
              <div className="text-[10px] text-indigo-300 line-clamp-2">{n.label}</div>
            </div>
          ),
        },
        style: {
          width: 245,
          background: '#0f172a',
          color: '#f8fafc',
          border: `1.5px solid ${qColor}`,
          borderRadius: '10px',
          padding: '10px',
          fontSize: '11px',
        },
      }
    })

    const computedEdges = edges.map((e, idx) => {
      const eid = String(e.id || idx)
      const stroke = EDGE_COLORS[e.relation_type] || '#64748b'
      return {
        id: eid,
        source: String(e.source),
        target: String(e.target),
        label: `${e.relation_type} (${Math.round((e.confidence || 0.8) * 100)}%)`,
        animated: e.relation_type === 'contradicts',
        style: { stroke, strokeWidth: selectedEdgeId === eid ? 3 : 2 },
        labelStyle: { fill: '#f8fafc', fontSize: 10, fontWeight: 700 },
        labelBgStyle: { fill: '#0f172a', fillOpacity: 0.85 },
        markerEnd: { type: MarkerType.ArrowClosed, color: stroke },
      }
    })

    return { flowNodes: computedNodes, flowEdges: computedEdges }
  }, [graphData, selectedEdgeId])

  const selectedEdge =
    (graphData.edges || []).find((e, idx) => String(e.id || idx) === selectedEdgeId) || null

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 backdrop-blur flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-rose-400 font-semibold text-sm">
            <Network className="h-4 w-4" />
            <span>Đấu Trường Tranh Biện Học Thuật &bull; Interactive Conflict Graph &amp; Research Gaps</span>
          </div>
          <p className="text-xs text-slate-300 mt-1 max-w-2xl leading-relaxed">
            Hệ thống 3-Agent trích xuất luận điểm toàn văn có kiểm chứng trích dẫn (Verbatim Gate), dùng thuật toán
            tối ưu O(k&middot;N) bắt cặp đối chiếu (<span className="text-rose-400 font-medium">Contradicts</span>,{' '}
            <span className="text-amber-400 font-medium">Assumption Mismatch</span>) và vẽ đồ thị tương tác.
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

          {/* Interactive ReactFlow Network Canvas */}
          <div className="rounded-xl border border-slate-800 bg-slate-950 overflow-hidden">
            <div className="px-4 py-2.5 border-b border-slate-800 flex items-center justify-between text-xs">
              <span className="font-semibold text-white">
                Đồ thị Tranh biện Tương tác (Bấm vào cạnh nối để xem chi tiết tranh luận)
              </span>
              <div className="flex items-center gap-3 text-[10px]">
                <span className="text-rose-400">&bull; Contradicts</span>
                <span className="text-amber-400">&bull; Assumption Mismatch</span>
                <span className="text-cyan-400">&bull; Refines</span>
                <span className="text-emerald-400">&bull; Supports</span>
              </div>
            </div>
            <div style={{ height: 340, width: '100%' }}>
              <ReactFlow
                nodes={flowNodes}
                edges={flowEdges}
                fitView
                onEdgeClick={(_evt, edge) => setSelectedEdgeId(edge.id)}
              >
                <Background color="#1e293b" gap={18} />
                <Controls />
              </ReactFlow>
            </div>
          </div>

          {selectedEdge && (
            <div className="rounded-xl border border-rose-500/40 bg-rose-950/10 p-5 space-y-2">
              <div className="text-xs font-bold uppercase text-rose-300">
                Chi tiết Cạnh Đang Chọn: {selectedEdge.relation_type} ({Math.round((selectedEdge.confidence || 0.8) * 100)}%)
              </div>
              <div className="text-xs text-slate-200">{selectedEdge.debate_summary}</div>
              {selectedEdge.root_cause_hypothesis && (
                <div className="text-xs text-amber-200/90 italic">
                  Root Cause: {selectedEdge.root_cause_hypothesis}
                </div>
              )}
            </div>
          )}

          {/* Dialectical Edges Cards */}
          <div className="space-y-3">
            <h4 className="text-sm font-semibold text-white flex items-center gap-2">
              <GitCompare className="h-4 w-4 text-rose-400" />
              Chi Tiết Các Cặp Luận Điểm Đối Lập &amp; Giả Thuyết Nguyên Nhân Gốc Rễ
            </h4>

            {graphData.edges.map((e, idx) => (
              <div
                key={idx}
                onClick={() => setSelectedEdgeId(String(e.id || idx))}
                className="cursor-pointer rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3 hover:border-slate-700 transition"
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
