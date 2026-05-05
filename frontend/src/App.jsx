import { Routes, Route } from 'react-router-dom'
import InputPage from './pages/InputPage.jsx'
import ReportPage from './pages/ReportPage.jsx'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<InputPage />} />
      <Route path="/report/:runId" element={<ReportPage />} />
      <Route path="/report-preview" element={<ReportPage preview />} />
    </Routes>
  )
}
