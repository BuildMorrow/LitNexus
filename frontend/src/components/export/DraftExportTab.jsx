import { Copy, FileDown } from 'lucide-react'

export default function DraftExportTab({
  draftReport,
  isGeneratingDraft,
  draftFormat,
  setDraftFormat,
  onDownloadDraftFile,
}) {
  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 backdrop-blur flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-cyan-400 font-semibold text-sm">
            <FileDown className="h-4 w-4" />
            <span>Xuất Bản Thảo Bài Báo Đầu Tiên (First Draft Manuscript) &amp; Trích Dẫn BibTeX Chuẩn PRISMA</span>
          </div>
          <p className="text-xs text-slate-300 mt-1 max-w-2xl leading-relaxed">
            Tự động kết hợp dữ liệu từ phễu sàng lọc Active Learning, ma trận bằng chứng không bịa nguồn,
            đối thoại tranh biện đa agent và trích dẫn BibTeX chuẩn xác để ra ngay bản dự thảo đầu tiên.
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
            Tải File {draftFormat.toUpperCase()}
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
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 space-y-3">
            <h4 className="text-sm font-semibold text-white">Sơ đồ Dòng Chảy PRISMA 2020 (Flow Summary)</h4>
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
