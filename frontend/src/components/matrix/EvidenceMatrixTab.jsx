import { FileText } from 'lucide-react'

export default function EvidenceMatrixTab({
  isLoadingMatrix,
  matrixData,
  onReload,
}) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-semibold text-white">
            Bảng Ma trận So sánh Bằng chứng (Comparative Evidence Matrix)
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Mọi luận điểm đều được neo chặt vào câu trích dẫn nguyên văn (`evidence_quote`) chống bịa nguồn.
          </p>
        </div>

        <button
          onClick={onReload}
          className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs text-slate-200 hover:bg-slate-700 transition"
        >
          Tải lại ma trận
        </button>
      </div>

      {isLoadingMatrix ? (
        <div className="py-12 text-center text-sm text-slate-500">Đang tải ma trận so sánh...</div>
      ) : matrixData.length === 0 ? (
        <div className="py-12 text-center text-sm text-slate-500">
          Chưa có claim nào được trích xuất từ các bài Included. Hãy đảm bảo có ít nhất 2 bài Included và chạy
          Conflict Analysis.
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-slate-800">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="px-4 py-3">Bài báo &bull; Năm &bull; Quartile</th>
                <th className="px-4 py-3">Luận điểm chính (Claim)</th>
                <th className="px-4 py-3">Phương pháp (Methodology)</th>
                <th className="px-4 py-3">Dataset &bull; Metrics</th>
                <th className="px-4 py-3">Giả định (Assumptions)</th>
                <th className="px-4 py-3">Bằng chứng trích dẫn (Evidence Quote)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {matrixData.map((row, idx) => (
                <tr key={idx} className="hover:bg-slate-850/30">
                  <td className="px-4 py-3 font-medium text-white max-w-[200px]">
                    {row.paper_title}
                    <div className="text-[11px] text-slate-400 font-normal mt-0.5">
                      {row.year || 'N/A'} &bull; {row.scopus_quartile || 'None'}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-indigo-300 max-w-[220px]">{row.claim_text}</td>
                  <td className="px-4 py-3 text-slate-200">{row.methodology}</td>
                  <td className="px-4 py-3">
                    <div className="font-semibold text-slate-200">{row.dataset}</div>
                    <div className="text-[11px] text-emerald-400 mt-0.5">{row.metric_summary}</div>
                  </td>
                  <td className="px-4 py-3 text-slate-400 max-w-[150px]">
                    {row.assumptions && row.assumptions.length > 0
                      ? row.assumptions.join(', ')
                      : 'None'}
                  </td>
                  <td className="px-4 py-3 text-amber-200/90 bg-amber-950/10 max-w-[280px] border-l border-amber-500/20">
                    <div className="italic">&ldquo;{row.evidence_quote}&rdquo;</div>
                    {(row.page_number || row.section_title) && (
                      <div className="mt-2 flex flex-wrap items-center gap-1.5 not-italic">
                        {row.page_number && (
                          <span className="inline-flex items-center gap-1 rounded bg-indigo-500/20 border border-indigo-500/40 px-1.5 py-0.5 text-[10px] font-semibold text-indigo-300">
                            <FileText className="h-2.5 w-2.5" />
                            Trang p.{row.page_number}
                          </span>
                        )}
                        {row.section_title && (
                          <span className="inline-flex items-center rounded bg-slate-800 border border-slate-700 px-1.5 py-0.5 text-[10px] text-slate-300 font-medium">
                            {row.section_title}
                          </span>
                        )}
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
