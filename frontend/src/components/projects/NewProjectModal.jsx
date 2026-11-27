export default function NewProjectModal({
  isOpen,
  newProject,
  setNewProject,
  onClose,
  onSubmit,
}) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
        <h3 className="text-lg font-bold text-white mb-2">Tạo Dự án SLR Mới theo PICO</h3>
        <p className="text-xs text-slate-400 mb-4">
          Xác lập mục tiêu nghiên cứu và tiêu chuẩn chọn/loại khắt khe trước khi tìm kiếm.
        </p>

        <form onSubmit={onSubmit} className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Tiêu đề Dự án</label>
            <input
              type="text"
              required
              value={newProject.title}
              onChange={(e) => setNewProject({ ...newProject, title: e.target.value })}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white focus:border-indigo-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Lĩnh vực (Domain)</label>
            <input
              type="text"
              required
              value={newProject.domain}
              onChange={(e) => setNewProject({ ...newProject, domain: e.target.value })}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white focus:border-indigo-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Câu hỏi nghiên cứu (Research Question)
            </label>
            <textarea
              rows={2}
              required
              value={newProject.research_question}
              onChange={(e) => setNewProject({ ...newProject, research_question: e.target.value })}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white focus:border-indigo-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-emerald-400 mb-1">
              Tiêu chuẩn Chọn (Inclusion Criteria - cách nhau bằng dấu phẩy)
            </label>
            <input
              type="text"
              value={newProject.inclusion_criteria}
              onChange={(e) => setNewProject({ ...newProject, inclusion_criteria: e.target.value })}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white focus:border-indigo-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-rose-400 mb-1">
              Tiêu chuẩn Loại (Exclusion Criteria - cách nhau bằng dấu phẩy)
            </label>
            <input
              type="text"
              value={newProject.exclusion_criteria}
              onChange={(e) => setNewProject({ ...newProject, exclusion_criteria: e.target.value })}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white focus:border-indigo-500 focus:outline-none"
            />
          </div>

          <div className="flex justify-end gap-2 pt-3">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-slate-700 px-4 py-2 text-xs font-medium text-slate-300 hover:bg-slate-800"
            >
              Hủy
            </button>
            <button
              type="submit"
              className="rounded-lg bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-500"
            >
              Tạo Project
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
