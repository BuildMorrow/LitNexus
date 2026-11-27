import { useState } from 'react'
import { AlertTriangle, BarChart3, Bot, CheckCircle2, Play, Terminal, Upload } from 'lucide-react'
import { apiRequest } from '../../services/api'

export default function DataAnalysisTab({
  projectId,
  isDemoMode,
  datasets,
  selectedDatasetId,
  setSelectedDatasetId,
  datasetName,
  setDatasetName,
  csvInput,
  setCsvInput,
  isProfiling,
  onUploadDataset,
  onReloadDatasets,
  analysisGoal,
  setAnalysisGoal,
  isAdvising,
  onGetAnalysisAdvice,
  analysisResult,
}) {
  const [editableCode, setEditableCode] = useState('')
  const [sandboxOutput, setSandboxOutput] = useState(null)
  const [isExecuting, setIsExecuting] = useState(false)
  const [isUploadingFile, setIsUploadingFile] = useState(false)

  const codeToRun = editableCode || analysisResult?.suggested_python_code || ''

  async function handleCsvFileUpload(file) {
    if (!file || !projectId) return
    setIsUploadingFile(true)
    try {
      if (isDemoMode) {
        const text = await file.text()
        setDatasetName(file.name)
        setCsvInput(text)
        alert(`[Demo Mode] Đã nạp nội dung file CSV "${file.name}".`)
        return
      }
      const formData = new FormData()
      formData.append('file', file)
      const created = await apiRequest(`/projects/${projectId}/analysis/datasets/upload-file`, {
        method: 'POST',
        body: formData,
      })
      onReloadDatasets?.()
      setSelectedDatasetId(created.id)
      alert(`Đã upload & profile file ${created.dataset_name} (N=${created.row_count})!`)
    } catch (err) {
      alert('Upload CSV failed: ' + err.message)
    } finally {
      setIsUploadingFile(false)
    }
  }

  async function handleExecuteSandbox() {
    if (!codeToRun.trim() || !selectedDatasetId) return
    setIsExecuting(true)
    try {
      if (isDemoMode) {
        await new Promise((res) => setTimeout(res, 500))
        setSandboxOutput({
          success: true,
          stdout: 'Mann-Whitney U statistic: 0.00, Exact p-value: 0.0380\n95% Bootstrap CI for median difference: [0.085, 0.165]',
          stderr: '',
          execution_time_ms: 142,
          figures: [],
          error: null,
        })
        return
      }
      const res = await apiRequest(
        `/projects/${projectId}/analysis/datasets/${selectedDatasetId}/execute`,
        {
          method: 'POST',
          body: JSON.stringify({ code: codeToRun, timeout_seconds: 10.0 }),
        }
      )
      setSandboxOutput(res)
    } catch (err) {
      setSandboxOutput({ success: false, error: err.message, stdout: '', figures: [] })
    } finally {
      setIsExecuting(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 backdrop-blur">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-emerald-400 font-semibold text-sm">
              <BarChart3 className="h-4 w-4" />
              <span>Trụ cột 2 &bull; Trợ lý Phân tích Dữ liệu &amp; Python Sandbox An Toàn</span>
            </div>
            <p className="text-xs text-slate-300 mt-1 max-w-2xl leading-relaxed">
              Tự động phát hiện cỡ mẫu nhỏ (N &lt; 30), bất đối xứng dữ liệu, cảnh báo giới hạn thống kê
              và cho phép chạy trực tiếp mã Python (Pandas/Scipy/Matplotlib) trong AST-Guarded Sandbox.
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: CSV Profile & Ingestion */}
        <div className="lg:col-span-5 space-y-4">
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-semibold text-white">1. Dữ liệu Nghiên cứu Thực nghiệm</h4>
              <label className="cursor-pointer inline-flex items-center gap-1 rounded border border-indigo-500/40 bg-indigo-600/15 px-2.5 py-1 text-[11px] font-semibold text-indigo-300 hover:bg-indigo-600/25">
                <Upload className="h-3 w-3" />
                {isUploadingFile ? 'Đang nạp...' : 'Upload .CSV'}
                <input
                  type="file"
                  accept=".csv,.tsv,text/csv"
                  className="hidden"
                  onChange={(e) => handleCsvFileUpload(e.target.files?.[0])}
                />
              </label>
            </div>

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
                  Nội dung CSV (Dán văn bản thô hoặc upload file)
                </label>
                <textarea
                  rows={6}
                  required
                  value={csvInput}
                  onChange={(e) => setCsvInput(e.target.value)}
                  className="w-full font-mono text-[11px] rounded-lg border border-slate-700 bg-slate-950 p-3 text-slate-200 focus:border-indigo-500 focus:outline-none leading-relaxed"
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
                    </div>
                  ))}
                </div>
              </div>

              {/* Editable Python Code + Sandbox Runner */}
              <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h4 className="text-sm font-semibold text-white">
                    Python EDA Sandbox (Tự động nạp DataFrame <code className="text-emerald-300">df</code>)
                  </h4>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(codeToRun)
                        alert('Đã sao chép mã nguồn Python vào Clipboard!')
                      }}
                      className="rounded border border-slate-700 bg-slate-800 px-2.5 py-1 text-[11px] text-slate-300 hover:bg-slate-700 transition"
                    >
                      Sao chép
                    </button>
                    <button
                      onClick={handleExecuteSandbox}
                      disabled={isExecuting}
                      className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-500 transition disabled:opacity-50"
                    >
                      <Play className="h-3.5 w-3.5" />
                      {isExecuting ? 'Đang thực thi...' : 'Chạy Code trong Sandbox'}
                    </button>
                  </div>
                </div>

                <textarea
                  rows={10}
                  value={codeToRun}
                  onChange={(e) => setEditableCode(e.target.value)}
                  className="w-full rounded-lg border border-slate-800 bg-slate-950 p-4 font-mono text-xs text-indigo-200 focus:border-indigo-500 focus:outline-none leading-relaxed"
                />

                {sandboxOutput && (
                  <div className="rounded-lg border border-slate-700 bg-slate-950 p-4 space-y-3">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="flex items-center gap-1.5 font-semibold text-emerald-400">
                        <Terminal className="h-3.5 w-3.5" />
                        Kết quả Thực thi Sandbox
                      </span>
                      <span className="text-slate-400">Thời gian: {sandboxOutput.execution_time_ms} ms</span>
                    </div>

                    {sandboxOutput.error && (
                      <div className="rounded border border-rose-500/40 bg-rose-950/30 p-2.5 text-xs text-rose-300 font-mono">
                        {sandboxOutput.error}
                      </div>
                    )}

                    {sandboxOutput.stdout && (
                      <pre className="rounded bg-slate-900 p-3 font-mono text-xs text-emerald-200 whitespace-pre-wrap">
                        {sandboxOutput.stdout}
                      </pre>
                    )}

                    {sandboxOutput.figures && sandboxOutput.figures.length > 0 && (
                      <div className="grid gap-3">
                        {sandboxOutput.figures.map((b64, fIdx) => (
                          <img
                            key={fIdx}
                            src={`data:image/png;base64,${b64}`}
                            alt={`Sandbox Plot ${fIdx + 1}`}
                            className="rounded-lg border border-slate-700 bg-white max-w-full"
                          />
                        ))}
                      </div>
                    )}
                  </div>
                )}
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
