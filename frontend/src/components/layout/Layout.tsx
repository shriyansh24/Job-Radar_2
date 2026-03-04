import { ReactNode } from 'react'
import Sidebar from './Sidebar'
import TopBar from './TopBar'
import ScraperLog from '../scraper/ScraperLog'

type Page = 'dashboard' | 'jobs' | 'pipeline' | 'analytics' | 'settings'

interface LayoutProps {
  children: ReactNode
  currentPage: Page
  onNavigate: (page: Page) => void
}

export default function Layout({ children, currentPage, onNavigate }: LayoutProps) {
  return (
    <div className="flex h-screen overflow-hidden bg-base">
      <Sidebar currentPage={currentPage} onNavigate={onNavigate} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <TopBar />
        <main className="flex-1 overflow-auto p-6">
          {children}
        </main>
      </div>
      <ScraperLog />
    </div>
  )
}
