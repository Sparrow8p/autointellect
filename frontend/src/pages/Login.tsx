import { useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { BadgeCheck, ChartNoAxesColumnIncreasing, GitBranch, Mail } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { BackButton } from '../components/BackButton'
import { Brand } from '../components/Brand'

function AppleIcon() {
  return (
    <svg viewBox="0 0 24 24" width="26" height="26" fill="currentColor" aria-hidden="true">
      <path d="M16.7 3.1c-.8 1-1.9 1.7-3.1 1.6-.2-1.2.4-2.4 1.1-3.2C15.5.6 16.7.1 17.8 0c.1 1.2-.4 2.3-1.1 3.1ZM20.2 17.5c-.5 1.2-.8 1.8-1.4 2.8-.9 1.4-2.2 3.1-3.8 3.1-1.4 0-1.8-.9-3.8-.9-1.9 0-2.4.9-3.8.9-1.5.1-2.8-1.5-3.7-2.9C1.1 16.6.5 11 2.1 8.1 3.3 6 5.2 4.8 7.1 4.8c1.5 0 2.5.8 3.8.8 1.2 0 2-.8 3.8-.8 1.4 0 2.9.7 4 1.8-3.5 1.9-2.9 7.1 1.5 8.9v2Z" transform="translate(2 1) scale(.86)" />
    </svg>
  )
}

export function Login() {
  const navigate = useNavigate()
  const identifierInput = useRef<HTMLInputElement>(null)
  const [identifier, setIdentifier] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const value = identifier.trim()
    const isEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)
    const isPhone = /^\+?\d{10,15}$/.test(value.replace(/[\s()-]/g, ''))

    if (!value || (!isEmail && !isPhone)) {
      setError(value ? 'Введите корректный телефон или email.' : 'Введите телефон или email, чтобы продолжить.')
      identifierInput.current?.focus()
      return
    }

    setError('')
    void navigate('/home')
  }

  function showProviderNotice(provider: string) {
    setNotice('Вход через ' + provider + ' пока недоступен. Укажите телефон или email.')
  }

  return (
    <div className="login-page">
      <a href="#login-form" className="skip-link">Перейти к форме входа</a>
      <div className="login-shell">
        <header className="login-header">
          <Brand />
          <BackButton />
        </header>

        <main className="login-content">
          <section className="login-pitch" aria-labelledby="login-pitch-title">
            <p className="login-eyebrow">СПОКОЙНОЕ РЕШЕНИЕ. ПОНЯТНЫЕ ЦИФРЫ.</p>
            <h2 id="login-pitch-title" className="login-pitch-title">
              Узнайте, выгоднее<br className="hidden xl:block" />{' '}
              отремонтировать или продать<br className="hidden xl:block" />{' '}
              автомобиль, за 3 минуты
            </h2>

            <ul className="login-benefits">
              <li>
                <ChartNoAxesColumnIncreasing size={28} strokeWidth={1.1} aria-hidden="true" />
                <span>Честный диапазон цен — от и до, без ложной точности</span>
              </li>
              <li>
                <GitBranch size={28} strokeWidth={1.1} aria-hidden="true" />
                <span>Три сценария: продать как есть, ремонт + продажа, ремонт + эксплуатация</span>
              </li>
              <li>
                <BadgeCheck size={28} strokeWidth={1.1} aria-hidden="true" />
                <span>Чёткая рекомендация с цифрами и объяснением</span>
              </li>
            </ul>
            <p className="login-pitch-note">Без сложных терминов. Окончательное решение — за вами.</p>
          </section>

          <section id="login-form" className="login-card" aria-labelledby="login-title">
            <h1 id="login-title" tabIndex={-1} className="login-title">Вход в аккаунт</h1>
            <p className="login-subtitle">Сохраняйте расчёты и возвращайтесь к ним</p>

            <form onSubmit={handleSubmit} noValidate className="login-form">
              <label htmlFor="identifier" className="sr-only">Телефон или Email</label>
              <div className="relative">
                <Mail size={20} strokeWidth={1.3} className="login-input-icon" aria-hidden="true" />
                <input
                  ref={identifierInput}
                  id="identifier"
                  name="identifier"
                  type="text"
                  autoComplete="username"
                  placeholder="Телефон или Email"
                  required
                  maxLength={254}
                  value={identifier}
                  onChange={(event) => { setIdentifier(event.target.value); setError('') }}
                  aria-invalid={Boolean(error)}
                  aria-describedby={error ? 'identifier-error login-note' : 'login-note'}
                  className={error ? 'login-input border-error' : 'login-input'}
                />
              </div>
              {error && <p id="identifier-error" role="alert" className="mt-2 text-xs leading-5 text-error">{error}</p>}
              <button type="submit" className="login-continue">Продолжить</button>
              <p id="login-note" className="sr-only">Форма прототипа: телефон и email пока не подтверждаются.</p>
            </form>

            <div className="login-divider" aria-hidden="true"><span />или<span /></div>
            <div className="grid grid-cols-2 gap-4">
              <button type="button" onClick={() => showProviderNotice('Яндекс')} className="login-social">
                <span aria-hidden="true" className="text-[24px] font-semibold leading-none text-[#fc3f3f]">Я</span> Яндекс
              </button>
              <button type="button" onClick={() => showProviderNotice('Apple')} className="login-social"><AppleIcon /> Apple</button>
            </div>

            <p className="login-terms">Нажимая «Продолжить», вы соглашаетесь с Условиями и Политикой конфиденциальности</p>
            {notice && <p role="status" aria-live="polite" className="mt-3 text-xs leading-5 text-muted">{notice}</p>}
          </section>
        </main>
      </div>
    </div>
  )
}
