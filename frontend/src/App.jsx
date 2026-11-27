import { useEffect, useState } from 'react'
import { BarChart3, FileDown, FileSpreadsheet, Filter, MessageSquare, Network, Plus, Wand2 } from 'lucide-react'
import { apiRequest } from './services/api'
import AuthScreen from './components/auth/AuthScreen'
import Header from './components/layout/Header'
import KpiDashboard from './components/layout/KpiDashboard'
import NewProjectModal from './components/projects/NewProjectModal'
import ResearchSetupTab from './components/setup/ResearchSetupTab'
import ScreeningBoardTab from './components/screening/ScreeningBoardTab'
import EvidenceMatrixTab from './components/matrix/EvidenceMatrixTab'
import DataAnalysisTab from './components/analysis/DataAnalysisTab'
import ConflictGraphTab from './components/conflicts/ConflictGraphTab'
import DraftExportTab from './components/export/DraftExportTab'
import WorkspaceRagTab from './components/workspace/WorkspaceRagTab'
import {
  DEMO_ANALYSIS_RESULT,
  DEMO_DATASET,
  DEMO_DRAFT_REPORT,
  DEMO_GRAPH_DATA,
  DEMO_KPI_METRICS,
  DEMO_MATRIX_DATA,
  DEMO_PAPERS,
  DEMO_PROJECT,
  DEMO_QUALITY_GATE,
  DEMO_SEARCH_HISTORY,
  DEMO_WORKSPACE_MESSAGES,
} from './data/demoData'

const DEMO_TOKEN = 'mock-demo-token-for-prototype'

export default function App() {
  const [apiStatus, setApiStatus] = useState('checking')
  const [token, setToken] = useState(() => localStorage.getItem('litnexus_token'))
  const [activeTab, setActiveTab] = useState('screening')
  const isDemoMode = token === DEMO_TOKEN

  // Auth state
  const [authEmail, setAuthEmail] = useState('researcher@univ.edu')
  const [authPassword, setAuthPassword] = useState('secret123')
  const [authName, setAuthName] = useState('Dr. Alex Research')
  const [isRegister, setIsRegister] = useState(false)
  const [authError, setAuthError] = useState('')

  // Project state
  const [projects, setProjects] = useState([])
  const [selectedProjectId, setSelectedProjectId] = useState(null)
  const [showNewProjectModal, setShowNewProjectModal] = useState(false)
  const [newProject, setNewProject] = useState({
    title: 'Arrhythmia Detection on Wearable ECG',
    domain: 'Biomedical AI',
    research_question: 'How do lightweight 1D CNNs perform on wearable single-lead ECG compared to 2D models?',
    inclusion_criteria: 'Uses 1D CNN, Evaluates on single-lead wearable ECG, Quantitative F1 or accuracy reported',
    exclusion_criteria: 'Animal studies, Non-wearable multi-lead ECG, Pure review papers without benchmark',
  })

  // Papers, Search History & Snowballing
  const [papers, setPapers] = useState([])
  const [searchHistory, setSearchHistory] = useState([])
  const [searchQuery, setSearchQuery] = useState('wearable ECG 1D CNN arrhythmia')
  const [searchLimit, setSearchLimit] = useState(25)
  const [isSearching, setIsSearching] = useState(false)
  const [isSnowballing, setIsSnowballing] = useState(false)
  const [yearFrom, setYearFrom] = useState('')
  const [yearTo, setYearTo] = useState('')
  const [openAccessOnly, setOpenAccessOnly] = useState(false)

  // Active Learning, Dual-Peer & LLM Batch
  const [isRunningAL, setIsRunningAL] = useState(false)
  const [isRunningLLM, setIsRunningLLM] = useState(false)
  const [isRunningDualPeer, setIsRunningDualPeer] = useState(false)
  const [qualityGate, setQualityGate] = useState(null)

  // KPI Metrics & Comparative Matrix
  const [kpiMetrics, setKpiMetrics] = useState(null)
  const [matrixData, setMatrixData] = useState([])
  const [isLoadingMatrix, setIsLoadingMatrix] = useState(false)
  const [ingestingPaperId, setIngestingPaperId] = useState(null)

  // Data Analysis Assistant State (Pillar 2)
  const [datasets, setDatasets] = useState([])
  const [selectedDatasetId, setSelectedDatasetId] = useState(null)
  const [csvInput, setCsvInput] = useState(`patient_id,age,wearable_snr,heart_rate,f1_score,noise_level
p_01,45,18.5,72,0.98,low
p_02,52,14.2,85,0.94,medium
p_03,61,9.8,68,0.86,high
p_04,39,21.0,76,0.99,low
p_05,71,8.5,92,0.81,high
p_06,58,16.0,80,0.95,medium
p_07,64,11.2,74,0.89,medium
p_08,49,19.3,69,0.97,low`)
  const [datasetName, setDatasetName] = useState('Wearable_Cohort_Pilot_N8.csv')
  const [analysisGoal, setAnalysisGoal] = useState(
    'Compare F1 score across low vs high noise levels and evaluate sample power'
  )
  const [analysisResult, setAnalysisResult] = useState(null)
  const [isProfiling, setIsProfiling] = useState(false)
  const [isAdvising, setIsAdvising] = useState(false)

  // Conflict Discovery & Graph State
  const [graphData, setGraphData] = useState({ nodes: [], edges: [], research_gaps: [] })
  const [isLoadingGraph, setIsLoadingGraph] = useState(false)
  const [isAnalyzingConflicts, setIsAnalyzingConflicts] = useState(false)

  // First Draft Export State
  const [draftReport, setDraftReport] = useState(null)
  const [isGeneratingDraft, setIsGeneratingDraft] = useState(false)
  const [draftFormat, setDraftFormat] = useState('md')

  // Workspace RAG Chat State
  const [workspaceMessages, setWorkspaceMessages] = useState([])

  const activeProject = projects.find((p) => p.id === selectedProjectId) || null

  useEffect(() => {
    apiRequest('/health')
      .then(() => setApiStatus('online'))
      .catch(() => setApiStatus('offline'))
  }, [])

  useEffect(() => {
    if (token && !isDemoMode) loadProjects()
  }, [token, isDemoMode])

  useEffect(() => {
    if (selectedProjectId && !isDemoMode) {
      loadProjectPapers(selectedProjectId)
      loadSearchHistory(selectedProjectId)
      loadQualityGate(selectedProjectId)
      loadKpiMetrics(selectedProjectId)
      if (activeTab === 'matrix') loadComparativeMatrix(selectedProjectId)
      else if (activeTab === 'analysis') loadProjectDatasets(selectedProjectId)
      else if (activeTab === 'conflicts') loadConflictGraph(selectedProjectId)
      else if (activeTab === 'draft') loadDraftReport(selectedProjectId)
      else if (activeTab === 'workspace') loadWorkspaceMessages(selectedProjectId)
    }
  }, [selectedProjectId, activeTab, isDemoMode])

  async function handleAuth(e) {
    e.preventDefault()
    setAuthError('')
    try {
      const endpoint = isRegister ? '/auth/register' : '/auth/login'
      const payload = isRegister
        ? { email: authEmail, password: authPassword, full_name: authName }
        : { email: authEmail, password: authPassword }

      const res = await apiRequest(endpoint, { method: 'POST', body: JSON.stringify(payload) })
      localStorage.setItem('litnexus_token', res.access_token)
      setToken(res.access_token)
    } catch (err) {
      setAuthError(err.message || 'Authentication failed')
    }
  }

  function handleLogout() {
    localStorage.removeItem('litnexus_token')
    setToken(null)
    setProjects([])
    setSelectedProjectId(null)
    setPapers([])
    setSearchHistory([])
    setKpiMetrics(null)
  }

  function loadPrototypeDemo() {
    localStorage.setItem('litnexus_token', DEMO_TOKEN)
    setToken(DEMO_TOKEN)
    setProjects([DEMO_PROJECT])
    setSelectedProjectId(DEMO_PROJECT.id)
    setKpiMetrics(DEMO_KPI_METRICS)
    setQualityGate(DEMO_QUALITY_GATE)
    setPapers(DEMO_PAPERS)
    setSearchHistory(DEMO_SEARCH_HISTORY)
    setMatrixData(DEMO_MATRIX_DATA)
    setDatasets([DEMO_DATASET])
    setSelectedDatasetId(DEMO_DATASET.id)
    setAnalysisResult(DEMO_ANALYSIS_RESULT)
    setGraphData(DEMO_GRAPH_DATA)
    setDraftReport(DEMO_DRAFT_REPORT)
    setWorkspaceMessages(DEMO_WORKSPACE_MESSAGES)
  }

  async function loadProjects() {
    try {
      const list = await apiRequest('/projects')
      setProjects(list)
      if (list.length > 0 && !selectedProjectId) setSelectedProjectId(list[0].id)
    } catch (err) {
      console.error(err)
    }
  }

  async function createProject(e) {
    e.preventDefault()
    try {
      const payload = {
        title: newProject.title,
        domain: newProject.domain,
        research_question: newProject.research_question,
        inclusion_criteria: newProject.inclusion_criteria.split(',').map((s) => s.trim()).filter(Boolean),
        exclusion_criteria: newProject.exclusion_criteria.split(',').map((s) => s.trim()).filter(Boolean),
      }
      const created = await apiRequest('/projects', { method: 'POST', body: JSON.stringify(payload) })
      setProjects([created, ...projects])
      setSelectedProjectId(created.id)
      setShowNewProjectModal(false)
    } catch (err) {
      alert('Failed to create project: ' + err.message)
    }
  }

  async function loadProjectPapers(pId) {
    try {
      setPapers(await apiRequest(`/projects/${pId}/papers`))
    } catch (err) {
      console.error(err)
    }
  }

  async function loadSearchHistory(pId) {
    try {
      setSearchHistory(await apiRequest(`/projects/${pId}/search/history`))
    } catch (err) {
      console.error(err)
    }
  }

  async function loadQualityGate(pId) {
    try {
      setQualityGate(await apiRequest(`/projects/${pId}/screening/quality-gate`))
    } catch (err) {
      console.error(err)
    }
  }

  async function loadKpiMetrics(pId) {
    try {
      setKpiMetrics(await apiRequest(`/projects/${pId}/conflicts/kpi-metrics`))
    } catch (err) {
      console.error(err)
    }
  }

  async function loadComparativeMatrix(pId) {
    setIsLoadingMatrix(true)
    try {
      const data = await apiRequest(`/projects/${pId}/conflicts/comparative-matrix`)
      setMatrixData(data.items || [])
    } catch (err) {
      console.error(err)
    } finally {
      setIsLoadingMatrix(false)
    }
  }

  async function loadProjectDatasets(pId) {
    try {
      const list = await apiRequest(`/projects/${pId}/analysis/datasets`)
      setDatasets(list)
      if (list.length > 0 && !selectedDatasetId) setSelectedDatasetId(list[0].id)
    } catch (err) {
      console.error(err)
    }
  }

  async function loadConflictGraph(pId) {
    setIsLoadingGraph(true)
    try {
      setGraphData(await apiRequest(`/projects/${pId}/conflicts/graph`))
    } catch (err) {
      console.error(err)
    } finally {
      setIsLoadingGraph(false)
    }
  }

  async function handleRunConflictAnalysis() {
    if (!selectedProjectId) return
    setIsAnalyzingConflicts(true)
    try {
      await apiRequest(`/projects/${selectedProjectId}/conflicts/analyze`, { method: 'POST' })
      alert('Đã hoàn thành 3-Agent Conflict Discovery: Bóc tách claims, đối chiếu tranh biện và tổng hợp Research Gaps!')
      await loadConflictGraph(selectedProjectId)
      await loadComparativeMatrix(selectedProjectId)
    } catch (err) {
      alert('Conflict Analysis failed: ' + err.message)
    } finally {
      setIsAnalyzingConflicts(false)
    }
  }

  async function loadWorkspaceMessages(pId) {
    try {
      setWorkspaceMessages(await apiRequest(`/projects/${pId}/workspace/messages`))
    } catch (err) {
      console.error(err)
    }
  }

  async function loadDraftReport(pId) {
    setIsGeneratingDraft(true)
    try {
      setDraftReport(await apiRequest(`/projects/${pId}/conflicts/export-draft`))
    } catch (err) {
      console.error(err)
    } finally {
      setIsGeneratingDraft(false)
    }
  }

  function downloadDraftFile(format) {
    if (!draftReport) return
    const map = {
      md: { content: draftReport.draft_markdown, filename: 'DRAFT_PAPER.md', type: 'text/markdown' },
      tex: { content: draftReport.latex_content || '', filename: 'paper_slr.tex', type: 'application/x-tex' },
      qmd: { content: draftReport.quarto_content || '', filename: 'review_report.qmd', type: 'text/plain' },
      bib: { content: draftReport.bibtex_content || '', filename: 'references.bib', type: 'application/x-bibtex' },
    }
    const target = map[format] || map.md
    const blob = new Blob([target.content], { type: target.type })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = target.filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  async function handleUploadDataset(e) {
    e.preventDefault()
    if (!selectedProjectId) return
    setIsProfiling(true)
    try {
      const res = await apiRequest(`/projects/${selectedProjectId}/analysis/datasets`, {
        method: 'POST',
        body: JSON.stringify({ dataset_name: datasetName, csv_raw_text: csvInput }),
      })
      setDatasets([res, ...datasets])
      setSelectedDatasetId(res.id)
      alert(`Đã nạp và profile thành công dataset: ${res.dataset_name} (${res.row_count} dòng, ${res.column_count} cột)`)
    } catch (err) {
      alert('Upload dataset failed: ' + err.message)
    } finally {
      setIsProfiling(false)
    }
  }

  async function handleGetAnalysisAdvice(e) {
    e.preventDefault()
    if (!selectedProjectId || !selectedDatasetId) {
      alert('Vui lòng chọn hoặc nạp một dataset trước khi phân tích.')
      return
    }
    setIsAdvising(true)
    try {
      const res = await apiRequest(`/projects/${selectedProjectId}/analysis/datasets/${selectedDatasetId}/advise`, {
        method: 'POST',
        body: JSON.stringify({ analysis_goal: analysisGoal }),
      })
      setAnalysisResult(res)
    } catch (err) {
      alert('Analysis advise failed: ' + err.message)
    } finally {
      setIsAdvising(false)
    }
  }

  async function handleSearch(e) {
    e.preventDefault()
    if (!selectedProjectId) return
    setIsSearching(true)
    try {
      await apiRequest(`/projects/${selectedProjectId}/search`, {
        method: 'POST',
        body: JSON.stringify({
          query: searchQuery,
          limit: Number(searchLimit),
          year_from: yearFrom ? Number(yearFrom) : null,
          year_to: yearTo ? Number(yearTo) : null,
          open_access_only: openAccessOnly,
        }),
      })
      await loadProjectPapers(selectedProjectId)
      await loadSearchHistory(selectedProjectId)
      await loadKpiMetrics(selectedProjectId)
    } catch (err) {
      alert('Search failed: ' + err.message)
    } finally {
      setIsSearching(false)
    }
  }

  async function handleSnowball() {
    const seedIds = papers.filter((p) => p.screening_status === 'included').map((p) => p.id)
    if (seedIds.length === 0) return
    setIsSnowballing(true)
    try {
      if (isDemoMode) {
        await new Promise((res) => setTimeout(res, 600))
        setPapers((prev) => [
          {
            id: `sb-${Date.now()}`,
            title: 'Noise-Robust Single-Lead Wearable Arrhythmia Benchmark (Snowball Discovery)',
            authors: ['Tran, Minh', 'Pham, Lan'],
            journal: 'Biomedical Signal Processing and Control',
            year: 2025,
            scopus_quartile: 'Q1',
            discovery_source: 'forward_snowball',
            seed_distance: 1,
            screening_status: 'uncertain',
            screening_source: 'none',
            al_inclusion_prob: 0.64,
            al_uncertainty_score: 0.72,
            abstract: 'Follow-up study citing single-lead 1D CNN patches under ambulatory motion artifacts.',
          },
          ...prev,
        ])
        return
      }
      const res = await apiRequest(`/projects/${selectedProjectId}/search/snowball`, {
        method: 'POST',
        body: JSON.stringify({ seed_paper_ids: seedIds.slice(0, 5), limit_per_direction: 15, distance: 1 }),
      })
      alert(
        `Snowball 2 chiều hoàn tất! Tìm thêm ${res.added_count} bài mới (Backward: ${res.backward_count}, Forward: ${res.forward_count}).`
      )
      await loadProjectPapers(selectedProjectId)
      await loadSearchHistory(selectedProjectId)
      await loadKpiMetrics(selectedProjectId)
    } catch (err) {
      alert('Snowball failed: ' + err.message)
    } finally {
      setIsSnowballing(false)
    }
  }

  async function handleLabelPaper(paperId, status) {
    if (isDemoMode) {
      setPapers((prev) =>
        prev.map((p) => (p.id === paperId ? { ...p, screening_status: status, screening_source: 'human' } : p))
      )
      return
    }
    try {
      await apiRequest(`/projects/${selectedProjectId}/screening/papers/${paperId}/label`, {
        method: 'PATCH',
        body: JSON.stringify({ status }),
      })
      setPapers((prev) =>
        prev.map((p) => (p.id === paperId ? { ...p, screening_status: status, screening_source: 'human' } : p))
      )
      loadKpiMetrics(selectedProjectId)
    } catch (err) {
      alert('Failed to label paper: ' + err.message)
    }
  }

  async function handleIngestPdf(paper) {
    if (!paper) return
    let pdfUrl = paper.pdf_url
    if (!pdfUrl) {
      pdfUrl = window.prompt(
        'Nhập URL file PDF trực tuyến (Open Access / arXiv) để trích xuất toàn văn có neo trang:',
        'https://arxiv.org/pdf/2401.00001.pdf'
      )
      if (!pdfUrl) return
    }
    setIngestingPaperId(paper.id)
    try {
      if (isDemoMode) {
        await new Promise((res) => setTimeout(res, 600))
        alert(`[Demo Mode] Đã trích xuất PDF "${paper.title}" thành công!`)
        return
      }
      const res = await apiRequest(`/projects/${selectedProjectId}/papers/${paper.id}/ingest-pdf`, {
        method: 'POST',
        body: JSON.stringify({ pdf_url: pdfUrl }),
      })
      alert(`Đã trích xuất toàn văn PDF thành công!\nSố trang: ${res.pages_processed}\nSố chunks: ${res.chunks_indexed}`)
      loadProjectPapers(selectedProjectId)
    } catch (err) {
      alert('Lỗi nạp PDF: ' + err.message)
    } finally {
      setIngestingPaperId(null)
    }
  }

  async function handleRunActiveLearning() {
    setIsRunningAL(true)
    try {
      await apiRequest(`/projects/${selectedProjectId}/screening/run-active-learning`, { method: 'POST' })
      await loadProjectPapers(selectedProjectId)
      await loadKpiMetrics(selectedProjectId)
    } catch (err) {
      alert('Active Learning failed: ' + err.message)
    } finally {
      setIsRunningAL(false)
    }
  }

  async function handleRunDualPeer() {
    setIsRunningDualPeer(true)
    try {
      if (isDemoMode) {
        await new Promise((res) => setTimeout(res, 600))
        alert('[Demo Mode] Dual-Agent Peer Screening hoàn tất với Grounding Precision = 100%!')
        return
      }
      const res = await apiRequest(`/projects/${selectedProjectId}/screening/dual-peer-screen`, {
        method: 'POST',
        body: JSON.stringify({ limit: 8 }),
      })
      setQualityGate(res.quality_gate)
      alert(
        `Phản biện mù đôi hoàn tất ${res.processed_count} bài! Bất đồng cần trọng tài: ${res.disagreement_count}. Grounding trung bình: ${(
          res.avg_grounding_score * 100
        ).toFixed(0)}%`
      )
      await loadProjectPapers(selectedProjectId)
      await loadKpiMetrics(selectedProjectId)
    } catch (err) {
      alert('Dual-Peer screen failed: ' + err.message)
    } finally {
      setIsRunningDualPeer(false)
    }
  }

  async function handleHitlApprove(paperId) {
    if (isDemoMode) {
      setPapers((prev) =>
        prev.map((p) =>
          p.id === paperId
            ? { ...p, screening_rationale: { ...(p.screening_rationale || {}), hitl_approved: true } }
            : p
        )
      )
      return
    }
    try {
      const updated = await apiRequest(`/projects/${selectedProjectId}/screening/papers/${paperId}/hitl-override`, {
        method: 'POST',
        body: JSON.stringify({ action: 'approve', note: 'Approved via HITL review' }),
      })
      setPapers((prev) => prev.map((p) => (p.id === paperId ? updated : p)))
      await loadQualityGate(selectedProjectId)
    } catch (err) {
      alert('HITL approval failed: ' + err.message)
    }
  }

  async function handleAutoLabelUncertain() {
    setIsRunningLLM(true)
    try {
      const res = await apiRequest(`/projects/${selectedProjectId}/screening/auto-label-uncertain`, {
        method: 'POST',
        body: JSON.stringify({ limit: 10 }),
      })
      alert(`LLM đã phân loại ${res.processed_count} bài (Included: ${res.auto_included}, Excluded: ${res.auto_excluded}).`)
      await loadProjectPapers(selectedProjectId)
      await loadKpiMetrics(selectedProjectId)
    } catch (err) {
      alert('Auto-label failed: ' + err.message)
    } finally {
      setIsRunningLLM(false)
    }
  }

  const tabs = [
    { id: 'setup', label: '0. Thiết lập Đề tài (AI PICO)', icon: Wand2, iconColor: 'text-cyan-400', accent: 'border-cyan-500 text-cyan-400' },
    { id: 'screening', label: '1. Sàng lọc & Snowball', icon: Filter, accent: 'border-indigo-500 text-indigo-400' },
    { id: 'matrix', label: '2. Ma trận Bằng chứng', icon: FileSpreadsheet, accent: 'border-indigo-500 text-indigo-400' },
    { id: 'analysis', label: '3. Phân tích Dữ liệu', icon: BarChart3, iconColor: 'text-emerald-400', accent: 'border-indigo-500 text-indigo-400' },
    { id: 'conflicts', label: '4. Đồ thị Mâu thuẫn', icon: Network, iconColor: 'text-rose-400', accent: 'border-rose-500 text-rose-400' },
    { id: 'workspace', label: '5. Hỏi đáp PDF & Xác minh (RAG)', icon: MessageSquare, iconColor: 'text-indigo-400', accent: 'border-indigo-500 text-indigo-400' },
    { id: 'draft', label: '6. Xuất Bản thảo PRISMA', icon: FileDown, iconColor: 'text-cyan-400', accent: 'border-indigo-500 text-indigo-400' },
  ]

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans">
      <Header apiStatus={apiStatus} token={token} isDemoMode={isDemoMode} onLogout={handleLogout} />

      {!token ? (
        <AuthScreen
          isRegister={isRegister}
          setIsRegister={setIsRegister}
          authName={authName}
          setAuthName={setAuthName}
          authEmail={authEmail}
          setAuthEmail={setAuthEmail}
          authPassword={authPassword}
          setAuthPassword={setAuthPassword}
          authError={authError}
          onSubmit={handleAuth}
          onEnterDemo={loadPrototypeDemo}
        />
      ) : (
        <main className="mx-auto max-w-7xl px-6 py-6 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-xl border border-slate-800 bg-slate-900/60 p-4 backdrop-blur">
            <div className="flex items-center gap-3">
              <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Project:</span>
              <select
                value={selectedProjectId || ''}
                onChange={(e) => setSelectedProjectId(e.target.value)}
                className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-sm text-white focus:border-indigo-500 focus:outline-none"
              >
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.title}
                  </option>
                ))}
              </select>
            </div>

            <button
              onClick={() => setShowNewProjectModal(true)}
              className="inline-flex items-center gap-1.5 rounded-lg border border-indigo-500/40 bg-indigo-600/20 px-3 py-1.5 text-xs font-medium text-indigo-300 hover:bg-indigo-600/30 transition"
            >
              <Plus className="h-4 w-4" />
              Tạo Project SLR Mới (PICO)
            </button>
          </div>

          <KpiDashboard kpiMetrics={kpiMetrics} />

          <div className="flex overflow-x-auto border-b border-slate-800 space-x-6 text-sm font-medium">
            {tabs.map((tab) => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`pb-3 shrink-0 transition flex items-center gap-2 ${
                    activeTab === tab.id ? `border-b-2 ${tab.accent} font-semibold` : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <Icon className={`h-4 w-4 ${tab.iconColor || ''}`} />
                  {tab.label}
                </button>
              )
            })}
          </div>

          {activeTab === 'setup' && (
            <ResearchSetupTab
              activeProject={activeProject}
              isDemoMode={isDemoMode}
              onApplyBooleanQuery={(q) => {
                setSearchQuery(q)
                setActiveTab('screening')
              }}
            />
          )}

          {activeTab === 'screening' && (
            <ScreeningBoardTab
              searchQuery={searchQuery}
              setSearchQuery={setSearchQuery}
              searchLimit={searchLimit}
              setSearchLimit={setSearchLimit}
              yearFrom={yearFrom}
              setYearFrom={setYearFrom}
              yearTo={yearTo}
              setYearTo={setYearTo}
              openAccessOnly={openAccessOnly}
              setOpenAccessOnly={setOpenAccessOnly}
              isSearching={isSearching}
              onSearch={handleSearch}
              searchHistory={searchHistory}
              isRunningAL={isRunningAL}
              onRunActiveLearning={handleRunActiveLearning}
              isRunningLLM={isRunningLLM}
              onAutoLabelUncertain={handleAutoLabelUncertain}
              isRunningDualPeer={isRunningDualPeer}
              onRunDualPeer={handleRunDualPeer}
              isSnowballing={isSnowballing}
              onSnowball={handleSnowball}
              qualityGate={qualityGate}
              papers={papers}
              onLabelPaper={handleLabelPaper}
              onHitlApprove={handleHitlApprove}
              onIngestPdf={handleIngestPdf}
              ingestingPaperId={ingestingPaperId}
            />
          )}

          {activeTab === 'matrix' && (
            <EvidenceMatrixTab
              isLoadingMatrix={isLoadingMatrix}
              matrixData={matrixData}
              onReload={() => loadComparativeMatrix(selectedProjectId)}
            />
          )}

          {activeTab === 'analysis' && (
            <DataAnalysisTab
              projectId={selectedProjectId}
              isDemoMode={isDemoMode}
              datasets={datasets}
              selectedDatasetId={selectedDatasetId}
              setSelectedDatasetId={setSelectedDatasetId}
              datasetName={datasetName}
              setDatasetName={setDatasetName}
              csvInput={csvInput}
              setCsvInput={setCsvInput}
              isProfiling={isProfiling}
              onUploadDataset={handleUploadDataset}
              onReloadDatasets={() => loadProjectDatasets(selectedProjectId)}
              analysisGoal={analysisGoal}
              setAnalysisGoal={setAnalysisGoal}
              isAdvising={isAdvising}
              onGetAnalysisAdvice={handleGetAnalysisAdvice}
              analysisResult={analysisResult}
            />
          )}

          {activeTab === 'conflicts' && (
            <ConflictGraphTab
              isAnalyzingConflicts={isAnalyzingConflicts}
              onRunConflictAnalysis={handleRunConflictAnalysis}
              isLoadingGraph={isLoadingGraph}
              graphData={graphData}
            />
          )}

          {activeTab === 'workspace' && (
            <WorkspaceRagTab
              projectId={selectedProjectId}
              papers={papers}
              messages={workspaceMessages}
              setMessages={setWorkspaceMessages}
              isDemoMode={isDemoMode}
              onReloadPapers={() => loadProjectPapers(selectedProjectId)}
            />
          )}

          {activeTab === 'draft' && (
            <DraftExportTab
              projectId={selectedProjectId}
              isDemoMode={isDemoMode}
              draftReport={draftReport}
              isGeneratingDraft={isGeneratingDraft}
              draftFormat={draftFormat}
              setDraftFormat={setDraftFormat}
              onDownloadDraftFile={downloadDraftFile}
            />
          )}
        </main>
      )}

      <NewProjectModal
        isOpen={showNewProjectModal}
        newProject={newProject}
        setNewProject={setNewProject}
        onClose={() => setShowNewProjectModal(false)}
        onSubmit={createProject}
      />
    </div>
  )
}
