import { ArrowRight, SearchX } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { Link } from 'react-router-dom'

export function Placeholder({ title, icon: Icon }: { title: string; icon: LucideIcon }) {
  return (
    <section className="mt-7 min-h-[50dvh] rounded-3xl border border-line bg-white p-7 sm:p-10">
      <span className="grid size-12 place-items-center rounded-2xl bg-sage text-forest"><Icon size={24} strokeWidth={1.5} aria-hidden="true" /></span>
      <p className="eyebrow mt-7">СКОРО В АВТО-ИНТЕЛЛЕКТЕ</p>
      <h1 tabIndex={-1} className="mt-3 text-3xl leading-tight font-medium tracking-[-1px] outline-none sm:text-4xl">{title}</h1>
      <p className="mt-4 text-sm leading-6 text-muted">Этот раздел пока в разработке.</p>
    </section>
  )
}

export function NotFound() {
  return (
    <section className="mt-7 min-h-[50dvh] rounded-3xl border border-line bg-white p-7 sm:p-10">
      <SearchX size={32} strokeWidth={1.5} className="text-forest" aria-hidden="true" />
      <p className="eyebrow mt-7">ОШИБКА 404</p>
      <h1 tabIndex={-1} className="mt-3 text-3xl font-medium tracking-[-1px] outline-none">Страница не найдена</h1>
      <p className="mt-4 text-sm text-muted">Кажется, здесь был неверный поворот.</p>
      <Link to="/home" className="primary-button mt-7 w-fit">На главную <ArrowRight size={17} aria-hidden="true" /></Link>
    </section>
  )
}
