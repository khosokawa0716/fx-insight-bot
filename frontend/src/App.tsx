import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ThemeProvider } from './contexts/ThemeContext'
import { DashboardPage } from './pages/DashboardPage'
import { PositionDetailPage } from './pages/PositionDetailPage'
import { NewsPage } from './pages/NewsPage'
import { SignalsPage } from './pages/SignalsPage'
import { SettingsPage } from './pages/SettingsPage'
import { PresentationPage } from './pages/PresentationPage'

function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/position/:positionId" element={<PositionDetailPage />} />
          <Route path="/news" element={<NewsPage />} />
          <Route path="/signals" element={<SignalsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/presentation" element={<PresentationPage />} />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  )
}

export default App
