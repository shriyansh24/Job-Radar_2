import React, { useState, useEffect } from 'react';
import { 
  LayoutGrid, List, KanbanSquare, BarChart3, Settings as SettingsIcon, 
  TerminalSquare, Search, Filter, ChevronRight, Star, 
  MapPin, DollarSign, Clock, ExternalLink, Copy, CheckCircle2,
  XCircle, AlertCircle, Play, Pause, ChevronDown, Check,
  Briefcase, Activity, Target, UploadCloud, Eye, EyeOff, Save,
  Sparkles, Loader2, MessageSquare
} from 'lucide-react';

// --- GEMINI API HELPER ---
const callGeminiAPI = async (prompt, systemInstruction = "You are an expert career coach and technical recruiter. Format responses clearly and concisely.") => {
  const apiKey = ""; // Provided by the execution environment
  const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key=${apiKey}`;
  
  const payload = {
    contents: [{ parts: [{ text: prompt }] }],
    systemInstruction: { parts: [{ text: systemInstruction }] }
  };

  let delay = 1000;
  for (let i = 0; i < 5; i++) {
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!response.ok) throw new Error(`API Error: ${response.status}`);
      const result = await response.json();
      return result.candidates?.[0]?.content?.parts?.[0]?.text || "No insights generated.";
    } catch (error) {
      if (i === 4) throw new Error("Failed to generate content after multiple attempts.");
      await new Promise(r => setTimeout(r, delay));
      delay *= 2; // 1s, 2s, 4s, 8s, 16s
    }
  }
};

// --- DESIGN SYSTEM (Injected via Style Tag) ---
const StyleSystem = () => (
  <style>{`
    @import url('https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500;600&display=swap');

    :root {
      --bg-base: #000000;
      --bg-surface: #0a0a0a;
      --bg-elevated: #111111;
      --border: #333333;
      --text-primary: #EDEDED;
      --text-secondary: #888888;
      --accent: #0070F3; /* Vercel Blue */
      --accent-green: #10B981;
      --accent-amber: #F5A623;
      --accent-red: #E00000;
      --accent-cyan: #3291FF;
      --font-ui: 'Geist', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      --font-mono: 'Geist Mono', monospace;
    }

    body {
      background-color: var(--bg-base);
      color: var(--text-primary);
      font-family: var(--font-ui);
      margin: 0;
      overflow: hidden; /* App shell handles scrolling */
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
    }

    .font-mono { font-family: var(--font-mono); }
    
    /* Custom Scrollbar - Cleaner and thinner */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: var(--bg-base); }
    ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--text-secondary); }

    /* Utilities */
    .glass-panel { background: rgba(10, 10, 10, 0.7); backdrop-filter: blur(12px); border-top: 1px solid var(--border); }
  `}</style>
);

// --- MOCK DATA ---
const MOCK_JOBS = [
  {
    id: 'j1', title: 'AI Engineer', company: 'OpenAI', domain: 'openai.com', location: 'San Francisco, CA',
    remote_type: 'hybrid', source: 'greenhouse', posted_at: '2h ago', match_score: 96,
    salary: '$180k - $250k', tech_stack: ['Python', 'PyTorch', 'C++'], status: 'new',
    summary: 'Core engineering role working on foundational models. High focus on optimization and large-scale distributed training infrastructure.',
    flags: { green: ['Clear comp', 'Top tier AI'], red: ['High stress potential'] }
  },
  {
    id: 'j2', title: 'Machine Learning Engineer', company: 'Anthropic', domain: 'anthropic.com', location: 'Remote',
    remote_type: 'remote', source: 'lever', posted_at: '5h ago', match_score: 94,
    salary: '$175k - $230k', tech_stack: ['Python', 'Rust', 'AWS'], status: 'saved',
    summary: 'Focuses on alignment and model safety. Requires strong background in reinforcement learning from human feedback (RLHF).',
    flags: { green: ['Fully remote', 'Safety focused'], red: [] }
  },
  {
    id: 'j3', title: 'Software Engineer, ML Systems', company: 'Stripe', domain: 'stripe.com', location: 'Seattle, WA',
    remote_type: 'onsite', source: 'greenhouse', posted_at: '1d ago', match_score: 88,
    salary: '$160k - $210k', tech_stack: ['Ruby', 'Python', 'Kafka'], status: 'applied',
    summary: 'Building ML infrastructure for fraud detection pipelines processing millions of transactions daily.',
    flags: { green: ['Great benefits'], red: ['On-site required'] }
  },
  {
    id: 'j4', title: 'Senior Data Scientist', company: 'Figma', domain: 'figma.com', location: 'New York, NY',
    remote_type: 'hybrid', source: 'ashby', posted_at: '2d ago', match_score: 82,
    salary: null, tech_stack: ['Python', 'SQL', 'dbt'], status: 'interviewing',
    summary: 'Product analytics and predictive modeling for user growth and feature adoption.',
    flags: { green: ['Design focused'], red: ['No salary listed'] }
  },
  {
    id: 'j5', title: 'Full Stack Engineer', company: 'Vercel', domain: 'vercel.com', location: 'Remote',
    remote_type: 'remote', source: 'serpapi', posted_at: '3d ago', match_score: 91,
    salary: '$150k - $190k', tech_stack: ['TypeScript', 'React', 'Rust'], status: 'rejected',
    summary: 'Building core platform features for Next.js and the Vercel deployment infrastructure.',
    flags: { green: ['Next.js ecosystem'], red: [] }
  },
  {
    id: 'j6', title: 'Backend Engineer', company: 'Discord', domain: 'discord.com', location: 'Remote',
    remote_type: 'remote', source: 'jobspy', posted_at: '4d ago', match_score: 85,
    salary: '$165k - $200k', tech_stack: ['Rust', 'Elixir', 'PostgreSQL'], status: 'offer',
    summary: 'Scaling real-time communication systems for millions of concurrent users.',
    flags: { green: ['Massive scale', 'Elixir/Rust stack'], red: [] }
  },
  {
    id: 'j7', title: 'Data Engineer', company: 'Netflix', domain: 'netflix.com', location: 'Los Gatos, CA',
    remote_type: 'hybrid', source: 'lever', posted_at: '6d ago', match_score: 79,
    salary: '$200k - $300k', tech_stack: ['Spark', 'Python', 'AWS'], status: 'ghosted',
    summary: 'Building petabyte-scale data pipelines for content recommendation engines.',
    flags: { green: ['Top tier comp'], red: ['Intense culture'] }
  }
];

const SOURCE_COLORS = {
  greenhouse: 'text-emerald-400 border-emerald-400/30 bg-emerald-400/10',
  lever: 'text-violet-400 border-violet-400/30 bg-violet-400/10',
  ashby: 'text-orange-400 border-orange-400/30 bg-orange-400/10',
  serpapi: 'text-red-400 border-red-400/30 bg-red-400/10',
  jobspy: 'text-slate-400 border-slate-400/30 bg-slate-400/10',
};

const STATUS_COLORS = {
  new: 'text-[var(--accent-green)]',
  saved: 'text-[var(--accent-amber)]',
  applied: 'text-[var(--accent-cyan)]',
  interviewing: 'text-purple-400',
  offer: 'text-pink-400',
  rejected: 'text-[var(--accent-red)]',
  ghosted: 'text-slate-500'
};

const KANBAN_COLUMNS = ['Saved', 'Applied', 'Phone Screen', 'Interview', 'Final Round', 'Offer', 'Rejected', 'Ghosted'];

// --- COMPONENTS ---

const ScoreRing = ({ score, size = 40, strokeWidth = 4 }) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (score / 100) * circumference;
  
  // Color logic
  let color = 'var(--accent)';
  if (score >= 90) color = 'var(--accent-green)';
  else if (score >= 80) color = 'var(--accent-cyan)';
  else if (score < 60) color = 'var(--accent-red)';

  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <svg className="transform -rotate-90 w-full h-full">
        <circle cx={size/2} cy={size/2} r={radius} stroke="var(--border)" strokeWidth={strokeWidth} fill="none" />
        <circle cx={size/2} cy={size/2} r={radius} stroke={color} strokeWidth={strokeWidth} fill="none" 
          strokeDasharray={circumference} strokeDashoffset={offset} strokeLinecap="round" 
          className="transition-all duration-1000 ease-out" />
      </svg>
      <span className="absolute font-mono text-[10px] font-medium" style={{ color }}>{score}</span>
    </div>
  );
};

const ScraperLogDrawer = () => {
  const [isOpen, setIsOpen] = useState(false);
  
  const logs = [
    { time: '14:23:01', source: 'serpapi', msg: 'Found 47 jobs for "AI Engineer" in "Remote"', type: 'info' },
    { time: '14:23:04', source: 'serpapi', msg: '12 new · 35 existing · 0 errors', type: 'success' },
    { time: '14:23:04', source: 'greenhouse', msg: 'Scanning 28 company boards...', type: 'info' },
    { time: '14:23:09', source: 'greenhouse', msg: 'openai: 3 new · anthropic: 1 new · stripe: 0 new', type: 'success' },
    { time: '14:23:15', source: 'lever', msg: 'Rate limit hit for netflix.com, backing off 30s', type: 'error' },
  ];

  return (
    <div className={`fixed bottom-0 right-0 w-full lg:w-[600px] bg-[var(--bg-surface)] border-t border-l border-[var(--border)] rounded-tl-xl shadow-2xl transition-all duration-300 z-50 ${isOpen ? 'h-[200px]' : 'h-[40px]'}`}>
      <div className="flex items-center justify-between px-4 h-[40px] cursor-pointer bg-[var(--bg-elevated)] rounded-tl-xl border-b border-[var(--border)]" onClick={() => setIsOpen(!isOpen)}>
        <div className="flex items-center gap-2">
          <TerminalSquare size={16} className="text-[var(--text-secondary)]" />
          <span className="text-xs font-mono text-[var(--text-secondary)]">Scraper_Terminal.exe</span>
          {!isOpen && <span className="text-xs font-mono text-[var(--accent-green)] ml-4 animate-pulse">Running: greenhouse</span>}
        </div>
        <div className="flex gap-2">
          <Pause size={14} className="text-[var(--text-secondary)] hover:text-white" />
          <ChevronDown size={16} className={`text-[var(--text-secondary)] transition-transform ${isOpen ? '' : 'rotate-180'}`} />
        </div>
      </div>
      
      {isOpen && (
        <div className="p-4 font-mono text-xs overflow-y-auto h-[160px] flex flex-col gap-1">
          {logs.map((log, i) => (
            <div key={i} className="flex gap-3">
              <span className="text-[var(--text-secondary)]">[{log.time}]</span>
              <span className="w-24 text-[var(--accent)]">{log.source.padEnd(10, ' ')}</span>
              <span className="text-[var(--border)]">→</span>
              <span className={log.type === 'error' ? 'text-[var(--accent-red)]' : log.type === 'success' ? 'text-[var(--accent-green)]' : 'text-[var(--text-primary)]'}>
                {log.msg}
              </span>
            </div>
          ))}
          <div className="flex gap-3 animate-pulse">
            <span className="text-[var(--text-secondary)]">[14:23:16]</span>
            <span className="w-24 text-[var(--accent)]">greenhouse</span>
            <span className="text-[var(--border)]">→</span>
            <span className="text-[var(--text-primary)]">Parsing jobs for figma...</span>
          </div>
        </div>
      )}
    </div>
  );
};

// --- PAGES ---

const Dashboard = () => (
  <div className="p-6 space-y-6 animate-in fade-in duration-300">
    {/* STAT CARDS */}
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      {[
        { label: 'Total Jobs', val: '12,847', spark: '+124', color: 'var(--text-primary)' },
        { label: 'New Today', val: '412', spark: '▲ 12% vs yday', color: 'var(--accent-green)' },
        { label: 'Applied', val: '48', spark: '12% success', color: 'var(--accent-cyan)' },
        { label: 'Avg Match Score', val: '78%', spark: 'Top 10% market', color: 'var(--accent)' },
      ].map((stat, i) => (
        <div key={i} className="bg-[var(--bg-surface)] border border-[var(--border)] rounded-lg p-5 flex flex-col gap-2 relative overflow-hidden group">
          <span className="text-sm text-[var(--text-secondary)]">{stat.label}</span>
          <span className="text-3xl font-mono font-medium" style={{ color: stat.color }}>{stat.val}</span>
          <span className="text-xs font-mono text-[var(--text-secondary)]">{stat.spark}</span>
          {/* Decorative noise gradient */}
          <div className="absolute -right-10 -bottom-10 w-32 h-32 bg-[var(--accent)] opacity-5 blur-2xl rounded-full group-hover:opacity-10 transition-opacity" />
        </div>
      ))}
    </div>

    <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
      {/* TOP MATCHES (60%) */}
      <div className="col-span-3 bg-[var(--bg-surface)] border border-[var(--border)] rounded-xl overflow-hidden flex flex-col">
        <div className="p-4 border-b border-[var(--border)] flex justify-between items-center">
          <h2 className="text-sm font-medium flex items-center gap-2">
            <Target size={16} className="text-[var(--accent)]" /> Top Matches
          </h2>
          <button className="text-xs text-[var(--text-secondary)] hover:text-white transition-colors">View All →</button>
        </div>
        <div className="flex-1 overflow-y-auto">
          {MOCK_JOBS.slice(0, 5).map(job => (
            <div key={job.id} className="p-4 border-b border-[var(--border)] flex items-center justify-between hover:bg-[var(--bg-elevated)] transition-colors cursor-pointer group">
              <div className="flex items-center gap-4">
                <img src={`https://logo.clearbit.com/${job.domain}`} alt={job.company} className="w-10 h-10 rounded bg-[var(--bg-elevated)] object-contain p-1" onError={(e) => { e.target.style.display='none'; e.target.nextSibling.style.display='flex'; }} />
                <div className="w-10 h-10 rounded bg-[var(--bg-elevated)] text-[var(--text-secondary)] font-mono text-xs hidden items-center justify-center border border-[var(--border)]">
                  {job.company.substring(0,2).toUpperCase()}
                </div>
                <div>
                  <h3 className="font-medium text-[var(--text-primary)] group-hover:text-[var(--accent)] transition-colors">{job.title}</h3>
                  <div className="flex items-center gap-2 text-xs mt-1">
                    <span className="text-[var(--text-secondary)]">{job.company}</span>
                    <span className="w-1 h-1 rounded-full bg-[var(--border)]" />
                    <span className="text-[var(--text-secondary)]">{job.location}</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-6">
                <div className="flex flex-col items-end gap-1">
                  <span className={`px-2 py-0.5 rounded-full text-[10px] uppercase font-mono border ${SOURCE_COLORS[job.source]}`}>
                    {job.source}
                  </span>
                  <span className="text-[10px] font-mono text-[var(--text-secondary)]">{job.posted_at}</span>
                </div>
                <ScoreRing score={job.match_score} size={36} strokeWidth={3} />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ACTIVITY & SKILLS (40%) */}
      <div className="col-span-2 space-y-6">
        
        <div className="bg-[var(--bg-surface)] border border-[var(--border)] rounded-xl p-4">
          <h2 className="text-sm font-medium mb-4 flex items-center gap-2">
            <Activity size={16} className="text-[var(--accent-green)]" /> Source Activity (7d)
          </h2>
          <div className="h-32 flex items-end justify-between gap-1 mt-6">
            {[40, 65, 30, 85, 120, 90, 150].map((val, i) => (
              <div key={i} className="w-full flex flex-col justify-end group relative">
                <div className="absolute -top-6 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 font-mono text-[10px] transition-opacity">{val}</div>
                {/* Simulated stacked bar */}
                <div className="w-full bg-[var(--accent)] opacity-20 hover:opacity-100 transition-opacity rounded-t-sm" style={{ height: `${val}%` }} />
              </div>
            ))}
          </div>
          <div className="flex justify-between mt-2 text-[10px] font-mono text-[var(--text-secondary)]">
            <span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span><span>Fri</span><span>Sat</span><span>Sun</span>
          </div>
        </div>

        <div className="bg-[var(--bg-surface)] border border-[var(--border)] rounded-xl p-4">
          <h2 className="text-sm font-medium mb-4">Top Skills in Market</h2>
          <div className="space-y-3">
            {[
              { name: 'Python', pct: 85 },
              { name: 'React', pct: 72 },
              { name: 'AWS', pct: 64 },
              { name: 'TypeScript', pct: 58 },
              { name: 'SQL', pct: 45 },
            ].map(skill => (
              <div key={skill.name} className="flex items-center gap-3 text-xs">
                <span className="w-20 font-mono text-[var(--text-secondary)]">{skill.name}</span>
                <div className="flex-1 h-1.5 bg-[var(--bg-elevated)] rounded-full overflow-hidden">
                  <div className="h-full bg-[var(--accent-cyan)] rounded-full" style={{ width: `${skill.pct}%` }} />
                </div>
                <span className="w-8 text-right font-mono text-[var(--text-secondary)]">{skill.pct}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  </div>
);

const JobBoard = () => {
  const [selectedJob, setSelectedJob] = useState(null);

  // --- AI Feature State ---
  const [aiResponse, setAiResponse] = useState("");
  const [isAiLoading, setIsAiLoading] = useState(false);
  const [aiError, setAiError] = useState("");
  const [activeAiTab, setActiveAiTab] = useState("");

  const handleAITool = async (toolType, job) => {
    setIsAiLoading(true);
    setAiError("");
    setAiResponse("");
    setActiveAiTab(toolType);

    let prompt = "";
    if (toolType === "coverLetter") {
      prompt = `Write a compelling, concise cover letter for the position of ${job.title} at ${job.company}. Job description highlights: ${job.summary}. Tech stack: ${job.tech_stack.join(', ')}. The tone should be professional, confident, and direct. Skip the address headers and keep it under 3 short paragraphs.`;
    } else if (toolType === "interviewPrep") {
      prompt = `I have an interview for ${job.title} at ${job.company}. Their tech stack is ${job.tech_stack.join(', ')}. Job description: ${job.summary}. Give me 3 highly specific technical interview questions and 2 behavioral questions tailored to this exact role, along with a 1-sentence tip on how to answer each. Use simple formatting.`;
    } else if (toolType === "gapAnalysis") {
      prompt = `Analyze the gap between a candidate with general software engineering experience and this specific role: ${job.title} at ${job.company}. Tech stack: ${job.tech_stack.join(', ')}. Job summary: ${job.summary}. What are the top 3 hidden requirements or challenges of this role that a candidate should bridge before applying? Keep it brief and actionable.`;
    }

    try {
      const result = await callGeminiAPI(prompt);
      setAiResponse(result);
    } catch (err) {
      setAiError("Failed to connect to AI copilot. Please try again.");
    } finally {
      setIsAiLoading(false);
    }
  };

  // Reset AI state when switching jobs
  useEffect(() => {
    setAiResponse("");
    setIsAiLoading(false);
    setAiError("");
    setActiveAiTab("");
  }, [selectedJob]);

  return (
    <div className="flex h-full animate-in fade-in duration-300">
      {/* FILTER PANEL */}
      <div className="w-[280px] border-r border-[var(--border)] bg-[var(--bg-surface)] overflow-y-auto hidden lg:block p-4 space-y-6">
        <div>
          <h3 className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-3">Search</h3>
          <div className="relative">
            <Search className="absolute left-3 top-2.5 text-[var(--text-secondary)]" size={14} />
            <input type="text" placeholder="Keywords, titles..." className="w-full bg-[var(--bg-base)] border border-[var(--border)] rounded-md py-2 pl-9 pr-3 text-sm focus:outline-none focus:border-[var(--accent)] text-[var(--text-primary)] transition-colors" />
          </div>
        </div>

        <div>
          <h3 className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-3">Sources</h3>
          <div className="space-y-2">
            {['Greenhouse', 'Lever', 'Ashby', 'Google Jobs', 'JobSpy'].map(src => (
              <label key={src} className="flex items-center gap-2 text-sm cursor-pointer group">
                <div className="w-4 h-4 rounded border border-[var(--border)] flex items-center justify-center group-hover:border-[var(--accent)] transition-colors bg-[var(--bg-base)]">
                  <Check size={10} className="opacity-0 group-hover:opacity-50" />
                </div>
                <span className="text-[var(--text-secondary)] group-hover:text-white transition-colors">{src}</span>
              </label>
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-3">Experience</h3>
          <div className="flex flex-wrap gap-2">
            {['Entry', 'Mid', 'Senior', 'Exec'].map(lvl => (
              <button key={lvl} className={`px-3 py-1 text-xs rounded-full border border-[var(--border)] ${lvl === 'Mid' || lvl === 'Senior' ? 'bg-[var(--accent)]/20 text-[var(--accent)] border-[var(--accent)]/50' : 'text-[var(--text-secondary)] hover:bg-[var(--bg-elevated)]'}`}>
                {lvl}
              </button>
            ))}
          </div>
        </div>
        
        <div>
          <h3 className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-3">Match Score</h3>
          <div className="px-2">
            <input type="range" className="w-full accent-[var(--accent)]" min="0" max="100" defaultValue="70" />
            <div className="flex justify-between text-[10px] font-mono text-[var(--text-secondary)] mt-1">
              <span>0%</span><span>&gt; 70%</span>
            </div>
          </div>
        </div>
      </div>

      {/* MAIN LIST */}
      <div className="flex-1 flex flex-col min-w-0">
        <div className="h-14 border-b border-[var(--border)] flex items-center justify-between px-6 bg-[var(--bg-surface)]">
          <div className="flex items-center gap-3 text-sm text-[var(--text-secondary)]">
            <span className="font-mono text-[var(--text-primary)]">1,402</span> matching jobs
          </div>
          <div className="flex items-center gap-4 text-sm">
            <span className="text-[var(--text-secondary)]">Sort by:</span>
            <select className="bg-transparent border-none text-[var(--text-primary)] focus:outline-none cursor-pointer">
              <option>Match Score</option>
              <option>Date Posted</option>
              <option>Date Scraped</option>
            </select>
          </div>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {MOCK_JOBS.map((job) => (
            <div key={job.id} 
              onClick={() => setSelectedJob(job)}
              className={`p-4 border rounded-lg cursor-pointer transition-all flex items-center justify-between group
                ${selectedJob?.id === job.id ? 'bg-[var(--bg-elevated)] border-[var(--accent)]' : 'bg-[var(--bg-surface)] border-[var(--border)] hover:border-[var(--text-secondary)]'}`}>
              
              <div className="flex items-center gap-4 w-1/2">
                 <img src={`https://logo.clearbit.com/${job.domain}`} alt="" className="w-12 h-12 rounded bg-black p-1 object-contain shrink-0" onError={(e) => e.target.style.display='none'} />
                 <div className="min-w-0">
                   <h3 className="font-semibold truncate text-[var(--text-primary)]">{job.title}</h3>
                   <div className="flex items-center gap-2 text-xs mt-1 text-[var(--text-secondary)]">
                     <Briefcase size={12}/> <span className="truncate">{job.company}</span>
                     <span className="w-1 h-1 rounded-full bg-[var(--border)] shrink-0" />
                     <MapPin size={12}/> <span className="truncate">{job.location}</span>
                   </div>
                 </div>
              </div>

              <div className="flex items-center gap-6 justify-end w-1/2">
                <div className="hidden xl:flex gap-1">
                  {job.tech_stack.map(t => (
                    <span key={t} className="px-2 py-1 text-[10px] font-mono rounded bg-[var(--bg-elevated)] text-[var(--accent)] border border-[var(--accent)]/20">{t}</span>
                  ))}
                </div>
                
                <div className="flex flex-col items-end gap-1 shrink-0 w-24">
                  <span className={`text-[11px] capitalize flex items-center gap-1 ${STATUS_COLORS[job.status] || 'text-white'}`}>
                    <div className="w-1.5 h-1.5 rounded-full bg-current" /> {job.status}
                  </span>
                  <span className="text-[10px] font-mono text-[var(--text-secondary)]">{job.posted_at}</span>
                </div>

                <div className="shrink-0">
                  <ScoreRing score={job.match_score} size={44} strokeWidth={4} />
                </div>
                
                <button className="text-[var(--text-secondary)] hover:text-yellow-400 opacity-0 group-hover:opacity-100 transition-all">
                  <Star size={18} />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* DETAIL PANEL (Slide-over) */}
      {selectedJob && (
        <div className="w-[480px] bg-[var(--bg-surface)] border-l border-[var(--border)] flex flex-col shadow-2xl animate-in slide-in-from-right-8 z-10 shrink-0">
          <div className="p-4 border-b border-[var(--border)] flex justify-between items-start sticky top-0 bg-[var(--bg-surface)] z-20">
            <div className="flex gap-4">
              <img src={`https://logo.clearbit.com/${selectedJob.domain}`} alt="" className="w-14 h-14 rounded-lg bg-white p-1 object-contain" onError={(e) => e.target.style.display='none'} />
              <div>
                <h2 className="font-bold text-lg leading-tight">{selectedJob.title}</h2>
                <div className="text-[var(--text-secondary)] text-sm flex items-center gap-2 mt-1">
                  {selectedJob.company} • {selectedJob.location}
                </div>
                {selectedJob.salary && (
                  <div className="text-[var(--accent-green)] font-mono text-xs mt-2 bg-[var(--accent-green)]/10 inline-block px-2 py-1 rounded border border-[var(--accent-green)]/20">
                    {selectedJob.salary}
                  </div>
                )}
              </div>
            </div>
            <button onClick={() => setSelectedJob(null)} className="text-[var(--text-secondary)] hover:text-white bg-[var(--bg-base)] p-1 rounded-full border border-[var(--border)]">
              <XCircle size={20} />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-6 space-y-8">
            
            {/* Status Selector */}
            <div>
              <label className="text-xs font-mono text-[var(--text-secondary)] uppercase mb-2 block">Application Status</label>
              <div className="flex flex-wrap gap-2">
                {['new', 'saved', 'applied', 'interviewing', 'offer', 'rejected'].map(s => (
                  <button key={s} className={`px-3 py-1.5 text-xs rounded-full border capitalize transition-colors
                    ${selectedJob.status === s 
                      ? 'bg-[var(--text-primary)] text-black border-[var(--text-primary)] font-medium' 
                      : 'border-[var(--border)] text-[var(--text-secondary)] hover:border-[var(--text-primary)] hover:text-[var(--text-primary)]'}`}>
                    {s}
                  </button>
                ))}
              </div>
            </div>

            {/* ✨ AI Toolkit */}
            <div className="bg-[var(--bg-elevated)] border border-[var(--border)] rounded-xl p-4 shadow-inner">
              <label className="text-xs font-mono text-[var(--accent)] flex items-center gap-2 mb-3">
                <Sparkles size={14} /> AI Copilot Tools
              </label>
              <div className="flex flex-wrap gap-2 mb-2">
                <button 
                  onClick={() => handleAITool('coverLetter', selectedJob)}
                  disabled={isAiLoading}
                  className="px-3 py-1.5 text-xs rounded-md border border-[var(--accent)]/30 bg-[var(--accent)]/10 text-[var(--accent)] hover:bg-[var(--accent)]/20 transition-colors flex items-center gap-1.5 disabled:opacity-50"
                >
                  <Sparkles size={12} /> Draft Cover Letter
                </button>
                <button 
                  onClick={() => handleAITool('interviewPrep', selectedJob)}
                  disabled={isAiLoading}
                  className="px-3 py-1.5 text-xs rounded-md border border-[var(--accent-cyan)]/30 bg-[var(--accent-cyan)]/10 text-[var(--accent-cyan)] hover:bg-[var(--accent-cyan)]/20 transition-colors flex items-center gap-1.5 disabled:opacity-50"
                >
                  <MessageSquare size={12} /> Interview Prep
                </button>
                <button 
                  onClick={() => handleAITool('gapAnalysis', selectedJob)}
                  disabled={isAiLoading}
                  className="px-3 py-1.5 text-xs rounded-md border border-[var(--accent-amber)]/30 bg-[var(--accent-amber)]/10 text-[var(--accent-amber)] hover:bg-[var(--accent-amber)]/20 transition-colors flex items-center gap-1.5 disabled:opacity-50"
                >
                  <Activity size={12} /> Gap Analysis
                </button>
              </div>

              {/* AI Output Area */}
              {(isAiLoading || aiResponse || aiError) && (
                <div className="mt-4 p-4 rounded-lg bg-[var(--bg-base)] border border-[var(--border)] relative overflow-hidden group">
                  {isAiLoading && (
                    <div className="flex items-center gap-2 text-[var(--text-secondary)] text-sm font-mono animate-pulse">
                      <Loader2 size={14} className="animate-spin text-[var(--accent)]" /> 
                      Synthesizing intelligence...
                    </div>
                  )}
                  {aiError && (
                    <div className="text-[var(--accent-red)] text-sm flex items-center gap-2">
                      <AlertCircle size={14} /> {aiError}
                    </div>
                  )}
                  {aiResponse && !isAiLoading && (
                    <div className="text-[var(--text-primary)] leading-relaxed whitespace-pre-wrap font-mono text-[11px] max-h-64 overflow-y-auto pr-8 custom-scrollbar">
                      {aiResponse}
                      <button 
                        onClick={() => {
                          try {
                            document.execCommand('copy'); // Fallback for iFrames
                            navigator.clipboard.writeText(aiResponse);
                          } catch (e) {}
                        }}
                        className="absolute top-2 right-2 p-1.5 rounded-md bg-[var(--bg-elevated)] border border-[var(--border)] text-[var(--text-secondary)] hover:text-white transition-colors opacity-0 group-hover:opacity-100"
                        title="Copy to clipboard"
                      >
                        <Copy size={12} />
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* AI Summary */}
            <div className="bg-[var(--bg-base)] border border-[var(--border)] rounded-xl p-4 relative overflow-hidden">
              <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-[var(--accent)] to-[var(--accent-cyan)]" />
              <label className="text-xs font-mono text-[var(--accent)] flex items-center gap-2 mb-2">
                <Target size={12} /> AI Summary
              </label>
              <p className="text-sm text-[var(--text-primary)] leading-relaxed">
                {selectedJob.summary}
              </p>
              
              <div className="flex gap-4 mt-4 pt-4 border-t border-[var(--border)]">
                <div className="flex-1">
                  <span className="text-[10px] uppercase text-[var(--accent-green)] block mb-1 font-semibold">Green Flags</span>
                  <ul className="text-xs text-[var(--text-secondary)] space-y-1">
                    {selectedJob.flags.green.map((f,i) => <li key={i} className="flex gap-1"><CheckCircle2 size={12} className="text-[var(--accent-green)] shrink-0"/> {f}</li>)}
                  </ul>
                </div>
                <div className="flex-1">
                  <span className="text-[10px] uppercase text-[var(--accent-red)] block mb-1 font-semibold">Red Flags</span>
                  <ul className="text-xs text-[var(--text-secondary)] space-y-1">
                    {selectedJob.flags.red.map((f,i) => <li key={i} className="flex gap-1"><AlertCircle size={12} className="text-[var(--accent-red)] shrink-0"/> {f}</li>)}
                    {selectedJob.flags.red.length === 0 && <li className="text-[10px] italic">None detected</li>}
                  </ul>
                </div>
              </div>
            </div>

            {/* Match Score Detail */}
            <div className="flex items-center gap-6 p-4 border border-[var(--border)] rounded-xl bg-[var(--bg-elevated)]">
              <ScoreRing score={selectedJob.match_score} size={64} strokeWidth={6} />
              <div>
                <h4 className="font-semibold text-sm">Strong Match</h4>
                <p className="text-xs text-[var(--text-secondary)] mt-1">Your resume's embedding strongly aligns with the required skills: <span className="text-white">Python, Machine Learning, Scalability</span>.</p>
              </div>
            </div>

            {/* Mock Description */}
            <div>
              <h3 className="text-sm font-semibold mb-3">Job Description</h3>
              <div className="text-sm text-[var(--text-secondary)] space-y-4 leading-relaxed bg-[var(--bg-base)] p-4 rounded-lg border border-[var(--border)]">
                <p>We are seeking an experienced {selectedJob.title} to join our world-class engineering team. You will be responsible for designing, building, and maintaining core infrastructure...</p>
                <p className="blur-[2px] select-none">Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam.</p>
                <div className="flex items-center gap-2 text-[var(--accent)] font-mono text-xs cursor-pointer">
                  <Eye size={14}/> Reveal full description
                </div>
              </div>
            </div>

          </div>

          {/* Footer Actions */}
          <div className="p-4 border-t border-[var(--border)] bg-[var(--bg-surface)] flex gap-3">
            <button className="flex-1 bg-white hover:bg-gray-200 text-black py-2.5 rounded-lg text-sm font-semibold transition-colors flex justify-center items-center gap-2">
              Apply Now <ExternalLink size={16}/>
            </button>
            <button className="px-4 py-2 border border-[var(--border)] hover:bg-[var(--bg-elevated)] rounded-lg text-[var(--text-secondary)] hover:text-white transition-colors">
              <Copy size={16} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

const Pipeline = () => {
  // Group jobs for Kanban
  const cols = KANBAN_COLUMNS.reduce((acc, col) => {
    const key = col.toLowerCase().replace(' ', '');
    // fuzzy map status to column for mockup
    acc[col] = MOCK_JOBS.filter(j => 
      (j.status === key) || 
      (key === 'applied' && j.status === 'applied') ||
      (key === 'interview' && j.status === 'interviewing') ||
      (key === 'offer' && j.status === 'offer') ||
      (key === 'rejected' && j.status === 'rejected')
    );
    return acc;
  }, {});

  return (
    <div className="h-full flex flex-col p-6 animate-in fade-in duration-300">
      <div className="mb-6 flex justify-between items-end">
        <div>
          <h1 className="text-xl font-bold">Application Pipeline</h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">Drag and drop to update status</p>
        </div>
        <button className="bg-[var(--bg-elevated)] border border-[var(--border)] px-4 py-2 rounded-lg text-sm flex items-center gap-2 hover:bg-[var(--border)] transition-colors">
          <Filter size={16}/> Filter Board
        </button>
      </div>

      <div className="flex-1 overflow-x-auto flex gap-4 pb-4 snap-x">
        {KANBAN_COLUMNS.map(col => (
          <div key={col} className="w-[300px] shrink-0 flex flex-col bg-[var(--bg-base)] border border-[var(--border)] rounded-xl overflow-hidden snap-start">
            <div className="p-3 border-b border-[var(--border)] bg-[var(--bg-surface)] flex justify-between items-center">
              <span className="font-semibold text-sm">{col}</span>
              <span className="bg-[var(--bg-elevated)] text-[var(--text-secondary)] px-2 py-0.5 rounded text-xs font-mono">
                {cols[col].length}
              </span>
            </div>
            
            <div className="flex-1 overflow-y-auto p-3 space-y-3 bg-[var(--bg-base)]">
              {cols[col].length === 0 ? (
                <div className="h-24 border-2 border-dashed border-[var(--border)] rounded-lg flex items-center justify-center text-xs text-[var(--text-secondary)] italic">
                  Drop here
                </div>
              ) : (
                cols[col].map(job => (
                  <div key={job.id} className="bg-[var(--bg-surface)] border border-[var(--border)] rounded-lg p-3 hover:border-[var(--accent)] cursor-grab active:cursor-grabbing transition-colors group">
                    <div className="flex gap-3 mb-2">
                      <img src={`https://logo.clearbit.com/${job.domain}`} alt="" className="w-8 h-8 rounded bg-white p-0.5 object-contain" onError={(e) => e.target.style.display='none'} />
                      <div className="min-w-0 flex-1">
                        <h4 className="text-sm font-semibold truncate leading-tight">{job.title}</h4>
                        <span className="text-xs text-[var(--text-secondary)] truncate block">{job.company}</span>
                      </div>
                    </div>
                    <div className="flex justify-between items-center mt-3 pt-3 border-t border-[var(--border)]">
                      <span className="text-[10px] font-mono text-[var(--text-secondary)]">{job.posted_at}</span>
                      <ScoreRing score={job.match_score} size={24} strokeWidth={2} />
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const Analytics = () => (
  <div className="p-6 overflow-y-auto h-full space-y-6 animate-in fade-in duration-300">
    <h1 className="text-xl font-bold mb-6">Analytics & Insights</h1>
    
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Funnel */}
      <div className="bg-[var(--bg-surface)] border border-[var(--border)] rounded-xl p-5">
        <h3 className="text-sm font-medium mb-6">Application Funnel</h3>
        <div className="flex flex-col gap-2 items-center">
          {[
            { label: 'Saved', val: 142, w: '100%', color: 'var(--text-secondary)' },
            { label: 'Applied', val: 48, w: '80%', color: 'var(--accent-cyan)' },
            { label: 'Interviewing', val: 12, w: '50%', color: 'var(--accent)' },
            { label: 'Offers', val: 2, w: '20%', color: 'var(--accent-green)' },
          ].map((step, i) => (
            <div key={i} className="flex flex-col items-center w-full">
              <div className="flex justify-between w-full text-xs mb-1 px-4 text-[var(--text-secondary)]">
                <span>{step.label}</span>
                <span className="font-mono">{step.val}</span>
              </div>
              <div className="h-8 rounded-sm transition-all flex items-center justify-center font-mono text-[10px] bg-opacity-20 relative overflow-hidden group" style={{ width: step.w, backgroundColor: step.color }}>
                <div className="absolute inset-0 opacity-20 mix-blend-overlay" style={{ backgroundColor: step.color }} />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Heatmap Mock */}
      <div className="bg-[var(--bg-surface)] border border-[var(--border)] rounded-xl p-5">
        <h3 className="text-sm font-medium mb-4">Skills Trending (Last 4 Weeks)</h3>
        <div className="space-y-2">
          {['Python', 'React', 'TypeScript', 'LLMs', 'PyTorch'].map((skill, rowIdx) => (
            <div key={skill} className="flex items-center gap-2">
              <span className="w-20 text-xs font-mono text-[var(--text-secondary)]">{skill}</span>
              <div className="flex flex-1 gap-1">
                {[1, 2, 3, 4].map(colIdx => {
                  const intensity = Math.random();
                  return (
                    <div key={colIdx} className="h-6 flex-1 rounded-sm" 
                         style={{ backgroundColor: `rgba(123, 97, 255, ${0.1 + intensity * 0.9})` }} 
                         title={`${Math.floor(intensity * 100)} jobs`} />
                  )
                })}
              </div>
            </div>
          ))}
          <div className="flex ml-22 gap-1 mt-2 text-[10px] font-mono text-[var(--text-secondary)]">
            <span className="flex-1 text-center">Wk 1</span>
            <span className="flex-1 text-center">Wk 2</span>
            <span className="flex-1 text-center">Wk 3</span>
            <span className="flex-1 text-center">This Wk</span>
          </div>
        </div>
      </div>
    </div>
  </div>
);

const Settings = () => (
  <div className="max-w-4xl mx-auto p-6 animate-in fade-in duration-300">
    <h1 className="text-xl font-bold mb-6">Settings</h1>
    
    <div className="flex gap-8">
      {/* Settings Nav */}
      <div className="w-48 space-y-1">
        {['API Keys', 'Scraper Config', 'Resume', 'Appearance'].map((tab, i) => (
          <button key={tab} className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${i===0 ? 'bg-[var(--bg-elevated)] text-[var(--text-primary)] font-medium border border-[var(--border)]' : 'text-[var(--text-secondary)] hover:text-white hover:bg-[var(--bg-elevated)] border border-transparent'}`}>
            {tab}
          </button>
        ))}
      </div>

      {/* Settings Content (API Keys Mock) */}
      <div className="flex-1 space-y-8">
        
        <section className="bg-[var(--bg-surface)] border border-[var(--border)] rounded-xl p-6">
          <h2 className="text-base font-medium mb-4 flex items-center gap-2 border-b border-[var(--border)] pb-3">
            <TerminalSquare size={18}/> Scraping APIs
          </h2>
          <div className="space-y-4">
            <div>
              <label className="text-xs text-[var(--text-secondary)] block mb-1">SerpApi Key (Primary - Google Jobs)</label>
              <div className="flex gap-2">
                <input type="password" value="sk-1234567890abcdef" readOnly className="flex-1 bg-[var(--bg-base)] border border-[var(--border)] rounded-md px-3 py-2 font-mono text-sm focus:border-[var(--accent)] outline-none" />
                <button className="px-4 bg-[var(--bg-elevated)] border border-[var(--border)] rounded-md text-sm hover:text-[var(--accent-green)] transition-colors">Test</button>
              </div>
            </div>
            <div>
              <label className="text-xs text-[var(--text-secondary)] block mb-1">TheirStack Key (Optional)</label>
              <input type="text" placeholder="sk-..." className="w-full bg-[var(--bg-base)] border border-[var(--border)] rounded-md px-3 py-2 font-mono text-sm focus:border-[var(--accent)] outline-none" />
            </div>
          </div>
        </section>

        <section className="bg-[var(--bg-surface)] border border-[var(--border)] rounded-xl p-6">
          <h2 className="text-base font-medium mb-4 flex items-center gap-2 border-b border-[var(--border)] pb-3">
            <Target size={18}/> LLM Enrichment
          </h2>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-[var(--text-secondary)] block mb-1">Ollama Base URL</label>
                <input type="text" defaultValue="http://localhost:11434" className="w-full bg-[var(--bg-base)] border border-[var(--border)] rounded-md px-3 py-2 font-mono text-sm outline-none" />
              </div>
              <div>
                <label className="text-xs text-[var(--text-secondary)] block mb-1">Local Model</label>
                <input type="text" defaultValue="qwen2.5:7b" className="w-full bg-[var(--bg-base)] border border-[var(--border)] rounded-md px-3 py-2 font-mono text-sm outline-none" />
              </div>
            </div>
            <div>
              <label className="text-xs text-[var(--text-secondary)] block mb-1">OpenAI API Key (Fallback)</label>
              <input type="password" placeholder="sk-proj-..." className="w-full bg-[var(--bg-base)] border border-[var(--border)] rounded-md px-3 py-2 font-mono text-sm outline-none" />
            </div>
          </div>
        </section>

        <div className="flex justify-end">
          <button className="bg-white hover:bg-gray-200 text-black px-6 py-2 rounded-lg text-sm font-semibold flex items-center gap-2 transition-all">
            <Save size={16}/> Save Configuration
          </button>
        </div>

      </div>
    </div>
  </div>
);


export default function App() {
  const [currentPage, setCurrentPage] = useState('dashboard');

  const navItems = [
    { id: 'dashboard', icon: LayoutGrid, label: 'Dashboard' },
    { id: 'jobs', icon: List, label: 'Job Board' },
    { id: 'pipeline', icon: KanbanSquare, label: 'Pipeline' },
    { id: 'analytics', icon: BarChart3, label: 'Analytics' },
    { id: 'settings', icon: SettingsIcon, label: 'Settings' },
  ];

  return (
    <div className="h-screen flex overflow-hidden text-[var(--text-primary)]">
      <StyleSystem />

      {/* SIDEBAR */}
      <div className="w-[240px] bg-[var(--bg-surface)] border-r border-[var(--border)] flex flex-col z-20 shrink-0">
        <div className="h-14 flex items-center px-6 border-b border-[var(--border)]">
          <div className="flex items-center gap-3">
            <div className="relative flex items-center justify-center w-6 h-6 bg-white text-black rounded-md">
              <span className="font-bold text-lg leading-none tracking-tighter" style={{ fontFamily: 'var(--font-mono)' }}>JR</span>
            </div>
            <span className="font-bold tracking-wide text-[var(--text-primary)]">JobRadar</span>
          </div>
        </div>

        <nav className="flex-1 py-6 px-3 space-y-1">
          {navItems.map(item => (
            <button
              key={item.id}
              onClick={() => setCurrentPage(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200
                ${currentPage === item.id 
                  ? 'bg-[var(--bg-elevated)] text-[var(--text-primary)] font-medium border border-[var(--border)]' 
                  : 'text-[var(--text-secondary)] hover:bg-[var(--bg-elevated)] hover:text-[var(--text-primary)] border border-transparent'}`}
            >
              <item.icon size={18} />
              {item.label}
            </button>
          ))}
        </nav>

        <div className="p-4 border-t border-[var(--border)] bg-[var(--bg-base)]/50">
          <div className="flex items-center justify-between text-xs text-[var(--text-secondary)]">
            <span className="font-mono">v0.1.0</span>
            <span className="flex items-center gap-1 bg-[var(--bg-elevated)] px-2 py-1 rounded border border-[var(--border)]">
              Local Only 🔒
            </span>
          </div>
        </div>
      </div>

      {/* MAIN LAYOUT */}
      <div className="flex-1 flex flex-col min-w-0">
        
        {/* TOP BAR */}
        <div className="h-14 bg-[var(--bg-surface)] border-b border-[var(--border)] flex items-center justify-between px-6 shrink-0 z-10">
          <div className="flex items-center gap-4">
            <span className="text-sm font-mono text-[var(--text-secondary)] border-r border-[var(--border)] pr-4 flex items-center gap-2">
              <Activity size={14} className="text-[var(--accent-green)]"/> 
              <span className="text-[var(--text-primary)]">12,847</span> jobs
            </span>
            <span className="text-xs font-mono text-[var(--accent-green)] flex items-center gap-1.5 bg-[var(--accent-green)]/10 border border-[var(--accent-green)]/20 px-2 py-0.5 rounded-full">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-green)] animate-pulse"></span>
              Live: 2 scrapers
            </span>
          </div>
          
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-xs bg-[var(--bg-elevated)] border border-[var(--border)] rounded-full px-3 py-1.5 shadow-inner">
              <UploadCloud size={14} className="text-[var(--text-secondary)]" />
              <span className="text-[var(--text-secondary)]">Resume:</span>
              <span className="text-[var(--accent-green)] flex items-center gap-1">
                <CheckCircle2 size={12}/> Active
              </span>
            </div>
          </div>
        </div>

        {/* CONTENT AREA */}
        <div className="flex-1 overflow-hidden bg-[var(--bg-base)] relative">
          {currentPage === 'dashboard' && <Dashboard />}
          {currentPage === 'jobs' && <JobBoard />}
          {currentPage === 'pipeline' && <Pipeline />}
          {currentPage === 'analytics' && <Analytics />}
          {currentPage === 'settings' && <Settings />}
        </div>

      </div>

      {/* FLOATING DRAWER */}
      <ScraperLogDrawer />
    </div>
  );
}