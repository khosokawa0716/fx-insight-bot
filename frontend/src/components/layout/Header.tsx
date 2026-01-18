import { Link } from 'react-router-dom'
import { Newspaper, Radio, Settings } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'

export function Header() {
  const { user, signOut } = useAuth()

  return (
    <header className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
        <div className="flex items-center gap-6">
          <Link to="/" className="text-xl font-bold text-gray-900 hover:text-gray-700">
            FX Insight Bot
          </Link>
          <nav className="flex items-center gap-1">
            <Link to="/">
              <Button variant="ghost" size="sm" className="text-gray-600">
                Dashboard
              </Button>
            </Link>
            <Link to="/news">
              <Button variant="ghost" size="sm" className="text-gray-600">
                <Newspaper className="h-4 w-4 mr-1" />
                News
              </Button>
            </Link>
            <Link to="/signals">
              <Button variant="ghost" size="sm" className="text-gray-600">
                <Radio className="h-4 w-4 mr-1" />
                Signals
              </Button>
            </Link>
            <Link to="/settings">
              <Button variant="ghost" size="sm" className="text-gray-600">
                <Settings className="h-4 w-4 mr-1" />
                Settings
              </Button>
            </Link>
          </nav>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-600">{user?.email}</span>
          <Button variant="ghost" size="sm" onClick={signOut}>
            Sign out
          </Button>
        </div>
      </div>
    </header>
  )
}
