import { ArrowLeft } from 'lucide-react'
import { useLocation, useNavigate } from 'react-router-dom'
import { backFallbacks } from '../routes'

export function BackButton({ inverse = false }: { inverse?: boolean }) {
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const fallback = backFallbacks[pathname]
  const hasPreviousEntry = typeof window.history.state?.idx === 'number' && window.history.state.idx > 0
  const canGoBack = hasPreviousEntry || Boolean(fallback)

  function goBack() {
    if (hasPreviousEntry) void navigate(-1)
    else if (fallback) void navigate(fallback, { replace: true })
  }

  return (
    <button
      type="button"
      onClick={goBack}
      aria-label="Назад"
      disabled={!canGoBack}
      title={canGoBack ? 'Вернуться на предыдущий экран' : 'Вы на первом экране'}
      className={`back-button inline-flex min-h-10 items-center gap-2 rounded-lg text-sm transition-colors disabled:cursor-default disabled:opacity-40 ${inverse ? 'text-white/70 hover:text-white' : 'text-muted hover:text-forest'}`}
    >
      <ArrowLeft size={17} aria-hidden="true" />
      <span className="back-button-label">Назад</span>
    </button>
  )
}
