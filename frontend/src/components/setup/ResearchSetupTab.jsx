import { useState } from 'react'
import { Compass, ListChecks, Search, Sparkles, Wand2 } from 'lucide-react'
import { apiRequest } from '../../services/api'

export default function ResearchSetupTab({
  activeProject,
  isDemoMode,
  onApplyBooleanQuery,
}) {
  const [idea, setIdea] = useState(
    activeProject?.research_question ||
      'How do lightweight 1D CNNs perform on wearable single-lead ECG compared to 2D spectrogram models?'
  )
  const [domain, setDomain] = useState(activeProject?.domain || 'Biomedical AI & Wearable Sensors')
  const [scopeResult, setScopeResult] = useState(null)
  const [criteriaResult, setCriteriaResult] = useState(
    activeProject
      ? {
          inclusion_criteria: activeProject.inclusion_criteria || [],
          exclusion_criteria: activeProject.exclusion_criteria || [],
        }
      : null
  )
  const [picoResult, setPicoResult] = useState(null)
  const [loadingAgent, setLoadingAgent] = useState(null)
  const [errorMsg, setErrorMsg] = useState('')

  async function runScopeAgent() {
    setErrorMsg('')
    setLoadingAgent('scope')
    try {
      if (isDemoMode) {
        setScopeResult({
          status: 'optimal',
          score: 88,
          feedback:
            'Đề tài có kỹ thuật cụ thể (lightweight 1D CNN), đối tượng rõ ràng (single-lead wearable ECG) và mục tiêu so sánh rõ ràng với mô hình 2D spectrogram.',
          suggested_topics: [
            'Đánh giá hiệu năng và mức tiêu thụ năng lượng của 1D CNN lượng tử hóa so với 2D Spectrogram ResNet trên ECG đeo tay đơn kênh',
            'Phân tích độ bền vững trước nhiễu chuyển động của các kiến trúc 1D CNN nhẹ trong tầm soát rối loạn nhịp tim ngoại trú',
          ],
        })
        return
      }
      const res = await apiRequest('/projects/assist/scope-optimizer', {
        method: 'POST',
        body: JSON.stringify({ idea, domain }),
      })
      setScopeResult(res)
    } catch (err) {
      setErrorMsg(err.message)
    } finally {
      setLoadingAgent(null)
    }
  }

  async function runCriteriaAgent() {
    setErrorMsg('')
    setLoadingAgent('criteria')
    try {
      if (isDemoMode) {
        setCriteriaResult({
          inclusion_criteria: [
            'Công bố từ năm 2020–2026 tại tạp chí/hội nghị có bình duyệt (Peer-reviewed)',
            'Sử dụng kiến trúc 1D CNN trên tín hiệu ECG đeo tay 1 kênh hoặc ít kênh',
            'Có đánh giá định lượng (F1-score, Sensitivity, Latency hoặc Power) trên tập chuẩn/thực nghiệm',
          ],
          exclusion_criteria: [
            'Nghiên cứu trên động vật hoặc chỉ dùng ECG lâm sàng 12 chuyển đạo bệnh viện',
            'Bài báo tổng quan lý thuyết thuần túy không có thực nghiệm đối chứng',
            'Bài tóm tắt ngắn (< 3 trang) hoặc trùng lặp nội dung',
          ],
        })
        return
      }
      const res = await apiRequest('/projects/assist/criteria-generator', {
        method: 'POST',
        body: JSON.stringify({ idea, domain }),
      })
      setCriteriaResult(res)
    } catch (err) {
      setErrorMsg(err.message)
    } finally {
      setLoadingAgent(null)
    }
  }

  async function runPicoAgent() {
    setErrorMsg('')
    setLoadingAgent('pico')
    try {
      if (isDemoMode) {
        setPicoResult({
          population: 'Patients monitored via single-lead wearable ECG patches',
          intervention: 'Lightweight 1D Convolutional Neural Networks (1D CNN)',
          comparison: '2D Spectrogram CNN / ResNet baselines',
          outcome: 'Arrhythmia classification F1-score, sensitivity, and edge latency',
          search_keywords: [
            'wearable ECG',
            'single-lead ECG',
            '1D CNN',
            'arrhythmia classification',
            'edge deep learning',
          ],
          boolean_query: '("wearable ECG" OR "single-lead ECG") AND ("1D CNN" OR "1D convolutional") AND arrhythmia',
        })
        return
      }
      const res = await apiRequest('/projects/assist/pico-query', {
        method: 'POST',
        body: JSON.stringify({
          idea,
          domain,
          inclusion_criteria: criteriaResult?.inclusion_criteria || [],
          exclusion_criteria: criteriaResult?.exclusion_criteria || [],
        }),
      })
      setPicoResult(res)
    } catch (err) {
      setErrorMsg(err.message)
    } finally {
      setLoadingAgent(null)
    }
  }

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 backdrop-blur space-y-4">
        <div className="flex items-center gap-2 text-indigo-400 font-semibold text-sm">
          <Wand2 className="h-4 w-4" />
          <span>3 AI Agents Định Hình Đề Tài &amp; Chuẩn Bị Truy Vấn PRISMA (PICO Setup Swarm)</span>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed">
          Nhập ý tưởng thô hoặc câu hỏi nghiên cứu hiện tại. Ba agent chuyên biệt sẽ kiểm định độ rộng/hẹp phạm vi,
          sinh bộ tiêu chí chọn/loại PRISMA 2020 và trích xuất khung PICO + chuỗi Boolean chuẩn học thuật.
        </p>

        {errorMsg && (
          <div className="rounded-lg border border-rose-500/40 bg-rose-950/30 p-3 text-xs text-rose-300">
            {errorMsg}
          </div>
        )}

        <div className="grid gap-4 sm:grid-cols-3">
          <div className="sm:col-span-2">
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Ý tưởng / Câu hỏi Nghiên cứu
            </label>
            <textarea
              rows={2}
              value={idea}
              onChange={(e) => setIdea(e.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white focus:border-indigo-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Lĩnh vực (Domain)</label>
            <input
              type="text"
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white focus:border-indigo-500 focus:outline-none"
            />
          </div>
        </div>

        <div className="flex flex-wrap gap-3">
          <button
            onClick={runScopeAgent}
            disabled={loadingAgent !== null}
            className="inline-flex items-center gap-1.5 rounded-lg border border-indigo-500/40 bg-indigo-600/20 px-4 py-2 text-xs font-semibold text-indigo-300 hover:bg-indigo-600/30 transition disabled:opacity-50"
          >
            <Compass className="h-4 w-4" />
            {loadingAgent === 'scope' ? 'Đang chấm phạm vi...' : 'Agent 1: Kiểm định Phạm vi (Scope Optimizer)'}
          </button>

          <button
            onClick={runCriteriaAgent}
            disabled={loadingAgent !== null}
            className="inline-flex items-center gap-1.5 rounded-lg border border-emerald-500/40 bg-emerald-600/20 px-4 py-2 text-xs font-semibold text-emerald-300 hover:bg-emerald-600/30 transition disabled:opacity-50"
          >
            <ListChecks className="h-4 w-4" />
            {loadingAgent === 'criteria' ? 'Đang sinh tiêu chí...' : 'Agent 2: Sinh Tiêu chí PRISMA (Include/Exclude)'}
          </button>

          <button
            onClick={runPicoAgent}
            disabled={loadingAgent !== null}
            className="inline-flex items-center gap-1.5 rounded-lg border border-cyan-500/40 bg-cyan-600/20 px-4 py-2 text-xs font-semibold text-cyan-300 hover:bg-cyan-600/30 transition disabled:opacity-50"
          >
            <Sparkles className="h-4 w-4" />
            {loadingAgent === 'pico' ? 'Đang tạo PICO & Query...' : 'Agent 3: Trích xuất PICO & Boolean Query'}
          </button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Agent 1 Output */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 space-y-3">
          <h4 className="text-sm font-semibold text-white flex items-center gap-2">
            <Compass className="h-4 w-4 text-indigo-400" />
            1. Đánh giá Phạm vi Đề tài
          </h4>
          {!scopeResult ? (
            <p className="text-xs text-slate-500">Chưa chạy Agent 1.</p>
          ) : (
            <div className="space-y-3 text-xs">
              <div className="flex items-center justify-between">
                <span
                  className={`rounded px-2 py-0.5 font-bold uppercase ${
                    scopeResult.status === 'optimal'
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                      : 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                  }`}
                >
                  {scopeResult.status}
                </span>
                <span className="font-semibold text-indigo-300">Score: {scopeResult.score}/100</span>
              </div>
              <p className="text-slate-300 leading-relaxed">{scopeResult.feedback}</p>
              {scopeResult.suggested_topics?.length > 0 && (
                <div className="space-y-1.5 pt-2 border-t border-slate-800">
                  <div className="text-[11px] font-semibold text-slate-400">Đề tài tinh chỉnh gợi ý (bấm để chọn):</div>
                  {scopeResult.suggested_topics.map((t, idx) => (
                    <button
                      key={idx}
                      onClick={() => setIdea(t)}
                      className="block w-full text-left rounded-lg border border-slate-800 bg-slate-950 p-2 text-[11px] text-indigo-200 hover:border-indigo-500/40 transition"
                    >
                      {t}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Agent 2 Output */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 space-y-3">
          <h4 className="text-sm font-semibold text-white flex items-center gap-2">
            <ListChecks className="h-4 w-4 text-emerald-400" />
            2. Tiêu chí Sàng lọc PRISMA
          </h4>
          {!criteriaResult ? (
            <p className="text-xs text-slate-500">Chưa chạy Agent 2.</p>
          ) : (
            <div className="space-y-3 text-xs">
              <div>
                <div className="text-[11px] font-semibold text-emerald-400 mb-1">Inclusion Criteria:</div>
                <ul className="list-disc pl-4 space-y-1 text-slate-300">
                  {criteriaResult.inclusion_criteria?.map((c, idx) => (
                    <li key={idx}>{c}</li>
                  ))}
                </ul>
              </div>
              <div className="pt-2 border-t border-slate-800">
                <div className="text-[11px] font-semibold text-rose-400 mb-1">Exclusion Criteria:</div>
                <ul className="list-disc pl-4 space-y-1 text-slate-300">
                  {criteriaResult.exclusion_criteria?.map((c, idx) => (
                    <li key={idx}>{c}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>

        {/* Agent 3 Output */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 space-y-3">
          <h4 className="text-sm font-semibold text-white flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-cyan-400" />
            3. Khung PICO &amp; Boolean Query
          </h4>
          {!picoResult ? (
            <p className="text-xs text-slate-500">Chưa chạy Agent 3.</p>
          ) : (
            <div className="space-y-2.5 text-xs">
              <div className="grid grid-cols-1 gap-1.5 text-[11px]">
                <div className="rounded bg-slate-950 p-2 border border-slate-800">
                  <strong className="text-cyan-300">P:</strong> {picoResult.population}
                </div>
                <div className="rounded bg-slate-950 p-2 border border-slate-800">
                  <strong className="text-cyan-300">I:</strong> {picoResult.intervention}
                </div>
                <div className="rounded bg-slate-950 p-2 border border-slate-800">
                  <strong className="text-cyan-300">C:</strong> {picoResult.comparison}
                </div>
                <div className="rounded bg-slate-950 p-2 border border-slate-800">
                  <strong className="text-cyan-300">O:</strong> {picoResult.outcome}
                </div>
              </div>

              <div>
                <div className="text-[11px] font-semibold text-slate-400 mb-1">Boolean Search Query:</div>
                <pre className="rounded bg-slate-950 border border-slate-800 p-2.5 font-mono text-[11px] text-emerald-300 whitespace-pre-wrap">
                  {picoResult.boolean_query}
                </pre>
              </div>

              <button
                onClick={() => onApplyBooleanQuery(picoResult.boolean_query)}
                className="w-full inline-flex items-center justify-center gap-1.5 rounded-lg bg-cyan-600 py-2 text-xs font-semibold text-white hover:bg-cyan-500 transition"
              >
                <Search className="h-3.5 w-3.5" />
                Đẩy Truy vấn sang Bảng Tìm kiếm
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
