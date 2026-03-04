import { useState, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Eye, EyeOff, Save, UploadCloud, Play, Loader2 } from 'lucide-react'
import { fetchSettings, updateSettings, uploadResume, triggerScraper } from '../api/client'
import { cn } from '../lib/utils'
import toast from 'react-hot-toast'

type Tab = 'keys' | 'scraper' | 'resume' | 'appearance'

export default function Settings() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<Tab>('keys')

  const { data: settings, isLoading } = useQuery({
    queryKey: ['settings'],
    queryFn: fetchSettings,
  })

  const mutation = useMutation({
    mutationFn: updateSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] })
      toast.success('Settings saved')
    },
    onError: () => toast.error('Failed to save settings'),
  })

  const tabs: { id: Tab; label: string }[] = [
    { id: 'keys', label: 'API Keys' },
    { id: 'scraper', label: 'Scraper Config' },
    { id: 'resume', label: 'Resume' },
  ]

  if (isLoading || !settings) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-text-secondary">Loading settings...</div>
      </div>
    )
  }

  return (
    <div className="max-w-3xl">
      <h1 className="text-lg font-semibold mb-4">Settings</h1>

      {/* Tabs */}
      <div className="flex border-b border-border mb-6">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              'px-4 py-2 text-sm font-medium transition-colors',
              activeTab === tab.id
                ? 'text-accent border-b-2 border-accent'
                : 'text-text-secondary hover:text-text-primary'
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'keys' && <APIKeysTab settings={settings} onSave={mutation.mutate} />}
      {activeTab === 'scraper' && <ScraperConfigTab settings={settings} onSave={mutation.mutate} />}
      {activeTab === 'resume' && <ResumeTab settings={settings} />}
    </div>
  )
}

// --- API Keys Tab ---
function APIKeysTab({ settings, onSave }: { settings: any; onSave: (data: any) => void }) {
  const [keys, setKeys] = useState({
    serpapi_key: '',
    theirstack_key: '',
    apify_key: '',
    openrouter_api_key: '',
    openrouter_primary_model: settings.openrouter_primary_model,
    openrouter_fallback_model: settings.openrouter_fallback_model,
  })
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({})

  const fields = [
    { key: 'serpapi_key', label: 'SerpApi Key', set: settings.serpapi_key_set, required: true },
    { key: 'openrouter_api_key', label: 'OpenRouter API Key', set: settings.openrouter_key_set, required: true },
    { key: 'theirstack_key', label: 'TheirStack Key', set: settings.theirstack_key_set, required: false },
    { key: 'apify_key', label: 'Apify Key', set: settings.apify_key_set, required: false },
  ]

  return (
    <div className="space-y-4">
      {fields.map((field) => (
        <div key={field.key}>
          <label className="text-xs font-semibold text-text-secondary uppercase flex items-center gap-2">
            {field.label}
            {field.required && <span className="text-accent-red">*</span>}
            {field.set && <span className="text-accent-green text-[10px]">(configured)</span>}
          </label>
          <div className="relative mt-1">
            <input
              type={showKeys[field.key] ? 'text' : 'password'}
              placeholder={field.set ? '••••••••' : 'Enter key...'}
              value={(keys as any)[field.key]}
              onChange={(e) => setKeys((prev) => ({ ...prev, [field.key]: e.target.value }))}
              className="w-full bg-elevated border border-border rounded-lg px-3 py-2 pr-10 text-sm text-text-primary placeholder:text-text-secondary focus:outline-none focus:border-accent"
            />
            <button
              onClick={() => setShowKeys((prev) => ({ ...prev, [field.key]: !prev[field.key] }))}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-text-secondary"
            >
              {showKeys[field.key] ? <EyeOff size={14} /> : <Eye size={14} />}
            </button>
          </div>
        </div>
      ))}

      {/* Model selectors */}
      <div>
        <label className="text-xs font-semibold text-text-secondary uppercase">Primary Model</label>
        <input
          type="text"
          value={keys.openrouter_primary_model}
          onChange={(e) => setKeys((prev) => ({ ...prev, openrouter_primary_model: e.target.value }))}
          className="w-full mt-1 bg-elevated border border-border rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-accent"
        />
      </div>
      <div>
        <label className="text-xs font-semibold text-text-secondary uppercase">Fallback Model</label>
        <input
          type="text"
          value={keys.openrouter_fallback_model}
          onChange={(e) => setKeys((prev) => ({ ...prev, openrouter_fallback_model: e.target.value }))}
          className="w-full mt-1 bg-elevated border border-border rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-accent"
        />
      </div>

      <button
        onClick={() => {
          const data: Record<string, string> = {}
          Object.entries(keys).forEach(([k, v]) => {
            if (v) data[k] = v
          })
          onSave(data)
        }}
        className="flex items-center gap-2 px-4 py-2 bg-accent text-white rounded-lg text-sm font-medium hover:bg-accent/90"
      >
        <Save size={14} /> Save API Keys
      </button>
    </div>
  )
}

// --- Scraper Config Tab ---
function ScraperConfigTab({ settings, onSave }: { settings: any; onSave: (data: any) => void }) {
  const [queries, setQueries] = useState<string>(
    (settings.default_queries || []).join('\n')
  )
  const [locations, setLocations] = useState<string>(
    (settings.default_locations || []).join('\n')
  )
  const [watchlist, setWatchlist] = useState<string>(
    (settings.company_watchlist || []).join('\n')
  )
  const [isRunning, setIsRunning] = useState(false)

  const handleRunAll = async () => {
    setIsRunning(true)
    try {
      await triggerScraper('all')
      toast.success('Scraping started')
    } catch {
      toast.error('Failed to start scrapers')
    }
    setIsRunning(false)
  }

  return (
    <div className="space-y-4">
      <div>
        <label className="text-xs font-semibold text-text-secondary uppercase">
          Search Queries (one per line)
        </label>
        <textarea
          value={queries}
          onChange={(e) => setQueries(e.target.value)}
          rows={4}
          className="w-full mt-1 bg-elevated border border-border rounded-lg px-3 py-2 text-sm text-text-primary placeholder:text-text-secondary focus:outline-none focus:border-accent resize-none"
        />
      </div>

      <div>
        <label className="text-xs font-semibold text-text-secondary uppercase">
          Target Locations (one per line)
        </label>
        <textarea
          value={locations}
          onChange={(e) => setLocations(e.target.value)}
          rows={3}
          className="w-full mt-1 bg-elevated border border-border rounded-lg px-3 py-2 text-sm text-text-primary placeholder:text-text-secondary focus:outline-none focus:border-accent resize-none"
        />
      </div>

      <div>
        <label className="text-xs font-semibold text-text-secondary uppercase">
          Company Watchlist (ATS slugs, one per line)
        </label>
        <textarea
          value={watchlist}
          onChange={(e) => setWatchlist(e.target.value)}
          rows={4}
          placeholder="openai&#10;anthropic&#10;stripe&#10;vercel"
          className="w-full mt-1 bg-elevated border border-border rounded-lg px-3 py-2 text-sm text-text-primary placeholder:text-text-secondary focus:outline-none focus:border-accent resize-none"
        />
      </div>

      <div className="flex gap-3 pt-2">
        <button
          onClick={() =>
            onSave({
              default_queries: queries.split('\n').filter(Boolean),
              default_locations: locations.split('\n').filter(Boolean),
              company_watchlist: watchlist.split('\n').filter(Boolean),
            })
          }
          className="flex items-center gap-2 px-4 py-2 bg-accent text-white rounded-lg text-sm font-medium hover:bg-accent/90"
        >
          <Save size={14} /> Save Config
        </button>

        <button
          onClick={handleRunAll}
          disabled={isRunning}
          className="flex items-center gap-2 px-4 py-2 border border-accent-green text-accent-green rounded-lg text-sm font-medium hover:bg-accent-green/10 disabled:opacity-50"
        >
          {isRunning ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
          Run All Scrapers Now
        </button>
      </div>
    </div>
  )
}

// --- Resume Tab ---
function ResumeTab({ settings }: { settings: any }) {
  const queryClient = useQueryClient()
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)

  const handleUpload = async (file: File) => {
    if (file.size > 5 * 1024 * 1024) {
      toast.error('File too large (max 5MB)')
      return
    }
    setIsUploading(true)
    try {
      await uploadResume(file)
      queryClient.invalidateQueries({ queryKey: ['settings'] })
      toast.success('Resume uploaded and embedded')
    } catch {
      toast.error('Failed to upload resume')
    }
    setIsUploading(false)
  }

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) handleUpload(file)
  }, [])

  return (
    <div className="space-y-4">
      {/* Drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={cn(
          'border-2 border-dashed rounded-xl p-8 text-center transition-colors',
          isDragging ? 'border-accent bg-accent/5' : 'border-border',
          isUploading && 'opacity-50'
        )}
      >
        <UploadCloud size={32} className="mx-auto text-text-secondary mb-3" />
        <p className="text-sm text-text-primary">
          {isUploading ? 'Uploading...' : 'Drop your resume here'}
        </p>
        <p className="text-xs text-text-secondary mt-1">PDF or TXT, max 5MB</p>
        <label className="inline-block mt-3">
          <input
            type="file"
            accept=".pdf,.txt"
            onChange={(e) => {
              const file = e.target.files?.[0]
              if (file) handleUpload(file)
            }}
            className="hidden"
          />
          <span className="px-4 py-2 bg-elevated border border-border rounded-lg text-xs text-text-primary cursor-pointer hover:border-accent">
            Browse Files
          </span>
        </label>
      </div>

      {/* Current resume info */}
      {settings.resume_filename && (
        <div className="bg-elevated border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-medium">{settings.resume_filename}</div>
              <div className="text-xs text-text-secondary mt-0.5">
                Uploaded {settings.resume_uploaded_at ? new Date(settings.resume_uploaded_at).toLocaleDateString() : 'N/A'}
              </div>
            </div>
            <span className="flex items-center gap-1.5 text-xs text-accent-green">
              <span className="w-1.5 h-1.5 rounded-full bg-accent-green" />
              Embedded
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
