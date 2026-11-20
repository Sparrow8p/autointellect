import type { FormEvent } from 'react'
import { ArrowRight, Plus, ShieldCheck } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'

const suggestions = ['Стук в подвеске', 'Не заводится', 'После ДТП', 'Горит Check Engine', 'Замена масла']
const steps = [
  'Опишите проблему и укажите авто',
  'Получите честный диапазон цен',
  'Сравните сценарии и примите решение',
]

export function Home({ problem, onProblemChange }: { problem: string; onProblemChange: (value: string) => void }) {
  const navigate = useNavigate()
  const canContinue = problem.trim().length >= 2

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (canContinue) void navigate('/car')
  }

  return (
    <>
      <section aria-labelledby="home-title">
        <p className="text-[13px] leading-4 text-muted">Ваше решение начинается с ясности</p>
        <h1 id="home-title" tabIndex={-1} className="home-title">Что случилось с машиной?</h1>
      </section>

      <div className="home-content">
        <form onSubmit={handleSubmit} className="min-w-0">
          <p className="home-description">Расскажите, что вас беспокоит. Мы поможем разобраться в стоимости и вариантах.</p>
          <label htmlFor="problem" className="sr-only">Описание проблемы</label>
          <div className="home-problem-field">
            <textarea
              id="problem"
              name="problem"
              value={problem}
              onChange={(event) => onProblemChange(event.target.value)}
              maxLength={1000}
              rows={6}
              placeholder="Опишите проблему своими словами. Например: стучит спереди на кочках при повороте руля или горит Check Engine"
              aria-describedby="problem-hint problem-count"
              className="home-textarea"
            />
            <span id="problem-count" className="home-problem-count">{problem.length} / 1 000</span>
          </div>

          <p id="problem-hint" className="mt-6 text-[13px] leading-4 text-muted">Или выберите частую проблему</p>
          <div className="mt-3 flex flex-wrap gap-2.5">
            {suggestions.map((suggestion) => (
              <button
                type="button"
                key={suggestion}
                aria-pressed={problem === suggestion}
                onClick={() => onProblemChange(problem === suggestion ? '' : suggestion)}
                className={problem === suggestion ? 'problem-tag problem-tag-active' : 'problem-tag'}
              >
                {suggestion}
              </button>
            ))}
          </div>

          <button type="submit" disabled={!canContinue} className="home-calculate">
            <ArrowRight size={20} strokeWidth={1} aria-hidden="true" />Рассчитать стоимость
          </button>
          <p className="home-disclaimer">
            <ShieldCheck size={16} strokeWidth={1} aria-hidden="true" />
            Ориентировочный расчёт, а не замена диагностики в сервисе
          </p>
        </form>

        <aside className="home-aside">
          <section className="home-car-card" aria-labelledby="your-car-title">
            <h2 id="your-car-title" className="text-xl leading-6 font-semibold">Ваш автомобиль</h2>
            <Link to="/car" className="home-add-car"><Plus size={22} strokeWidth={1} aria-hidden="true" />Добавить автомобиль</Link>
          </section>

          <section className="home-how" aria-labelledby="how-title">
            <h2 id="how-title" className="text-xl leading-6 font-semibold">Как это работает</h2>
            <ol className="mt-[22px] grid gap-[22px]">
              {steps.map((step, index) => (
                <li key={step} className="flex items-center gap-3.5">
                  <span className="home-step-number">{index + 1}</span>
                  <span className="text-sm leading-[1.45] text-muted">{step}</span>
                </li>
              ))}
            </ol>
          </section>
        </aside>
      </div>
    </>
  )
}
