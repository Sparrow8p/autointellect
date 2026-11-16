import { useState } from 'react'
import { Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { RouteEffects } from './components/RouteEffects'
import { Home } from './pages/Home'
import { CarProfile } from './pages/CarProfile'
import { RepairEstimate } from './pages/RepairEstimate'
import { CarValuation } from './pages/CarValuation'
import { Scenarios } from './pages/Scenarios'
import { History } from './pages/History'
import { Login } from './pages/Login'
import { NotFound, Placeholder } from './pages/Placeholder'
import { placeholderSections } from './routes'
import { loadSavedCarProfile } from './lib/carProfileStorage'

export function App() {
  const [problem, setProblem] = useState('')
  const [carDraft, setCarDraft] = useState(loadSavedCarProfile)
  const [priceAsIs, setPriceAsIs] = useState('580 000')

  return (
    <>
      <RouteEffects />
      <Routes>
        <Route path="/" element={<Login />} />
        <Route element={<Layout />}>
          <Route path="/home" element={<Home problem={problem} onProblemChange={setProblem} />} />
          <Route path="/car" element={<CarProfile draft={carDraft} onDraftChange={setCarDraft} />} />
          <Route path="/repair" element={<RepairEstimate car={carDraft} problem={problem} />} />
          <Route path="/valuation" element={<CarValuation car={carDraft} problem={problem} priceAsIs={priceAsIs} onPriceChange={setPriceAsIs} />} />
          <Route path="/scenarios" element={<Scenarios car={carDraft} priceAsIs={priceAsIs} onStartNew={() => { setProblem(''); setPriceAsIs('') }} />} />
          <Route path="/history" element={<History onStartNew={() => { setProblem(''); setPriceAsIs('') }} />} />
          {placeholderSections.map((section) => (
            <Route key={section.path} path={section.path} element={<Placeholder title={section.title} icon={section.icon} />} />
          ))}
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </>
  )
}
