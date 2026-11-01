import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { sections } from '../routes'

export function RouteEffects() {
  const { pathname } = useLocation()

  useEffect(() => {
    const title = pathname === '/' ? 'Вход' : sections.find((section) => section.path === pathname)?.title ?? 'Страница не найдена'
    document.title = `${title} · Авто-Интеллект`
    window.scrollTo(0, 0)
    document.querySelector<HTMLElement>('h1')?.focus({ preventScroll: true })
  }, [pathname])

  return null
}
