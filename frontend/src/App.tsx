import { useEffect, useState } from 'react'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { Layout } from './components/Layout'
import { RouteEffects } from './components/RouteEffects'
import { Home } from './pages/Home'
import { CarProfile } from './pages/CarProfile'
import { RepairEstimate } from './pages/RepairEstimate'
import { CarValuation } from './pages/CarValuation'
import { Scenarios } from './pages/Scenarios'
import { History } from './pages/History'
import { Login } from './pages/Login'
import { NotFound } from './pages/Placeholder'
import { loadSavedCarProfile, saveCarProfile } from './lib/carProfileStorage'
import { api, getToken, setToken } from './lib/api'
import type { ApiCar, ApiUser, EstimateResult, ScenariosResult } from './lib/api'
import { emptyCarProfile } from './types/carProfile'

export function App() {
  const location = useLocation()
  const [session, setSession] = useState(getToken)
  const [user, setUser] = useState<ApiUser | null>(null)
  const [problem, setProblem] = useState('')
  const [carDraft, setCarDraft] = useState(loadSavedCarProfile)
  const [priceAsIs, setPriceAsIs] = useState('')
  const [car, setCar] = useState<ApiCar | null>(null)
  const [estimate, setEstimate] = useState<EstimateResult | null>(null)
  const [comparison, setComparison] = useState<ScenariosResult | null>(null)

  function startNew() {
    setProblem('')
    setPriceAsIs('')
    setEstimate(null)
    setComparison(null)
  }

  function signOut() {
    setToken(null)
    setSession(null)
    setUser(null)
    setCar(null)
    setCarDraft({ ...emptyCarProfile })
    startNew()
    try { saveCarProfile({ ...emptyCarProfile, saveToProfile: false }) } catch { return }
  }

  useEffect(() => {
    function expired() {
      setSession(null)
      setUser(null)
      setCar(null)
      setCarDraft({ ...emptyCarProfile })
      setProblem('')
      setPriceAsIs('')
      setEstimate(null)
      setComparison(null)
    }
    window.addEventListener('auth-expired', expired)
    return () => window.removeEventListener('auth-expired', expired)
  }, [])

  useEffect(() => {
    if (!session) return
    const controller = new AbortController()
    void api<ApiUser>('/users/me', { signal: controller.signal }).then((profile) => {
      if (!controller.signal.aborted) setUser(profile)
    }).catch(() => undefined)
    return () => controller.abort()
  }, [session])

  return (
    <>
      <RouteEffects />
      <Routes>
        <Route path="/" element={<Login onAuthenticated={(token) => { setToken(token); setSession(token); setUser(null); setCar(null); startNew() }} />} />
        <Route element={session ? <Layout user={user} onLogout={signOut} /> : <Navigate to="/" replace state={{ from: location.pathname }} />}>
          <Route path="/home" element={<Home problem={problem} onProblemChange={(value) => { setProblem(value); setEstimate(null); setComparison(null) }} />} />
          <Route path="/car" element={<CarProfile draft={carDraft} problem={problem} onDraftChange={(draft) => { setCarDraft(draft); setCar(null); setEstimate(null); setComparison(null) }} onCalculated={(savedCar, result) => { setCar(savedCar); setEstimate(result); setComparison(null) }} />} />
          <Route path="/repair" element={car && estimate ? <RepairEstimate car={car} problem={problem} estimate={estimate} /> : <Navigate to="/car" replace />} />
          <Route path="/valuation" element={car && estimate ? <CarValuation car={car} problem={problem} estimate={estimate} priceAsIs={priceAsIs} onPriceChange={(value) => { setPriceAsIs(value); setComparison(null) }} onCalculated={setComparison} /> : <Navigate to="/car" replace />} />
          <Route path="/scenarios" element={car && comparison ? <Scenarios car={car} problem={problem} result={comparison} onStartNew={startNew} /> : <Navigate to="/valuation" replace />} />
          <Route path="/history" element={<History onStartNew={startNew} />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </>
  )
}
