import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import Layout from './components/layout/Layout'
import Dashboard from './pages/Dashboard'
import JobBoard from './pages/JobBoard'
import Pipeline from './pages/Pipeline'
import Analytics from './pages/Analytics'
import Settings from './pages/Settings'
import { connectSSE, fetchSettings, fetchStats } from './api/client'
import { useJobStore } from './store/useJobStore'

type Page = 'dashboard' | 'jobs' | 'pipeline' | 'analytics' | 'settings'

export default function App() {
  const [currentPage, setCurrentPage] = useState<Page>('dashboard')
  const { setIsScraperRunning, addScraperLog, setTotalJobCount, setIsResumeActive } = useJobStore()

  // Fetch initial stats for job count
  const { data: stats } = useQuery({
    queryKey: ['stats'],
    queryFn: fetchStats,
    refetchInterval: 30_000,
  })

  // Fetch settings to check resume status
  const { data: settings } = useQuery({
    queryKey: ['settings'],
    queryFn: fetchSettings,
  })

  useEffect(() => {
    if (stats) {
      setTotalJobCount(stats.total_jobs)
    }
  }, [stats])

  useEffect(() => {
    if (settings) {
      setIsResumeActive(!!settings.resume_filename)
    }
  }, [settings])

  // SSE connection
  useEffect(() => {
    const es = connectSSE((event) => {
      const now = new Date().toLocaleTimeString('en-US', { hour12: false })

      switch (event.event) {
        case 'scraper_started':
          setIsScraperRunning(true)
          addScraperLog({
            timestamp: now,
            source: event.source,
            message: `Starting ${event.source} scraper...`,
            type: 'info',
          })
          break
        case 'job_found':
          addScraperLog({
            timestamp: now,
            source: event.source,
            message: `Found ${event.count} jobs`,
            type: 'info',
          })
          break
        case 'scraper_progress':
          addScraperLog({
            timestamp: now,
            source: event.source,
            message: `${event.new} new \u00b7 ${event.existing} existing`,
            type: 'success',
          })
          break
        case 'scraper_completed':
          addScraperLog({
            timestamp: now,
            source: event.source,
            message: `Complete: ${event.found} found, ${event.new} new`,
            type: 'success',
          })
          setIsScraperRunning(false)
          break
        case 'scraper_error':
          addScraperLog({
            timestamp: now,
            source: event.source,
            message: `Error: ${event.error}`,
            type: 'error',
          })
          setIsScraperRunning(false)
          break
      }
    })

    return () => es.close()
  }, [])

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard': return <Dashboard />
      case 'jobs': return <JobBoard />
      case 'pipeline': return <Pipeline />
      case 'analytics': return <Analytics />
      case 'settings': return <Settings />
    }
  }

  return (
    <Layout currentPage={currentPage} onNavigate={setCurrentPage}>
      {renderPage()}
    </Layout>
  )
}
