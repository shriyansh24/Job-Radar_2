import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  X, ExternalLink, Star, MapPin, Clock, DollarSign,
  CheckCircle2, XCircle, Sparkles, Loader2, Copy,
} from 'lucide-react'
import { fetchJob, updateJob, streamCopilot } from '../../api/client'
import type { Job } from '../../api/client'
import { STATUS_COLORS } from '../../lib/constants'
import { timeAgo, formatSalary, cn } from '../../lib/utils'
import ScoreRing from './ScoreRing'
import JobStatusBadge from './JobStatusBadge'
import toast from 'react-hot-toast'

const STATUSES = ['new', 'saved', 'applied', 'interviewing', 'phone_screen', 'interview', 'final_round', 'offer', 'rejected', 'ghosted']

interface JobDetailPanelProps {
  jobId: string
  onClose: () => void
}

export default function JobDetailPanel({ jobId, onClose }: JobDetailPanelProps) {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<'details' | 'ai'>('details')
  const [copilotOutput, setCopilotOutput] = useState('')
  const [copilotLoading, setCopilotLoading] = useState(false)
  const [notes, setNotes] = useState('')

  const { data: job, isLoading } = useQuery({
    queryKey: ['job', jobId],
    queryFn: () => fetchJob(jobId),
    enabled: !!jobId,
  })

  const mutation = useMutation({
    mutationFn: (data: Partial<Job>) => updateJob(jobId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
      queryClient.invalidateQueries({ queryKey: ['job', jobId] })
    },
  })

  const runCopilot = async (tool: string) => {
    setCopilotLoading(true)
    setCopilotOutput('')
    setActiveTab('ai')
    try {
      for await (const chunk of streamCopilot(tool, jobId)) {
        setCopilotOutput((prev) => prev + chunk)
      }
    } catch (e) {
      setCopilotOutput('Error generating content. Please try again.')
    }
    setCopilotLoading(false)
  }

  if (isLoading || !job) {
    return (
      <div className="w-[480px] h-full bg-surface border-l border-border flex items-center justify-center">
        <div className="text-text-secondary">Loading...</div>
      </div>
    )
  }

  return (
    <div className="w-[480px] h-full bg-surface border-l border-border flex flex-col overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-border flex-shrink-0">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <h2 className="text-lg font-semibold truncate">{job.title}</h2>
            <p className="text-sm text-text-secondary mt-0.5">{job.company_name}</p>
          </div>
          <button onClick={onClose} className="p-1 rounded hover:bg-elevated text-text-secondary">
            <X size={18} />
          </button>
        </div>

        {/* Meta row */}
        <div className="flex items-center gap-3 mt-3 text-xs text-text-secondary">
          {(job.location_city || job.location_state) && (
            <span className="flex items-center gap-1">
              <MapPin size={12} />
              {[job.location_city, job.location_state].filter(Boolean).join(', ')}
            </span>
          )}
          <span className="flex items-center gap-1">
            <Clock size={12} />
            {timeAgo(job.posted_at || job.scraped_at)}
          </span>
          {(job.salary_min || job.salary_max) && (
            <span className="flex items-center gap-1">
              <DollarSign size={12} />
              {formatSalary(job.salary_min, job.salary_max)}
            </span>
          )}
        </div>

        {/* Status selector + actions */}
        <div className="flex items-center gap-2 mt-3">
          <select
            value={job.status}
            onChange={(e) => mutation.mutate({ status: e.target.value })}
            className="bg-elevated border border-border rounded-lg px-2 py-1.5 text-xs text-text-primary focus:outline-none focus:border-accent"
          >
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s.replace('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
              </option>
            ))}
          </select>

          <button
            onClick={() => mutation.mutate({ is_starred: !job.is_starred })}
            className={cn('p-1.5 rounded border border-border', job.is_starred ? 'text-accent-amber' : 'text-text-secondary')}
          >
            <Star size={14} fill={job.is_starred ? 'currentColor' : 'none'} />
          </button>

          <a
            href={job.url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={() => {
              if (job.status === 'new') mutation.mutate({ status: 'applied' })
            }}
            className="ml-auto flex items-center gap-1 px-3 py-1.5 bg-accent text-white rounded-lg text-xs font-medium hover:bg-accent/90"
          >
            Apply <ExternalLink size={12} />
          </a>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border flex-shrink-0">
        <button
          onClick={() => setActiveTab('details')}
          className={cn(
            'flex-1 py-2 text-xs font-medium transition-colors',
            activeTab === 'details'
              ? 'text-accent border-b-2 border-accent'
              : 'text-text-secondary hover:text-text-primary'
          )}
        >
          Details
        </button>
        <button
          onClick={() => setActiveTab('ai')}
          className={cn(
            'flex-1 py-2 text-xs font-medium transition-colors',
            activeTab === 'ai'
              ? 'text-accent border-b-2 border-accent'
              : 'text-text-secondary hover:text-text-primary'
          )}
        >
          AI Copilot
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {activeTab === 'details' ? (
          <>
            {/* Score */}
            {job.match_score !== null && (
              <div className="flex items-center gap-4 p-3 bg-elevated rounded-lg">
                <ScoreRing score={job.match_score} size={64} strokeWidth={4} />
                <div>
                  <div className="text-sm font-medium">Match Score</div>
                  <div className="text-xs text-text-secondary mt-0.5">
                    Based on resume similarity
                  </div>
                </div>
              </div>
            )}

            {/* AI Summary */}
            {job.summary_ai && (
              <div className="p-3 bg-elevated rounded-lg">
                <h3 className="text-xs font-semibold text-text-secondary uppercase mb-2">
                  AI Summary
                </h3>
                <p className="text-sm text-text-primary leading-relaxed">{job.summary_ai}</p>
              </div>
            )}

            {/* Green/Red flags */}
            {(job.green_flags?.length || job.red_flags?.length) ? (
              <div className="grid grid-cols-2 gap-3">
                {job.green_flags?.length ? (
                  <div className="p-3 bg-elevated rounded-lg">
                    <h4 className="text-xs font-semibold text-accent-green mb-2 flex items-center gap-1">
                      <CheckCircle2 size={12} /> Green Flags
                    </h4>
                    <ul className="space-y-1">
                      {job.green_flags.map((f, i) => (
                        <li key={i} className="text-xs text-text-secondary">{f}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                {job.red_flags?.length ? (
                  <div className="p-3 bg-elevated rounded-lg">
                    <h4 className="text-xs font-semibold text-accent-red mb-2 flex items-center gap-1">
                      <XCircle size={12} /> Red Flags
                    </h4>
                    <ul className="space-y-1">
                      {job.red_flags.map((f, i) => (
                        <li key={i} className="text-xs text-text-secondary">{f}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </div>
            ) : null}

            {/* Skills */}
            {job.skills_required?.length ? (
              <div>
                <h3 className="text-xs font-semibold text-text-secondary uppercase mb-2">
                  Required Skills
                </h3>
                <div className="flex flex-wrap gap-1">
                  {job.skills_required.map((skill) => (
                    <span key={skill} className="px-2 py-0.5 text-xs rounded bg-accent/10 text-accent">
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            ) : null}

            {/* Tech stack */}
            {job.tech_stack?.length ? (
              <div>
                <h3 className="text-xs font-semibold text-text-secondary uppercase mb-2">
                  Tech Stack
                </h3>
                <div className="flex flex-wrap gap-1">
                  {job.tech_stack.map((tech) => (
                    <span key={tech} className="px-2 py-0.5 text-xs rounded bg-accent-green/10 text-accent-green">
                      {tech}
                    </span>
                  ))}
                </div>
              </div>
            ) : null}

            {/* Notes */}
            <div>
              <h3 className="text-xs font-semibold text-text-secondary uppercase mb-2">Notes</h3>
              <textarea
                defaultValue={job.notes || ''}
                onBlur={(e) => {
                  if (e.target.value !== (job.notes || '')) {
                    mutation.mutate({ notes: e.target.value })
                  }
                }}
                placeholder="Add notes..."
                className="w-full bg-elevated border border-border rounded-lg px-3 py-2 text-sm text-text-primary placeholder:text-text-secondary focus:outline-none focus:border-accent resize-none"
                rows={3}
              />
            </div>

            {/* Description */}
            {job.description_markdown && (
              <div>
                <h3 className="text-xs font-semibold text-text-secondary uppercase mb-2">
                  Full Description
                </h3>
                <div
                  className="text-sm text-text-secondary leading-relaxed prose prose-invert prose-sm max-w-none"
                  dangerouslySetInnerHTML={{
                    __html: job.description_markdown
                      .replace(/\n/g, '<br/>')
                      .replace(/#{1,3}\s/g, '<strong>')
                  }}
                />
              </div>
            )}

            {/* Metadata footer */}
            <div className="pt-3 border-t border-border text-xs font-mono text-text-secondary space-y-1">
              <div>Source: {job.source}</div>
              <div>Scraped: {new Date(job.scraped_at).toLocaleString()}</div>
              {job.enriched_at && <div>Enriched: {new Date(job.enriched_at).toLocaleString()}</div>}
              <div className="truncate">ID: {job.job_id}</div>
            </div>
          </>
        ) : (
          /* AI Copilot Tab */
          <>
            <div className="space-y-2">
              <h3 className="text-xs font-semibold text-text-secondary uppercase">AI Copilot Tools</h3>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { tool: 'coverLetter', label: 'Cover Letter' },
                  { tool: 'interviewPrep', label: 'Interview Prep' },
                  { tool: 'gapAnalysis', label: 'Gap Analysis' },
                ].map(({ tool, label }) => (
                  <button
                    key={tool}
                    onClick={() => runCopilot(tool)}
                    disabled={copilotLoading}
                    className="flex items-center justify-center gap-1 px-3 py-2 bg-elevated border border-border rounded-lg text-xs text-text-primary hover:border-accent transition-colors disabled:opacity-50"
                  >
                    <Sparkles size={12} />
                    {label}
                  </button>
                ))}
              </div>
            </div>

            {/* Output */}
            <div className="mt-4">
              {copilotLoading && (
                <div className="flex items-center gap-2 text-xs text-text-secondary mb-2">
                  <Loader2 size={12} className="animate-spin" /> Generating...
                </div>
              )}
              {copilotOutput && (
                <div className="relative">
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(copilotOutput)
                      toast.success('Copied to clipboard')
                    }}
                    className="absolute top-2 right-2 p-1 rounded hover:bg-elevated text-text-secondary"
                  >
                    <Copy size={12} />
                  </button>
                  <div className="p-3 bg-elevated rounded-lg text-sm text-text-primary leading-relaxed whitespace-pre-wrap">
                    {copilotOutput}
                  </div>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
