import { useState } from 'react'
import { Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { RouteEffects } from './components/RouteEffects'
import { Home } from './pages/Home'
import { Login } from './pages/Login'
import { NotFound, Placeholder } from './pages/Placeholder'
import { placeholderSections } from './routes'

export function App() {
  const [problem, setProblem] = useState('')

  return (
    <>
      <RouteEffects />
      <Routes>
        <Route path="/" element={<Login />} />
        <Route element={<Layout />}>
          <Route path="/home" element={<Home problem={problem} onProblemChange={setProblem} />} />
          {placeholderSections.map((section) => (
            <Route key={section.path} path={section.path} element={<Placeholder title={section.title} icon={section.icon} />} />
          ))}
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </>
  )
}
