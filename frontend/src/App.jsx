import { useState, useEffect } from 'react'
import {
  Filter,
  GitCompare,
  Search,
  Sparkles,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Clock,
  Zap,
  BarChart3,
  Bot,
  Plus,
  ArrowRight,
  ShieldCheck,
  FileSpreadsheet,
  AlertTriangle,
} from 'lucide-react'
import { apiRequest } from './services/api'

export default function App() {
  const [apiStatus, setApiStatus] = useState('checking')
  const [token, setToken] = useState(() => localStorage.getItem('litnexus_token'))
  const [activeTab, setActiveTab] = useState('screening') // 'screening' | 'matrix' | 'conflicts'
  
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

  // Papers and Search
  const [papers, setPapers] = useState([])
  const [searchQuery, setSearchQuery] = useState('wearable ECG 1D CNN arrhythmia')
  const [searchLimit, setSearchLimit] = useState(25)
  const [isSearching, setIsSearching] = useState(false)
  const [yearFrom, setYearFrom] = useState('')
  const [yearTo, setYearTo] = useState('')
  const [openAccessOnly, setOpenAccessOnly] = useState(false)

  // Active Learning & LLM Batch
  const [isRunningAL, setIsRunningAL] = useState(false)
  const [isRunningLLM, setIsRunningLLM] = useState(false)
  const [alSummary, setAlSummary] = useState(null)

  // KPI Metrics & Comparative Matrix
  const [kpiMetrics, setKpiMetrics] = useState(null)
  const [matrixData, setMatrixData] = useState([])
  const [isLoadingMatrix, setIsLoadingMatrix] = useState(false)

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
  const [analysisGoal, setAnalysisGoal] = useState('Compare F1 score across low vs high noise levels and evaluate sample power')
  const [analysisResult, setAnalysisResult] = useState(null)
  const [isProfiling, setIsProfiling] = useState(false)
  const [isAdvising, setIsAdvising] = useState(false)

  // 1. Initial Health Check
  useEffect(() => {
    apiRequest('/health')
      .then(() => setApiStatus('online'))
      .catch(() => setApiStatus('offline'))
  }, [])

  // 2. Fetch Projects on Auth
  useEffect(() => {
    if (token) {
      loadProjects()
    }
  }, [token])

  // 3. Fetch Papers & KPI when selected project changes
  useEffect(() => {
    if (selectedProjectId) {
      loadProjectPapers(selectedProjectId)
      loadKpiMetrics(selectedProjectId)
      if (activeTab === 'matrix') {
        loadComparativeMatrix(selectedProjectId)
      } else if (activeTab === 'analysis') {
        loadProjectDatasets(selectedProjectId)
      }
    }
  }, [selectedProjectId, activeTab])

  async function handleAuth(e) {
    e.preventDefault()
    setAuthError('')
    try {
      const endpoint = isRegister ? '/auth/register' : '/auth/login'
      const payload = isRegister
        ? { email: authEmail, password: authPassword, full_name: authName }
        : { email: authEmail, password: authPassword }
      
      const res = await apiRequest(endpoint, {
        method: 'POST',
        body: JSON.stringify(payload),
      })
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
  }

  function loadPrototypeDemo() {
    const demoToken = 'mock-demo-token-for-prototype'
    localStorage.setItem('litnexus_token', demoToken)
    setToken(demoToken)

    const demoProject = {
      id: 'demo-proj-1',
      title: 'Wearable ECG 1D CNN Arrhythmia Detection',
      domain: 'Biomedical AI & Wearable Sensors',
      research_question: 'How do 1D CNNs perform on single-lead wearable ECG compared to 2D spectrogram models?',
      inclusion_criteria: ['Uses 1D CNN', 'Wearable single-lead ECG', 'Reports F1 or accuracy on public benchmark'],
      exclusion_criteria: ['Animal studies', '12-lead clinical ECG only', 'Review without empirical experiments'],
    }
    setProjects([demoProject])
    setSelectedProjectId('demo-proj-1')

    setKpiMetrics({
      total_papers: 35,
      included_count: 8,
      excluded_count: 22,
      uncertain_count: 5,
      unscreened_count: 0,
      human_labeled: 6,
      llm_labeled: 4,
      active_learning_labeled: 25,
      automation_rate: 82.86,
      token_savings_percentage: 71.43,
      estimated_hours_saved: 7.25,
    })

    setPapers([
      {
        id: 'p1',
        title: 'Real-Time ECG Arrhythmia Classification Using Lightweight 1D Convolutional Neural Networks',
        authors: ['Zhang, Wei', 'Smith, John', 'Tan, Le'],
        journal: 'IEEE Transactions on Biomedical Engineering',
        year: 2024,
        scopus_quartile: 'Q1',
        screening_status: 'uncertain',
        screening_source: 'none',
        al_inclusion_prob: 0.52,
        al_uncertainty_score: 0.96,
        abstract: 'We present a lightweight 1D CNN architecture tailored for edge computing on wearable single-lead patches, achieving 98.2% F1 on MIT-BIH dataset with only 45k parameters.',
      },
      {
        id: 'p2',
        title: 'Deep Residual 2D Spectrogram Networks for Multilead Clinical Holter Monitoring',
        authors: ['Kumar, Rajesh', 'Patel, Anita'],
        journal: 'Computers in Biology and Medicine',
        year: 2023,
        scopus_quartile: 'Q1',
        screening_status: 'excluded',
        screening_source: 'active_learning',
        al_inclusion_prob: 0.08,
        al_uncertainty_score: 0.16,
        abstract: 'This study converts 12-lead clinical ECG recordings into 2D STFT spectrogram images and trains a ResNet-50 for hospital intensive care telemetry.',
      },
      {
        id: 'p3',
        title: 'Ultra-low Power Neural Accelerators for Single-Lead Patch Arrhythmia Screening',
        authors: ['Nguyen, Nam', 'Le, Duy'],
        journal: 'IEEE Transactions on Neural Networks and Learning Systems',
        year: 2024,
        scopus_quartile: 'Q1',
        screening_status: 'included',
        screening_source: 'llm',
        al_inclusion_prob: 0.91,
        al_uncertainty_score: 0.18,
        abstract: 'Demonstrating an ultra-compact 1D convolutional model deployed on ARM Cortex-M4 wearable patches with 97.8% sensitivity under noisy motion artifacts.',
      },
    ])

    setMatrixData([
      {
        paper_id: 'p1',
        paper_title: 'Real-Time ECG Arrhythmia Classification Using Lightweight 1D Convolutional Neural Networks',
        year: 2024,
        scopus_quartile: 'Q1',
        claim_id: 'c1',
        claim_text: 'Lightweight 1D CNN matches 2D ResNet accuracy on wearable single-lead ECG while reducing compute by 14x.',
        methodology: 'Lightweight 1D-CNN (3 Conv layers, Depthwise Separable)',
        dataset: 'MIT-BIH Arrhythmia Benchmark (Single-lead Lead II)',
        metric_summary: 'F1-score = 0.982, Latency = 18ms, Params = 45k',
        assumptions: ['Stationary baseline noise', 'Segmented R-peaks provided by hardware detector'],
        evidence_quote: 'Our lightweight 1D CNN architecture achieves 98.2% F1 on MIT-BIH with only 45k parameters, cutting inference latency to 18ms.',
      },
      {
        paper_id: 'p3',
        paper_title: 'Ultra-low Power Neural Accelerators for Single-Lead Patch Arrhythmia Screening',
        year: 2024,
        scopus_quartile: 'Q1',
        claim_id: 'c2',
        claim_text: 'Quantized 1D CNN retains 97.8% sensitivity under real-world ambulatory motion artifacts.',
        methodology: '8-bit Quantized 1D-CNN with Temporal Batch Normalization',
        dataset: 'In-house Wearable Chest Patch Cohort (N=120 ambulatory patients)',
        metric_summary: 'Sensitivity = 97.8%, Power = 1.2mW',
        assumptions: ['Ambulatory motion artifacts present', 'Sampling rate fixed at 250Hz'],
        evidence_quote: 'The 8-bit quantized 1D model retained 97.8% sensitivity under continuous ambulatory motion with 1.2mW power draw.',
      },
    ])

    const demoDataset = {
      id: 'demo-dataset-1',
      dataset_name: 'Wearable_Cohort_Pilot_N8.csv',
      row_count: 8,
      column_count: 6,
      columns_metadata: [
        { name: 'patient_id', data_type: 'string', missing_count: 0, missing_ratio: 0.0, unique_count: 8, sample_values: ['p_01', 'p_02'] },
        { name: 'age', data_type: 'numeric', missing_count: 0, missing_ratio: 0.0, unique_count: 8, sample_values: ['45', '52'] },
        { name: 'wearable_snr', data_type: 'numeric', missing_count: 0, missing_ratio: 0.0, unique_count: 8, sample_values: ['18.5', '14.2'] },
        { name: 'heart_rate', data_type: 'numeric', missing_count: 0, missing_ratio: 0.0, unique_count: 8, sample_values: ['72', '85'] },
        { name: 'f1_score', data_type: 'numeric', missing_count: 0, missing_ratio: 0.0, unique_count: 8, sample_values: ['0.98', '0.94'] },
        { name: 'noise_level', data_type: 'string', missing_count: 0, missing_ratio: 0.0, unique_count: 3, sample_values: ['low', 'medium', 'high'] },
      ],
      missing_value_summary: {},
      sample_preview: [
        { patient_id: 'p_01', age: '45', wearable_snr: '18.5', heart_rate: '72', f1_score: '0.98', noise_level: 'low' },
        { patient_id: 'p_02', age: '52', wearable_snr: '14.2', heart_rate: '85', f1_score: '0.94', noise_level: 'medium' },
      ],
    }
    setDatasets([demoDataset])
    setSelectedDatasetId('demo-dataset-1')

    setAnalysisResult({
      risk_level: 'high',
      analysis_goal: 'Compare F1 score across low vs high noise levels and evaluate sample power',
      data_limitations: [
        {
          warning_type: 'SMALL_SAMPLE_SIZE',
          severity: 'high',
          message: 'Sample size N=8 is strictly below statistical threshold (N < 30).',
          recommendation: 'Do NOT use Student t-test or parametric ANOVA. Apply Mann-Whitney U or Wilcoxon rank-sum test with exact permutation and 95% Bootstrap CI.',
        },
      ],
      recommended_methods: [
        {
          method_name: 'Mann-Whitney U Test (Exact Permutation)',
          category: 'Non-Parametric Hypothesis Testing',
          rational: 'Robust against non-normality and avoids distributional bias on small pilot cohorts N=8.',
          assumptions: ['Independent observations', 'Continuous metric scale'],
          is_recommended: true,
        },
        {
          method_name: 'Bootstrap BCa 95% Confidence Intervals',
          category: 'Resampling Estimation',
          rational: 'Provides accurate confidence interval boundaries without assuming normal distribution.',
          assumptions: ['Random sample'],
          is_recommended: true,
        },
      ],
      suggested_python_code: `import pandas as pd
import numpy as np
from scipy import stats

# Empirical pilot analysis for N=8 wearable sensor data
df = pd.DataFrame({
    'f1_score': [0.98, 0.94, 0.86, 0.99, 0.81, 0.95, 0.89, 0.97],
    'noise': ['low', 'medium', 'high', 'low', 'high', 'medium', 'medium', 'low']
})

low_noise = df[df['noise'] == 'low']['f1_score']
high_noise = df[df['noise'] == 'high']['f1_score']

# Crucial Guard: Non-parametric Mann-Whitney U test (N < 30)
stat, p_val = stats.mannwhitneyu(low_noise, high_noise, alternative='two-sided')
print(f"Mann-Whitney U statistic: {stat:.2f}, Exact p-value: {p_val:.4f}")

# Bootstrap median difference
def bootstrap_diff(a, b, n_iter=2000):
    diffs = [np.median(np.random.choice(a, len(a), replace=True)) - 
             np.median(np.random.choice(b, len(b), replace=True)) for _ in range(n_iter)]
    return np.percentile(diffs, [2.5, 97.5])

ci_low, ci_high = bootstrap_diff(low_noise, high_noise)
print(f"95% Bootstrap CI for median difference: [{ci_low:.3f}, {ci_high:.3f}]")`,
      interpretation_guide: `Reporting format for IEEE/Nature:
"Due to the pilot cohort size (N=8), non-parametric analysis was employed. Wearable ECG models in low-noise conditions demonstrated significantly higher F1 scores compared to high-noise environments (Mann-Whitney U=0.0, p=0.038, Bootstrap 95% CI [0.08, 0.17]). However, given the limited sample power, these exploratory findings should be validated on a larger clinical cohort (N >= 50)."`,
    })
  }

  async function loadProjects() {
    try {
      const list = await apiRequest('/projects')
      setProjects(list)
      if (list.length > 0 && !selectedProjectId) {
        setSelectedProjectId(list[0].id)
      }
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
      const created = await apiRequest('/projects', {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      setProjects([created, ...projects])
      setSelectedProjectId(created.id)
      setShowNewProjectModal(false)
    } catch (err) {
      alert('Failed to create project: ' + err.message)
    }
  }

  async function loadProjectPapers(pId) {
    try {
      const list = await apiRequest(`/projects/${pId}/papers`)
      setPapers(list)
    } catch (err) {
      console.error(err)
    }
  }

  async function loadKpiMetrics(pId) {
    try {
      const data = await apiRequest(`/projects/${pId}/conflicts/kpi-metrics`)
      setKpiMetrics(data)
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
      if (list.length > 0 && !selectedDatasetId) {
        setSelectedDatasetId(list[0].id)
      }
    } catch (err) {
      console.error(err)
    }
  }

  async function handleUploadDataset(e) {
    e.preventDefault()
    if (!selectedProjectId) return
    setIsProfiling(true)
    try {
      const res = await apiRequest(`/projects/${selectedProjectId}/analysis/datasets`, {
        method: 'POST',
        body: JSON.stringify({
          dataset_name: datasetName,
          csv_raw_text: csvInput,
        }),
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
        body: JSON.stringify({
          analysis_goal: analysisGoal,
        }),
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
      await loadKpiMetrics(selectedProjectId)
    } catch (err) {
      alert('Search failed: ' + err.message)
    } finally {
      setIsSearching(false)
    }
  }

  async function handleLabelPaper(paperId, status) {
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

  async function handleRunActiveLearning() {
    setIsRunningAL(true)
    try {
      const res = await apiRequest(`/projects/${selectedProjectId}/screening/run-active-learning`, {
        method: 'POST',
      })
      setAlSummary(res)
      await loadProjectPapers(selectedProjectId)
      await loadKpiMetrics(selectedProjectId)
    } catch (err) {
      alert('Active Learning failed: ' + err.message)
    } finally {
      setIsRunningAL(false)
    }
  }

  async function handleAutoLabelUncertain() {
    setIsRunningLLM(true)
    try {
      const res = await apiRequest(`/projects/${selectedProjectId}/screening/auto-label-uncertain`, {
        method: 'POST',
        body: JSON.stringify({ limit: 10 }),
      })
      alert(`LLM đã phân loại ${res.processed_count} bài (Bao gồm: ${res.auto_included} bài Included, ${res.auto_excluded} bài Excluded) có bằng chứng trích dẫn.`)
      await loadProjectPapers(selectedProjectId)
      await loadKpiMetrics(selectedProjectId)
    } catch (err) {
      alert('Auto-label failed: ' + err.message)
    } finally {
      setIsRunningLLM(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans">
      {/* Top Header */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3.5">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-indigo-700 font-bold shadow-md shadow-indigo-500/20">
              LN
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-semibold tracking-tight text-white">LitNexus</h1>
                <span className="rounded bg-indigo-500/20 px-2 py-0.5 text-[10px] font-medium text-indigo-300 border border-indigo-500/30">
                  SLR &amp; Conflict Engine
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Active Learning Systematic Review &bull; Zero-Hallucination Evidence Grounding
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 rounded-full border border-slate-800 bg-slate-900 px-3 py-1 text-xs">
              <span
                className={`h-2 w-2 rounded-full ${
                  apiStatus === 'online' ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'
                }`}
              />
              <span className="text-slate-300">Backend: {apiStatus}</span>
            </div>

            {token && (
              <button
                onClick={handleLogout}
                className="text-xs text-slate-400 hover:text-slate-200 transition underline underline-offset-4"
              >
                Đăng xuất
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      {!token ? (
        /* Login / Register Card */
        <div className="mx-auto max-w-md px-6 py-20">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-8 shadow-2xl backdrop-blur">
            <div className="mb-6 text-center">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 mb-3">
                <ShieldCheck className="h-6 w-6" />
              </div>
              <h2 className="text-xl font-bold text-white">
                {isRegister ? 'Tạo Tài khoản Nghiên cứu' : 'Đăng nhập LitNexus'}
              </h2>
              <p className="mt-1 text-xs text-slate-400">
                Bảo vệ đa người dùng và cô lập dữ liệu nghiên cứu theo chuẩn an toàn
              </p>
            </div>

            {authError && (
              <div className="mb-4 rounded-lg border border-rose-500/40 bg-rose-950/40 p-3 text-xs text-rose-300">
                {authError}
              </div>
            )}

            <form onSubmit={handleAuth} className="space-y-4">
              {isRegister && (
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Họ và tên</label>
                  <input
                    type="text"
                    required
                    value={authName}
                    onChange={(e) => setAuthName(e.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
                    placeholder="TS. Nguyễn Văn A"
                  />
                </div>
              )}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Email Học thuật</label>
                <input
                  type="email"
                  required
                  value={authEmail}
                  onChange={(e) => setAuthEmail(e.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
                  placeholder="researcher@university.edu"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Mật khẩu</label>
                <input
                  type="password"
                  required
                  value={authPassword}
                  onChange={(e) => setAuthPassword(e.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
                  placeholder="••••••••"
                />
              </div>

              <button
                type="submit"
                className="w-full rounded-lg bg-indigo-600 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-600/30 hover:bg-indigo-500 transition"
              >
                {isRegister ? 'Đăng ký Tài khoản' : 'Đăng nhập vào Hệ thống'}
              </button>
            </form>

            {/* Quick Demo Prototype Mode */}
            <div className="mt-4 pt-4 border-t border-slate-800">
              <button
                type="button"
                onClick={loadPrototypeDemo}
                className="w-full flex items-center justify-center gap-2 rounded-lg border border-indigo-500/40 bg-indigo-950/40 py-2 text-xs font-semibold text-indigo-300 hover:bg-indigo-900/40 transition"
              >
                <Sparkles className="h-4 w-4 text-indigo-400" />
                Vào xem Prototype &bull; Trải nghiệm Dữ liệu Mẫu (Demo Mode)
              </button>
              <p className="mt-1.5 text-center text-[11px] text-slate-500">
                Xem ngay giao diện Active Screening, Ma trận Bằng chứng và KPI mà không cần nạp DB
              </p>
            </div>

            <div className="mt-6 text-center text-xs text-slate-400">
              {isRegister ? 'Đã có tài khoản?' : 'Chưa có tài khoản nghiên cứu?'}{' '}
              <button
                onClick={() => setIsRegister(!isRegister)}
                className="font-medium text-indigo-400 hover:text-indigo-300 underline"
              >
                {isRegister ? 'Đăng nhập' : 'Tạo mới ngay'}
              </button>
            </div>
          </div>
        </div>
      ) : (
        /* Workspace */
        <main className="mx-auto max-w-7xl px-6 py-6 space-y-6">
          {/* Project Switcher Bar */}
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

          {/* KPI Dashboard Widget */}
          {kpiMetrics && (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-6">
              <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-3.5">
                <div className="flex items-center justify-between text-slate-400 text-xs">
                  <span>Tổng bài nạp</span>
                  <Filter className="h-4 w-4 text-slate-500" />
                </div>
                <div className="mt-1 text-2xl font-bold text-white">{kpiMetrics.total_papers}</div>
                <div className="text-[11px] text-slate-500 mt-0.5">Trong cơ sở dữ liệu</div>
              </div>

              <div className="rounded-xl border border-emerald-900/40 bg-emerald-950/20 p-3.5">
                <div className="flex items-center justify-between text-emerald-400 text-xs">
                  <span>Included</span>
                  <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                </div>
                <div className="mt-1 text-2xl font-bold text-emerald-300">{kpiMetrics.included_count}</div>
                <div className="text-[11px] text-emerald-500/80 mt-0.5">Bài nghiên cứu cốt lõi</div>
              </div>

              <div className="rounded-xl border border-rose-900/40 bg-rose-950/20 p-3.5">
                <div className="flex items-center justify-between text-rose-400 text-xs">
                  <span>Excluded</span>
                  <XCircle className="h-4 w-4 text-rose-400" />
                </div>
                <div className="mt-1 text-2xl font-bold text-rose-300">{kpiMetrics.excluded_count}</div>
                <div className="text-[11px] text-rose-500/80 mt-0.5">Đã loại trừ</div>
              </div>

              <div className="rounded-xl border border-amber-900/40 bg-amber-950/20 p-3.5">
                <div className="flex items-center justify-between text-amber-400 text-xs">
                  <span>Cần rà soát (HITL)</span>
                  <HelpCircle className="h-4 w-4 text-amber-400" />
                </div>
                <div className="mt-1 text-2xl font-bold text-amber-300">{kpiMetrics.uncertain_count}</div>
                <div className="text-[11px] text-amber-500/80 mt-0.5">Độ bất định U(p) cao</div>
              </div>

              <div className="rounded-xl border border-indigo-900/40 bg-indigo-950/20 p-3.5">
                <div className="flex items-center justify-between text-indigo-400 text-xs">
                  <span>Tiết kiệm Token</span>
                  <Zap className="h-4 w-4 text-indigo-400" />
                </div>
                <div className="mt-1 text-2xl font-bold text-indigo-300">
                  {kpiMetrics.token_savings_percentage}%
                </div>
                <div className="text-[11px] text-indigo-400/80 mt-0.5">Nhờ Active Learning</div>
              </div>

              <div className="rounded-xl border border-cyan-900/40 bg-cyan-950/20 p-3.5">
                <div className="flex items-center justify-between text-cyan-400 text-xs">
                  <span>Giờ đọc tiết kiệm</span>
                  <Clock className="h-4 w-4 text-cyan-400" />
                </div>
                <div className="mt-1 text-2xl font-bold text-cyan-300">
                  {kpiMetrics.estimated_hours_saved}h
                </div>
                <div className="text-[11px] text-cyan-400/80 mt-0.5">&ge; 50% mục tiêu ĐH X</div>
              </div>
            </div>
          )}

          {/* Navigation Tabs */}
          <div className="flex border-b border-slate-800 space-x-6 text-sm font-medium">
            <button
              onClick={() => setActiveTab('screening')}
              className={`pb-3 transition flex items-center gap-2 ${
                activeTab === 'screening'
                  ? 'border-b-2 border-indigo-500 text-indigo-400 font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Filter className="h-4 w-4" />
              1. Phễu Sàng Lọc Học máy (Active Screening Board)
            </button>
            <button
              onClick={() => setActiveTab('matrix')}
              className={`pb-3 transition flex items-center gap-2 ${
                activeTab === 'matrix'
                  ? 'border-b-2 border-indigo-500 text-indigo-400 font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <FileSpreadsheet className="h-4 w-4" />
              2. Bảng Ma trận So sánh Bằng chứng (Comparative Matrix)
            </button>
            <button
              onClick={() => setActiveTab('analysis')}
              className={`pb-3 transition flex items-center gap-2 ${
                activeTab === 'analysis'
                  ? 'border-b-2 border-indigo-500 text-indigo-400 font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <BarChart3 className="h-4 w-4 text-emerald-400" />
              3. Trợ lý Phân Tích Dữ Liệu Sơ Bộ &bull; Cảnh Báo Giới Hạn (Data Analysis Studio)
            </button>
          </div>

          {/* Tab 1: Screening Board */}
          {activeTab === 'screening' && (
            <div className="space-y-6">
              {/* Search & Ingestion Box */}
              <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 backdrop-blur">
                <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                  <Search className="h-4 w-4 text-indigo-400" />
                  Tìm kiếm &amp; Nạp Bài báo Học thuật Miễn phí (OpenAlex &bull; SCImago SJR)
                </h3>
                <form onSubmit={handleSearch} className="space-y-3">
                  <div className="flex flex-col sm:flex-row gap-2">
                    <input
                      type="text"
                      required
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="flex-1 rounded-lg border border-slate-700 bg-slate-950 px-4 py-2 text-sm text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
                      placeholder="Nhập từ khóa học thuật (vd: wearable ECG 1D CNN arrhythmia)..."
                    />
                    <button
                      type="submit"
                      disabled={isSearching}
                      className="inline-flex items-center justify-center gap-2 rounded-lg bg-indigo-600 px-5 py-2 text-sm font-semibold text-white hover:bg-indigo-500 disabled:opacity-50 transition"
                    >
                      {isSearching ? 'Đang truy vấn OpenAlex...' : 'Tìm & Nạp bài báo'}
                    </button>
                  </div>

                  {/* Filter Chips */}
                  <div className="flex flex-wrap items-center gap-4 pt-1 text-xs text-slate-400">
                    <div className="flex items-center gap-1.5">
                      <span>Số bài nạp:</span>
                      <select
                        value={searchLimit}
                        onChange={(e) => setSearchLimit(e.target.value)}
                        className="rounded border border-slate-700 bg-slate-950 px-2 py-0.5 text-xs text-slate-200"
                      >
                        <option value={10}>10</option>
                        <option value={25}>25</option>
                        <option value={50}>50</option>
                      </select>
                    </div>

                    <div className="flex items-center gap-1.5">
                      <span>Từ năm:</span>
                      <input
                        type="number"
                        placeholder="2020"
                        value={yearFrom}
                        onChange={(e) => setYearFrom(e.target.value)}
                        className="w-16 rounded border border-slate-700 bg-slate-950 px-1.5 py-0.5 text-xs text-slate-200 text-center"
                      />
                    </div>

                    <div className="flex items-center gap-1.5">
                      <span>Đến năm:</span>
                      <input
                        type="number"
                        placeholder="2026"
                        value={yearTo}
                        onChange={(e) => setYearTo(e.target.value)}
                        className="w-16 rounded border border-slate-700 bg-slate-950 px-1.5 py-0.5 text-xs text-slate-200 text-center"
                      />
                    </div>

                    <label className="flex items-center gap-1.5 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={openAccessOnly}
                        onChange={(e) => setOpenAccessOnly(e.target.checked)}
                        className="rounded border-slate-700 bg-slate-950 text-indigo-600 focus:ring-0"
                      />
                      <span>Chỉ lấy bài Open Access / Toàn văn miễn phí</span>
                    </label>
                  </div>
                </form>
              </div>

              {/* Action Toolbar for Active Learning & LLM Batch */}
              <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-800 bg-slate-900/60 p-4">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-400 font-medium">Quy trình Active Learning:</span>
                  <span className="text-xs text-slate-300">
                    Chấm &ge; 6 bài mẫu (bao gồm cả Included &amp; Excluded) rồi kích hoạt huấn luyện cục bộ.
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={handleRunActiveLearning}
                    disabled={isRunningAL}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-indigo-500/40 bg-indigo-600/20 px-3.5 py-1.5 text-xs font-semibold text-indigo-300 hover:bg-indigo-600/30 transition disabled:opacity-50"
                  >
                    <Zap className="h-4 w-4" />
                    {isRunningAL ? 'Đang train ML...' : 'Huấn luyện Active Learning'}
                  </button>

                  <button
                    onClick={handleAutoLabelUncertain}
                    disabled={isRunningLLM}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-emerald-500/40 bg-emerald-600/20 px-3.5 py-1.5 text-xs font-semibold text-emerald-300 hover:bg-emerald-600/30 transition disabled:opacity-50"
                  >
                    <Bot className="h-4 w-4" />
                    {isRunningLLM ? 'LLM đang đọc...' : 'Nhờ AI chấm 10 bài phân vân (Có trích dẫn)'}
                  </button>
                </div>
              </div>

              {/* Papers Review Table */}
              <div className="rounded-xl border border-slate-800 bg-slate-900/40 overflow-hidden shadow-xl">
                <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-white">
                    Danh sách Bài báo ({papers.length} bài) &bull; Tự động xếp bài có độ bất định cao nhất lên đầu
                  </h3>
                </div>

                {papers.length === 0 ? (
                  <div className="py-12 text-center text-sm text-slate-500">
                    Chưa có bài báo nào trong project. Hãy nhập từ khóa tìm kiếm ở trên để nạp dữ liệu.
                  </div>
                ) : (
                  <div className="divide-y divide-slate-800/80">
                    {papers.map((paper) => {
                      const prob = paper.al_inclusion_prob
                      const unc = paper.al_uncertainty_score
                      const isUncertain = unc && unc >= 0.7

                      return (
                        <div key={paper.id} className="p-5 hover:bg-slate-850/40 transition">
                          <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                            <div className="space-y-2 flex-1">
                              <div className="flex flex-wrap items-center gap-2">
                                {paper.scopus_quartile && (
                                  <span className="rounded bg-amber-500/10 border border-amber-500/30 px-2 py-0.5 text-[11px] font-bold text-amber-400">
                                    {paper.scopus_quartile}
                                  </span>
                                )}
                                {paper.year && (
                                  <span className="text-xs text-slate-400 font-medium">({paper.year})</span>
                                )}
                                {paper.journal && (
                                  <span className="text-xs text-slate-400 italic">
                                    &bull; {paper.journal}
                                  </span>
                                )}
                                <span
                                  className={`rounded px-2 py-0.5 text-[11px] font-medium border ${
                                    paper.screening_status === 'included'
                                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                                      : paper.screening_status === 'excluded'
                                      ? 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                                      : paper.screening_status === 'uncertain'
                                      ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                                      : 'bg-slate-800 text-slate-400 border-slate-700'
                                  }`}
                                >
                                  {paper.screening_status.toUpperCase()} ({paper.screening_source})
                                </span>
                              </div>

                              <h4 className="text-base font-semibold text-white leading-snug">
                                {paper.title}
                              </h4>

                              {paper.authors && paper.authors.length > 0 && (
                                <p className="text-xs text-slate-400">
                                  Tác giả: {paper.authors.slice(0, 4).join(', ')}
                                  {paper.authors.length > 4 ? ' et al.' : ''}
                                </p>
                              )}

                              <p className="text-xs text-slate-300 line-clamp-3 leading-relaxed">
                                {paper.abstract || 'Không có đoạn tóm tắt khả dụng.'}
                              </p>

                              {/* Machine Learning Probability & Uncertainty Bar */}
                              {prob !== null && prob !== undefined && (
                                <div className="flex items-center gap-4 pt-1 text-[11px] text-slate-400">
                                  <div>
                                    Xác suất phù hợp (p):{' '}
                                    <span className="font-semibold text-indigo-300">
                                      {(prob * 100).toFixed(1)}%
                                    </span>
                                  </div>
                                  <div>
                                    Độ bất định (U):{' '}
                                    <span
                                      className={`font-semibold ${
                                        isUncertain ? 'text-amber-400' : 'text-slate-400'
                                      }`}
                                    >
                                      {unc?.toFixed(2)}
                                    </span>
                                  </div>
                                </div>
                              )}
                            </div>

                            {/* 1-Click Human-in-the-Loop Labeling Actions */}
                            <div className="flex sm:flex-col items-center gap-2 shrink-0">
                              <button
                                onClick={() => handleLabelPaper(paper.id, 'included')}
                                className="w-24 rounded-lg border border-emerald-500/40 bg-emerald-600/10 px-3 py-1.5 text-xs font-semibold text-emerald-400 hover:bg-emerald-600/20 transition flex items-center justify-center gap-1"
                              >
                                <CheckCircle2 className="h-3.5 w-3.5" />
                                Include
                              </button>
                              <button
                                onClick={() => handleLabelPaper(paper.id, 'excluded')}
                                className="w-24 rounded-lg border border-rose-500/40 bg-rose-600/10 px-3 py-1.5 text-xs font-semibold text-rose-400 hover:bg-rose-600/20 transition flex items-center justify-center gap-1"
                              >
                                <XCircle className="h-3.5 w-3.5" />
                                Exclude
                              </button>
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Tab 2: Comparative Evidence Matrix */}
          {activeTab === 'matrix' && (
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
                  onClick={() => loadComparativeMatrix(selectedProjectId)}
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
                          <td className="px-4 py-3 italic text-amber-200/90 bg-amber-950/10 max-w-[250px] border-l border-amber-500/20">
                            &ldquo;{row.evidence_quote}&rdquo;
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* Tab 3: Data Analysis Assistant Studio (Pillar 2) */}
          {activeTab === 'analysis' && (
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
                      Hệ thống tự động phát hiện cỡ mẫu nhỏ ($N &lt; 30$), bất đối xứng dữ liệu, cảnh báo giới hạn nghiêm ngặt và sinh code Python mẫu (Pandas/Scipy).
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

                    <form onSubmit={handleUploadDataset} className="space-y-3 pt-1 border-t border-slate-800/80">
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

                  {/* Goal Configuration Box */}
                  <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 space-y-3">
                    <h4 className="text-sm font-semibold text-white">2. Mục tiêu Phân Tích Định Lượng</h4>
                    <form onSubmit={handleGetAnalysisAdvice} className="space-y-3">
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

                {/* Right Column: Statistical Warnings, Recommended Methods & Code */}
                <div className="lg:col-span-7 space-y-4">
                  {!analysisResult ? (
                    <div className="rounded-xl border border-slate-800 bg-slate-900/30 p-12 text-center text-xs text-slate-500">
                      Chưa có kết quả phân tích. Hãy chọn bộ dữ liệu và nhấn &ldquo;Gợi Ý Phương Pháp &amp; Sinh Code Phân Tích&rdquo;.
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {/* Crucial Statistical Guard Warnings */}
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

                      {/* Recommended Methods */}
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

                      {/* Executable Python Code */}
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

                      {/* Academic Interpretation Guide */}
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
          )}
        </main>
      )}

      {/* New Project Modal */}
      {showNewProjectModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
            <h3 className="text-lg font-bold text-white mb-2">Tạo Dự án SLR Mới theo PICO</h3>
            <p className="text-xs text-slate-400 mb-4">
              Xác lập mục tiêu nghiên cứu và tiêu chuẩn chọn/loại khắt khe trước khi tìm kiếm.
            </p>

            <form onSubmit={createProject} className="space-y-3">
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
                <label className="block text-xs font-medium text-slate-300 mb-1">Câu hỏi nghiên cứu (Research Question)</label>
                <textarea
                  rows={2}
                  required
                  value={newProject.research_question}
                  onChange={(e) => setNewProject({ ...newProject, research_question: e.target.value })}
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white focus:border-indigo-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-emerald-400 mb-1">Tiêu chuẩn Chọn (Inclusion Criteria - cách nhau bằng dấu phẩy)</label>
                <input
                  type="text"
                  value={newProject.inclusion_criteria}
                  onChange={(e) => setNewProject({ ...newProject, inclusion_criteria: e.target.value })}
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white focus:border-indigo-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-rose-400 mb-1">Tiêu chuẩn Loại (Exclusion Criteria - cách nhau bằng dấu phẩy)</label>
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
                  onClick={() => setShowNewProjectModal(false)}
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
      )}
    </div>
  )
}
