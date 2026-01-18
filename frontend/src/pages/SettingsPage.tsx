import { Link } from 'react-router-dom'
import { ArrowLeft, Bell, Clock, Palette, Shield } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface SettingItemProps {
  icon: React.ReactNode
  title: string
  description: string
  children: React.ReactNode
}

function SettingItem({ icon, title, description, children }: SettingItemProps) {
  return (
    <div className="flex items-start justify-between py-4 border-b last:border-b-0">
      <div className="flex items-start gap-3">
        <div className="text-gray-400 mt-0.5">{icon}</div>
        <div>
          <h3 className="font-medium text-gray-900">{title}</h3>
          <p className="text-sm text-gray-500 mt-0.5">{description}</p>
        </div>
      </div>
      <div className="flex-shrink-0">{children}</div>
    </div>
  )
}

interface ToggleSwitchProps {
  enabled: boolean
  onChange: (enabled: boolean) => void
  disabled?: boolean
}

function ToggleSwitch({ enabled, onChange, disabled = false }: ToggleSwitchProps) {
  return (
    <button
      type="button"
      onClick={() => !disabled && onChange(!enabled)}
      disabled={disabled}
      className={cn(
        "relative inline-flex h-6 w-11 items-center rounded-full transition-colors",
        enabled ? 'bg-blue-600' : 'bg-gray-200',
        disabled && 'opacity-50 cursor-not-allowed'
      )}
    >
      <span
        className={cn(
          "inline-block h-4 w-4 transform rounded-full bg-white transition-transform",
          enabled ? 'translate-x-6' : 'translate-x-1'
        )}
      />
    </button>
  )
}

export function SettingsPage() {
  const { user, signOut } = useAuth()

  // 設定値（現在は表示のみ、将来的にはlocalStorageやFirestoreで永続化）
  const settings = {
    autoRefresh: true,
    refreshInterval: 30,
    notifications: false,
    darkMode: false,
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <Link to="/">
              <Button variant="ghost" size="icon">
                <ArrowLeft className="h-5 w-5" />
              </Button>
            </Link>
            <h1 className="text-xl font-bold text-gray-900">
              Settings
            </h1>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">{user?.email}</span>
            <Button variant="ghost" size="sm" onClick={signOut}>
              Sign out
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-2xl mx-auto px-4 py-6 space-y-6">
        {/* Display Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Display Settings</CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <SettingItem
              icon={<Clock className="h-5 w-5" />}
              title="Auto Refresh"
              description="Automatically refresh data every 30 seconds"
            >
              <ToggleSwitch
                enabled={settings.autoRefresh}
                onChange={() => {}}
                disabled
              />
            </SettingItem>

            <SettingItem
              icon={<Palette className="h-5 w-5" />}
              title="Dark Mode"
              description="Use dark color theme (Coming soon)"
            >
              <ToggleSwitch
                enabled={settings.darkMode}
                onChange={() => {}}
                disabled
              />
            </SettingItem>
          </CardContent>
        </Card>

        {/* Notification Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Notifications</CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <SettingItem
              icon={<Bell className="h-5 w-5" />}
              title="Push Notifications"
              description="Receive notifications for important signals (Coming soon)"
            >
              <ToggleSwitch
                enabled={settings.notifications}
                onChange={() => {}}
                disabled
              />
            </SettingItem>
          </CardContent>
        </Card>

        {/* Account Info */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Account</CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <SettingItem
              icon={<Shield className="h-5 w-5" />}
              title="Email"
              description="Your login email address"
            >
              <span className="text-sm text-gray-600">{user?.email}</span>
            </SettingItem>

            <div className="pt-4">
              <Button
                variant="outline"
                className="w-full text-red-600 hover:text-red-700 hover:bg-red-50"
                onClick={signOut}
              >
                Sign Out
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* App Info */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">About</CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Version</span>
                <span className="text-gray-900">0.1.0</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Environment</span>
                <span className="text-gray-900">
                  {import.meta.env.MODE === 'production' ? 'Production' : 'Development'}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </main>

      {/* Footer */}
      <footer className="border-t mt-auto bg-white">
        <div className="max-w-7xl mx-auto px-4 py-4 text-center text-sm text-gray-500">
          FX Insight Bot - Display Only Dashboard
        </div>
      </footer>
    </div>
  )
}
