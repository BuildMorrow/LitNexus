import { useState } from 'react'
import { FileText, MessageSquare, Send, ShieldCheck, Upload } from 'lucide-react'
import { apiRequest } from '../../services/api'

export default function WorkspaceRagTab({
  projectId,
  papers,
  messages,
  setMessages,
  isDemoMode,
  onReloadPapers,
}) {
  const [question, setQuestion] = useState(
    'So sánh độ chính xác F1-score và khả năng chịu nhiễu chuyển động giữa các mô hình 1D CNN?'
  )
  const [selectedPaperIds, setSelectedPaperIds] = useState([])
  const [isSending, setIsSending] = useState(false)
  const [uploadingPaperId, setUploadingPaperId] = useState(null)
  const [activeCitation, setActiveCitation] = useState(null)
  const [highlightData, setHighlightData] = useState(null)
  const [isLoadingHighlight, setIsLoadingHighlight] = useState(false)

  const includedOrAll = papers.filter((p) => p.screening_status === 'included')
  const selectablePapers = includedOrAll.length > 0 ? includedOrAll : papers

  function togglePaper(pid) {
    setSelectedPaperIds((prev) =>
      prev.includes(pid) ? prev.filter((x) => x !== pid) : [...prev, pid]
    )
  }

  async function handleSendChat(e) {
    e.preventDefault()
    if (!question.trim() || !projectId) return
    const currentQ = question.trim()
    setQuestion('')
    setIsSending(true)

    const userBubble = { id: `u-${Date.now()}`, role: 'user', content: currentQ, citations: [], guardrail: {} }
    setMessages((prev) => [...prev, userBubble])

    try {
      if (isDemoMode) {
        await new Promise((res) => setTimeout(res, 500))
        const demoReply = {
          id: `a-${Date.now()}`,
          role: 'assistant',
          content:
            'Mô hình 1D CNN nhẹ đạt F1 = 98.2% trên tập MIT-BIH với độ trễ 18ms trong điều kiện ít nhiễu [1]. Khi hoạt động trong môi trường vận động thực tế, phiên bản lượng tử hóa 8-bit giữ được độ nhạy 97.8% ở mức công suất 1.2mW [2].',
          citations: [
            {
              index: 1,
              paper_id: 'p1',
              paper_title: 'Real-Time ECG Arrhythmia Classification Using Lightweight 1D Convolutional Neural Networks',
              page_number: 1,
              section_title: '3. Experimental Results',
              excerpt:
                'Our lightweight 1D CNN architecture achieves 98.2% F1 on MIT-BIH with only 45k parameters, cutting inference latency to 18ms.',
              retrieval_score: 0.032,
            },
            {
              index: 2,
              paper_id: 'p3',
              paper_title: 'Ultra-low Power Neural Accelerators for Single-Lead Patch Arrhythmia Screening',
              page_number: 4,
              section_title: 'Methodology & Benchmarks',
              excerpt:
                'The 8-bit quantized 1D model retained 97.8% sensitivity under continuous ambulatory motion with 1.2mW power draw.',
              retrieval_score: 0.029,
            },
          ],
          guardrail: {
            is_safe: true,
            safety_verdict: 'VERIFIED_HIGH_CONFIDENCE',
            faithfulness_score: 1.0,
            hallucination_rate: 0.0,
            citation_precision: 1.0,
            summary_verdict: 'Độ tin cậy cao: 2/2 nhận định được neo nguồn xác thực (100%).',
          },
        }
        setMessages((prev) => [...prev, demoReply])
        return
      }

      const res = await apiRequest(`/projects/${projectId}/workspace/chat`, {
        method: 'POST',
        body: JSON.stringify({
          question: currentQ,
          paper_ids: selectedPaperIds.length > 0 ? selectedPaperIds : null,
        }),
      })
      setMessages((prev) => [...prev, res])
    } catch (err) {
      alert('RAG Chat error: ' + err.message)
    } finally {
      setIsSending(false)
    }
  }

  async function handlePdfUpload(paperId, file) {
    if (!file) return
    setUploadingPaperId(paperId)
    try {
      if (isDemoMode) {
        alert(`[Demo Mode] Đã upload & lập chỉ mục pgvector cho file "${file.name}".`)
        return
      }
      const formData = new FormData()
      formData.append('file', file)
      const res = await apiRequest(`/projects/${projectId}/papers/${paperId}/upload-pdf`, {
        method: 'POST',
        body: formData,
      })
      alert(`Đã upload PDF & lập chỉ mục ${res.chunks_indexed} chunks (${res.pages_processed} trang)!`)
      onReloadPapers?.()
    } catch (err) {
      alert('Upload PDF failed: ' + err.message)
    } finally {
      setUploadingPaperId(null)
    }
  }

  async function handleInspectCitation(cit) {
    setActiveCitation(cit)
    setIsLoadingHighlight(true)
    setHighlightData(null)
    try {
      if (isDemoMode) {
        await new Promise((res) => setTimeout(res, 300))
        setHighlightData({
          page: cit.page_number || 1,
          total_pages: 6,
          boxes: [{ x: 0.1, y: 0.34, width: 0.78, height: 0.08 }],
          page_image_base64: null,
          demo_excerpt: cit.excerpt,
        })
        return
      }
      const params = new URLSearchParams({
        page: String(cit.page_number || 1),
        quote: cit.excerpt || '',
      })
      const data = await apiRequest(
        `/projects/${projectId}/papers/${cit.paper_id}/pdf-highlight?${params.toString()}`
      )
      setHighlightData(data)
    } catch (err) {
      setHighlightData({
        page: cit.page_number || 1,
        boxes: [],
        page_image_base64: null,
        error: err.message,
      })
    } finally {
      setIsLoadingHighlight(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 backdrop-blur flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-indigo-400 font-semibold text-sm">
            <MessageSquare className="h-4 w-4" />
            <span>pgvector Hybrid RAG Workspace &bull; RAG Guardrail Auditor &amp; Visual PDF Highlighter</span>
          </div>
          <p className="text-xs text-slate-300 mt-1 max-w-2xl leading-relaxed">
            Upload PDF toàn văn để tìm kiếm lai (Vector + Lexical RRF) cô lập theo dự án, tự động kiểm tra
            ảo giác (Faithfulness Score) và bấm vào trích dẫn <code className="text-indigo-300">[1]</code> để
            mở trang PDF kèm vùng tô sáng gốc.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Sources + Guarded RAG Chat */}
        <div className="lg:col-span-7 space-y-4">
          {/* Paper Scope & PDF Uploader */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4 space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-semibold text-white uppercase tracking-wider">
                Nguồn Tài Liệu Phạm Vi Chat ({selectedPaperIds.length || 'Tất cả'} bài)
              </h4>
              {selectedPaperIds.length > 0 && (
                <button
                  onClick={() => setSelectedPaperIds([])}
                  className="text-[11px] text-indigo-400 hover:underline"
                >
                  Chọn tất cả
                </button>
              )}
            </div>
            <div className="max-h-40 overflow-y-auto space-y-1.5 pr-1">
              {selectablePapers.map((p) => (
                <div
                  key={p.id}
                  className="flex items-center justify-between gap-2 rounded-lg border border-slate-800 bg-slate-950/70 px-3 py-2 text-xs"
                >
                  <label className="flex items-center gap-2 cursor-pointer flex-1 min-w-0">
                    <input
                      type="checkbox"
                      checked={selectedPaperIds.includes(p.id)}
                      onChange={() => togglePaper(p.id)}
                      className="rounded border-slate-700 bg-slate-900 text-indigo-600 focus:ring-0"
                    />
                    <span className="truncate text-slate-200">{p.title}</span>
                  </label>
                  <label className="shrink-0 cursor-pointer inline-flex items-center gap-1 rounded border border-indigo-500/40 bg-indigo-600/10 px-2 py-0.5 text-[10px] font-semibold text-indigo-300 hover:bg-indigo-600/20">
                    <Upload className="h-3 w-3" />
                    {uploadingPaperId === p.id ? 'Đang nạp...' : 'Upload PDF'}
                    <input
                      type="file"
                      accept="application/pdf,.pdf"
                      className="hidden"
                      onChange={(e) => handlePdfUpload(p.id, e.target.files?.[0])}
                    />
                  </label>
                </div>
              ))}
            </div>
          </div>

          {/* Chat Thread */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4 flex flex-col h-[480px]">
            <div className="flex-1 overflow-y-auto space-y-4 pr-1">
              {messages.length === 0 ? (
                <div className="py-16 text-center text-xs text-slate-500">
                  Hãy đặt câu hỏi học thuật về các bài báo đã chọn để nhận câu trả lời có trích dẫn kiểm chứng.
                </div>
              ) : (
                messages.map((msg, idx) => (
                  <div
                    key={msg.id || idx}
                    className={`rounded-xl p-4 text-xs space-y-2.5 ${
                      msg.role === 'user'
                        ? 'bg-indigo-600/20 border border-indigo-500/30 ml-8 text-indigo-100'
                        : 'bg-slate-950/80 border border-slate-800 mr-4 text-slate-200'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-bold uppercase text-[10px] tracking-wider text-slate-400">
                        {msg.role === 'user' ? 'Nhà nghiên cứu' : 'LitNexus RAG Scholar'}
                      </span>
                      {msg.role === 'assistant' && msg.guardrail?.safety_verdict && (
                        <span
                          className={`inline-flex items-center gap-1 rounded px-2 py-0.5 text-[10px] font-bold border ${
                            msg.guardrail.is_safe
                              ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
                              : 'bg-rose-500/15 text-rose-300 border-rose-500/30'
                          }`}
                        >
                          <ShieldCheck className="h-3 w-3" />
                          Faithfulness: {Math.round((msg.guardrail.faithfulness_score || 0) * 100)}%
                        </span>
                      )}
                    </div>

                    <div className="leading-relaxed whitespace-pre-wrap">{msg.content}</div>

                    {msg.citations && msg.citations.length > 0 && (
                      <div className="pt-2 border-t border-slate-800/80 flex flex-wrap gap-1.5">
                        {msg.citations.map((cit) => (
                          <button
                            key={cit.index}
                            type="button"
                            onClick={() => handleInspectCitation(cit)}
                            className={`inline-flex items-center gap-1 rounded px-2 py-0.5 text-[11px] font-medium border transition ${
                              activeCitation?.index === cit.index
                                ? 'bg-amber-500/20 border-amber-400 text-amber-200'
                                : 'bg-slate-900 border-slate-700 text-indigo-300 hover:border-indigo-500/50'
                            }`}
                          >
                            <FileText className="h-3 w-3" />
                            [{cit.index}] Trang p.{cit.page_number}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>

            <form onSubmit={handleSendChat} className="pt-3 mt-3 border-t border-slate-800 flex gap-2">
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Đặt câu hỏi dựa trên tài liệu PDF của dự án..."
                className="flex-1 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white focus:border-indigo-500 focus:outline-none"
              />
              <button
                type="submit"
                disabled={isSending}
                className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-500 transition disabled:opacity-50"
              >
                <Send className="h-3.5 w-3.5" />
                {isSending ? 'Đang hỏi...' : 'Gửi'}
              </button>
            </form>
          </div>
        </div>

        {/* Right: PDF Evidence Verification & Bounding-Box Highlighter Panel */}
        <div className="lg:col-span-5">
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 space-y-4 h-full">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-semibold text-white flex items-center gap-2">
                <FileText className="h-4 w-4 text-amber-400" />
                Bảng Xác Minh Bằng Chứng PDF (Visual Highlighter)
              </h4>
              {activeCitation && (
                <span className="text-[11px] text-amber-300 font-semibold">
                  Trích dẫn [{activeCitation.index}] &bull; Trang {activeCitation.page_number}
                </span>
              )}
            </div>

            {!activeCitation ? (
              <div className="py-24 text-center text-xs text-slate-500">
                Bấm vào thẻ trích dẫn <code className="text-indigo-300">[1] Trang p.X</code> ở khung chat
                để mở trang PDF và tô sáng câu trích dẫn nguyên văn.
              </div>
            ) : isLoadingHighlight ? (
              <div className="py-24 text-center text-xs text-slate-400">Đang định vị tọa độ PDF...</div>
            ) : (
              <div className="space-y-3 text-xs">
                <div className="rounded-lg bg-slate-950 border border-slate-800 p-3 space-y-1">
                  <div className="font-semibold text-white">{activeCitation.paper_title}</div>
                  <div className="italic text-amber-200/90">&ldquo;{activeCitation.excerpt}&rdquo;</div>
                </div>

                {highlightData?.page_image_base64 ? (
                  <div className="relative rounded-lg overflow-hidden border border-slate-700 bg-white">
                    <img
                      src={`data:image/png;base64,${highlightData.page_image_base64}`}
                      alt={`PDF Page ${highlightData.page}`}
                      className="w-full h-auto block"
                    />
                    {highlightData.boxes?.map((box, bIdx) => (
                      <div
                        key={bIdx}
                        style={{
                          left: `${box.x * 100}%`,
                          top: `${box.y * 100}%`,
                          width: `${box.width * 100}%`,
                          height: `${box.height * 100}%`,
                        }}
                        className="absolute bg-amber-400/35 border border-amber-500 rounded-sm pointer-events-none"
                      />
                    ))}
                  </div>
                ) : (
                  <div className="rounded-lg border border-slate-800 bg-slate-950 p-4 space-y-2 text-slate-300">
                    <div className="text-[11px] font-semibold text-indigo-300">
                      Bằng chứng định vị ({highlightData?.boxes?.length || 0} vùng khớp trên trang {highlightData?.page}):
                    </div>
                    <p className="italic leading-relaxed text-amber-100/90">
                      &ldquo;{highlightData?.demo_excerpt || activeCitation.excerpt}&rdquo;
                    </p>
                    {highlightData?.error && (
                      <p className="text-[11px] text-amber-400">Lưu ý: {highlightData.error}</p>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
