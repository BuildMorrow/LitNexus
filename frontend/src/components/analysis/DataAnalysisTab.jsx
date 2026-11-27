import { AlertTriangle, BarChart3, Bot, CheckCircle2 } from 'lucide-react'

export default function DataAnalysisTab({
  datasets,
  selectedDatasetId,
  setSelectedDatasetId,
  datasetName,
  setDatasetName,
  csvInput,
  setCsvInput,
  isProfiling,
  onUploadDataset,
  analysisGoal,
  setAnalysisGoal,
  isAdvising,
  onGetAnalysisAdvice,
  analysisResult,
}) {
  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 backdrop-blur">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-emerald-400 font-semibold text-sm">
              <BarChart3 className="h-4 w-4" />
              <span>Trụ cột 2 &bull; Trợ lý Phân tích Dữ liệu Ban đầu &amp; Sinh Code Tự động</span>
            </div>
            <p className="text-xs text-slate-300 mt-1 max-w-2xl leading-relaxed">
              Giải quyết bài toán SV và nghiên cứu viên thiếu kinh nghiệm chọn sai kiểm định thống kê.
              Hệ thống tự động phát hiện cỡ mẫu nhỏ (N &lt; 30), bất đối xứng dữ liệu, cảnh báo giới hạn nghiêm ngặt và sinh code Python mẫu (Pandas/Scipy).
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: CSV Profile & Ingestion */}
        <div className="lg:col-span-5 space-y-4">
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 space-y-4">
            <h4 className="text-sm font-semibold text-white flex items-center justify-between">
              <span>1. Dữ liệu Nghiên cứu Thực nghiệm</span>
              {datasets.length > 0 && (
                <span className="text-[11px] text-slate-400 font-normal">
                  {datasets.length} dataset sẵn sàng
                </span>
              )}
            </h4>

            {datasets.length > 0 && (
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Chọn Dataset:</label>
                <select
                  value={selectedDatasetId || ''}
                  onChange={(e) => setSelectedDatasetId(e.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-xs text-white focus:border-indigo-500 focus:outline-none"
                >
                  {datasets.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.dataset_name} (N={d.row_count}, {d.column_count} cột)
                    </option>
                  ))}
                </select>
              </div>
            )}

            <form onSubmit={onUploadDataset} className="space-y-3 pt-1 border-t border-slate-800/80">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Tên Tệp / Bộ Dữ Liệu</label>
                <input
                  type="text"
                  required
                  value={datasetName}
                  onChange={(e) => setDatasetName(e.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-xs text-white focus:border-indigo-500 focus:outline-none"
                  placeholder="Pilot_Patient_Data.csv"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Nội dung CSV (Dán văn bản thô hoặc upload)
                </label>
                <textarea
                  rows={6}
                  required
                  value={csvInput}
                  onChange={(e) => setCsvInput(e.target.value)}
                  className="w-full font-mono text-[11px] rounded-lg border border-slate-700 bg-slate-950 p-3 text-slate-200 focus:border-indigo-500 focus:outline-none leading-relaxed"
                  placeholder="col1,col2,col3&#10;val1,val2,val3"
                />
              </div>

              <button
                type="submit"
                disabled={isProfiling}
                className="w-full rounded-lg border border-emerald-500/40 bg-emerald-600/20 py-2 text-xs font-semibold text-emerald-300 hover:bg-emerald-600/30 transition disabled:opacity-50"
              >
                {isProfiling ? 'Đang phân tích schema...' : 'Nạp & Phân Tích Cấu Trúc Dataset'}
              </button>
            </form>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 space-y-3">
            <h4 className="text-sm font-semibold text-white">2. Mục tiêu Phân Tích Định Lượng</h4>
            <form onSubmit={onGetAnalysisAdvice} className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Câu hỏi thống kê hoặc bài toán cần kiểm định:
                </label>
                <textarea
                  rows={3}
                  required
                  value={analysisGoal}
                  onChange={(e) => setAnalysisGoal(e.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 p-2.5 text-xs text-slate-100 focus:border-indigo-500 focus:outline-none"
                  placeholder="So sánh độ nhạy mô hình giữa nhóm nhiễu thấp vs nhiễu cao..."
                />
              </div>

              <button
                type="submit"
                disabled={isAdvising}
                className="w-full flex items-center justify-center gap-2 rounded-lg bg-indigo-600 py-2.5 text-xs font-semibold text-white shadow-lg shadow-indigo-600/30 hover:bg-indigo-500 transition disabled:opacity-50"
              >
                <Bot className="h-4 w-4" />
                {isAdvising ? 'Đang tính toán kiểm định...' : 'Gợi Ý Phương Pháp & Sinh Code Phân Tích'}
              </button>
            </form>
          </div>
        </div>

        {/* Right Column */}
        <div className="lg:col-span-7 space-y-4">
          {!analysisResult ? (
            <div className="rounded-xl border border-slate-800 bg-slate-900/30 p-12 text-center text-xs text-slate-500">
              Chưa có kết quả phân tích. Hãy chọn bộ dữ liệu và nhấn &ldquo;Gợi Ý Phương Pháp &amp; Sinh Code Phân Tích&rdquo;.
            </div>
          ) : (
            <div className="space-y-4">
              {analysisResult.data_limitations && analysisResult.data_limitations.length > 0 && (
                <div className="space-y-2">
                  {analysisResult.data_limitations.map((w, idx) => (
                    <div
                      key={idx}
                      className={`rounded-xl border p-4 backdrop-blur ${
                        w.severity === 'high'
                          ? 'border-rose-500/50 bg-rose-950/20 text-rose-200'
                          : 'border-amber-500/50 bg-amber-950/20 text-amber-200'
                      }`}
                    >
                      <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider">
                        <AlertTriangle className="h-4 w-4 shrink-0" />
                        <span>Cảnh Báo Giới Hạn: {w.warning_type} ({w.severity.toUpperCase()})</span>
                      </div>
                      <p className="text-xs mt-1.5 font-medium">{w.message}</p>
                      <p className="text-[11px] opacity-90 mt-1 italic">
                        &bull; Khuyến nghị an toàn: {w.recommendation}
                      </p>
                    </div>
                  ))}
                </div>
              )}

              <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 space-y-3">
                <h4 className="text-sm font-semibold text-white flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                  Phương Pháp Thống Kê / ML Được Đề Xuất
                </h4>

                <div className="grid gap-3 sm:grid-cols-2">
                  {analysisResult.recommended_methods?.map((m, idx) => (
                    <div key={idx} className="rounded-lg border border-slate-800 bg-slate-950/70 p-3.5 space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-xs text-indigo-300">{m.method_name}</span>
                        <span className="text-[10px] rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-1.5 py-0.5">
                          {m.category}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-300 leading-relaxed">{m.rational}</p>
                      {m.assumptions && m.assumptions.length > 0 && (
                        <div className="text-[10px] text-slate-500 pt-1">
                          Giả định: {m.assumptions.join(' &bull; ')}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-semibold text-white">
                    Code Python Phân Tích Mẫu (Pandas &bull; Scipy &bull; Statsmodels)
                  </h4>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(analysisResult.suggested_python_code)
                      alert('Đã sao chép mã nguồn Python vào Clipboard!')
                    }}
                    className="rounded border border-slate-700 bg-slate-800 px-2.5 py-1 text-[11px] text-slate-300 hover:bg-slate-700 transition"
                  >
                    Sao chép Code
                  </button>
                </div>

                <pre className="overflow-x-auto rounded-lg border border-slate-800 bg-slate-950 p-4 font-mono text-xs text-indigo-200 leading-relaxed max-h-[360px]">
                  <code>{analysisResult.suggested_python_code}</code>
                </pre>
              </div>

              {analysisResult.interpretation_guide && (
                <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 space-y-2">
                  <h4 className="text-sm font-semibold text-white">
                    Hướng Dẫn Diễn Giải Kết Quả (Academic Reporting Style)
                  </h4>
                  <div className="rounded-lg border border-slate-800/80 bg-slate-950/60 p-4 text-xs text-slate-300 leading-relaxed whitespace-pre-line italic">
                    {analysisResult.interpretation_guide}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
