import { useRef, useState } from 'react'
import { ChevronDown, LogIn, X } from 'lucide-react'
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'
import { sections } from '../routes'
import { BackButton } from './BackButton'
import { Brand } from './Brand'

export function Layout() {
  const [menuOpen, setMenuOpen] = useState(false)
  const { pathname } = useLocation()
  const aboutDialog = useRef<HTMLDialogElement>(null)

  return (
    <div className="min-h-dvh">
      <a href="#main-content" className="skip-link">Перейти к содержимому</a>
      <header className="app-header">
        <div className="app-shell app-topbar">
          <Brand />
          <nav aria-label="Основная навигация" className="app-navigation">
            <NavLink to="/home" className={({ isActive }) => isActive || ['/car', '/repair', '/valuation'].includes(pathname) ? 'app-tab app-tab-active' : 'app-tab'}>Главная</NavLink>
            <NavLink to="/history" className={({ isActive }) => isActive ? 'app-tab app-tab-active' : 'app-tab'}>История расчётов</NavLink>
            <button type="button" onClick={() => aboutDialog.current?.showModal()} className="app-tab">О сервисе</button>
          </nav>

          <div className="app-header-actions">
            {pathname !== '/car' && <BackButton />}
            <div className="relative" onKeyDown={(event) => { if (event.key === 'Escape') setMenuOpen(false) }}>
              <button
                type="button"
                className="account-button"
                aria-label={menuOpen ? 'Закрыть меню' : 'Открыть меню'}
                aria-expanded={menuOpen}
                aria-controls="account-navigation"
                onClick={() => setMenuOpen(!menuOpen)}
              >
                <span className="account-avatar" aria-hidden="true">АК</span>
                <span className="hidden sm:inline">Александр</span>
                <ChevronDown size={16} strokeWidth={1} className="hidden text-forest sm:block" aria-hidden="true" />
              </button>

              {menuOpen && (
                <nav id="account-navigation" aria-label="Разделы приложения" className="account-menu">
                  {sections.map(({ path, title, icon: Icon }) => (
                    <NavLink key={path} to={path} onClick={() => setMenuOpen(false)} className={({ isActive }) => isActive ? 'nav-link nav-link-active' : 'nav-link'}>
                      <Icon size={18} strokeWidth={1.6} aria-hidden="true" />{title}
                    </NavLink>
                  ))}
                  <button type="button" onClick={() => { setMenuOpen(false); aboutDialog.current?.showModal() }} className="nav-link w-full">О сервисе</button>
                  <Link to="/" onClick={() => setMenuOpen(false)} className="nav-link mt-2 border-t border-line">
                    <LogIn size={18} aria-hidden="true" />На экран входа
                  </Link>
                </nav>
              )}
            </div>
          </div>
        </div>
      </header>

      <main id="main-content" tabIndex={-1} className="app-shell app-main">
        <Outlet />
      </main>

      <dialog
        ref={aboutDialog}
        aria-labelledby="about-title"
        className="about-dialog"
        onClick={(event) => { if (event.target === event.currentTarget) aboutDialog.current?.close() }}
      >
        <div className="flex items-start justify-between gap-6">
          <h2 id="about-title" className="text-xl font-bold">Об Авто-Интеллекте</h2>
          <button type="button" onClick={() => aboutDialog.current?.close()} aria-label="Закрыть" className="rounded p-1 text-muted"><X size={20} aria-hidden="true" /></button>
        </div>
        <p className="mt-4 text-sm leading-6 text-muted">Помогаем разобраться в стоимости ремонта и сравнить варианты: продать автомобиль как есть, отремонтировать и продать или продолжить пользоваться.</p>
        <p className="mt-3 text-sm leading-6 text-muted">Предварительная оценка помогает сориентироваться. Окончательное решение — за вами.</p>
        <button type="button" onClick={() => aboutDialog.current?.close()} className="primary-button mt-6">Понятно</button>
      </dialog>
    </div>
  )
}
