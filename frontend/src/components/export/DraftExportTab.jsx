import { Copy, FileDown, FileSpreadsheet } from 'lucide-react'
import { apiDownloadBlob } from '../../services/api'

export default function DraftExportTab({
  projectId,
  isDemoMode,
  draftReport,
  isGeneratingDraft,
  draftFormat,
  setDraftFormat,
  onDownloadDraftFile,
}) {
  async function handleDownloadExcel() {
    if (isDemoMode) {
      alert('[Demo Mode] Sẵn sàng tải workbook 3 sheets UTF-8 (.xlsx) từ backend PostgreSQL.')
      return
    }
    try {
      const blob = await apiDownloadBlob(`/projects/${projectId}/conflicts/export-xlsx`)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'litnexus_slr_report.xlsx'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (err) {
      alert('Excel export failed: ' + err.message)
    }
  }

  function handleDownloadSvg() {
    if (!draftReport?.prisma_svg) return
    const blob = new Blob([draftReport.prisma_svg], { type: 'image/svg+xml' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'prisma_2020_flow.svg'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 backdrop-blur flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-cyan-400 font-semibold text-sm">
            <FileDown className="h-4 w-4" />
            <span>Xuất Bản Thảo PRISMA 2020 &bull; Sơ đồ SVG &bull; Excel UTF-8</span>
          </div>
          <p className="text-xs text-slate-300 mt-1 max-w-2xl leading-relaxed">
            Xuất trực tiếp bản thảo 4 định dạng học thuật (.md, .tex, .qmd, .bib), sơ đồ dòng chảy PRISMA 2020 SVG
            chuẩn xuất bản và bảng tính Excel 3-sheet tiếng Việt chuẩn xác.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="flex rounded-lg bg-slate-950 p-1 border border-slate-800">
            {[
              { id: 'md', label: 'Markdown (.md)' },
              { id: 'tex', label: 'LaTeX (.tex)' },
              { id: 'qmd', label: 'Quarto (.qmd)' },
              { id: 'bib', label: 'BibTeX (.bib)' },
            ].map((fmt) => (
              <button
                key={fmt.id}
                onClick={() => setDraftFormat(fmt.id)}
                className={`px-2.5 py-1 text-xs font-semibold rounded-md transition ${
                  draftFormat === fmt.id ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
              >
                {fmt.label}
              </button>
            ))}
          </div>

          <button
            onClick={() => {
              let text = draftReport?.draft_markdown
              if (draftFormat === 'tex') text = draftReport?.latex_content
              else if (draftFormat === 'qmd') text = draftReport?.quarto_content
              else if (draftFormat === 'bib') text = draftReport?.bibtex_content
              if (text) {
                navigator.clipboard.writeText(text)
                alert(`Đã sao chép nội dung ${draftFormat.toUpperCase()} vào Clipboard!`)
              }
            }}
            disabled={!draftReport}
            className="flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs text-slate-200 hover:bg-slate-700 transition disabled:opacity-50"
          >
            <Copy className="h-4 w-4" />
            Copy
          </button>

          <button
            onClick={() => onDownloadDraftFile(draftFormat)}
            disabled={!draftReport}
            className="flex items-center gap-1.5 rounded-lg border border-cyan-500/40 bg-cyan-600/20 px-3 py-1.5 text-xs font-semibold text-cyan-300 hover:bg-cyan-600/30 transition disabled:opacity-50"
          >
            <FileDown className="h-4 w-4" />
            Tải {draftFormat.toUpperCase()}
          </button>

          <button
            onClick={handleDownloadExcel}
            className="flex items-center gap-1.5 rounded-lg border border-emerald-500/40 bg-emerald-600/20 px-3 py-1.5 text-xs font-semibold text-emerald-300 hover:bg-emerald-600/30 transition"
          >
            <FileSpreadsheet className="h-4 w-4" />
            Xuất Excel (.xlsx)
          </button>
        </div>
      </div>

      {isGeneratingDraft ? (
        <div className="py-12 text-center text-xs text-slate-500">Đang tổng hợp bản thảo bài báo...</div>
      ) : !draftReport ? (
        <div className="rounded-xl border border-slate-800 bg-slate-900/30 p-12 text-center text-xs text-slate-500">
          Chưa có bản thảo bài báo. Hãy đảm bảo project có bài báo và thử lại.
        </div>
      ) : (
        <div className="space-y-6">
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-semibold text-white">Sơ đồ Dòng Chảy PRISMA 2020 (SVG Vector)</h4>
              {draftReport.prisma_svg && (
                <button
                  onClick={handleDownloadSvg}
                  className="inline-flex items-center gap-1 rounded border border-indigo-500/40 bg-indigo-600/15 px-3 py-1 text-xs font-semibold text-indigo-300 hover:bg-indigo-600/25 transition"
                >
                  <FileDown className="h-3.5 w-3.5" />
                  Tải sơ đồ (.svg)
                </button>
              )}
            </div>

            {draftReport.prisma_svg ? (
              <div
                className="max-w-2xl mx-auto rounded-lg overflow-hidden border border-slate-800"
                dangerouslySetInnerHTML={{ __html: draftReport.prisma_svg }}
              />
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                <div className="rounded-lg bg-slate-950 p-3 border border-slate-800">
                  <div className="text-[11px] text-slate-400">1. Identified</div>
                  <div className="text-lg font-bold text-white mt-1">{draftReport.prisma_flow_summary.identified}</div>
                </div>
                <div className="rounded-lg bg-slate-950 p-3 border border-slate-800">
                  <div className="text-[11px] text-slate-400">2. Screened</div>
                  <div className="text-lg font-bold text-white mt-1">{draftReport.prisma_flow_summary.screened}</div>
                </div>
                <div className="rounded-lg bg-slate-950 p-3 border border-slate-800">
                  <div className="text-[11px] text-rose-400">3. Excluded</div>
                  <div className="text-lg font-bold text-rose-300 mt-1">{draftReport.prisma_flow_summary.excluded}</div>
                </div>
                <div className="rounded-lg bg-slate-950 p-3 border border-emerald-900/40">
                  <div className="text-[11px] text-emerald-400">4. Included Core Studies</div>
                  <div className="text-lg font-bold text-emerald-300 mt-1">{draftReport.prisma_flow_summary.included}</div>
                </div>
              </div>
            )}
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-semibold text-white">
                {draftFormat === 'md' && 'Nội Dung Bản Dự Thảo Đầu Tiên (DRAFT_PAPER.md)'}
                {draftFormat === 'tex' && 'Mã Nguồn LaTeX Bài Báo Khoa Học (paper_slr.tex)'}
                {draftFormat === 'qmd' && 'Bản Báo Cáo Nghiên Cứu Đa Định Dạng Quarto (review_report.qmd)'}
                {draftFormat === 'bib' && 'Trích Dẫn Học Thuật Chuẩn Hóa (references.bib)'}
              </h4>
              <span className="text-[11px] text-slate-400 font-mono">
                {draftFormat === 'md' && 'Markdown format'}
                {draftFormat === 'tex' && 'LaTeX article class'}
                {draftFormat === 'qmd' && 'Quarto reproducible document'}
                {draftFormat === 'bib' && 'BibTeX bibliography'}
              </span>
            </div>
            <pre className="overflow-x-auto rounded-lg border border-slate-800 bg-slate-950 p-5 font-mono text-xs text-slate-200 leading-relaxed whitespace-pre-wrap max-h-[600px]">
              {draftFormat === 'md' && draftReport.draft_markdown}
              {draftFormat === 'tex' && (draftReport.latex_content || 'Chưa có bản xuất LaTeX.')}
              {draftFormat === 'qmd' && (draftReport.quarto_content || 'Chưa có bản xuất Quarto.')}
              {draftFormat === 'bib' && draftReport.bibtex_content}
            </pre>
          </div>
        </div>
      )}
    </div>
  )
}
