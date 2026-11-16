import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { ArrowRight, CarFront, ChartNoAxesCombined } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import { api, errorMessage } from '../lib/api'
import type { ApiCar, EstimateResult, ScenariosResult } from '../lib/api'

const formatMoney = (value: number) => value.toLocaleString('ru-RU')

export function CarValuation({ car, problem, estimate, priceAsIs, onPriceChange, onCalculated }: {
  car: ApiCar
  problem: string
  estimate: EstimateResult
  priceAsIs: string
  onPriceChange: (value: string) => void
  onCalculated: (result: ScenariosResult) => void
}) {
  const navigate = useNavigate()
  const [touched, setTouched] = useState(false)
  const [preview, setPreview] = useState<{ price: number; result: ScenariosResult } | null>(null)
  const [failure, setFailure] = useState<{ price: number; message: string } | null>(null)
  const [attempt, setAttempt] = useState(0)
  const digits = priceAsIs.replace(/\s/g, '')
  const price = Number(digits)
  const isValid = /^\d+$/.test(digits) && Number.isSafeInteger(price) && price > 0 && price <= 100_000_000
  const result = isValid && preview?.price === price ? preview.result : null
  const error = isValid && failure?.price === price ? failure.message : ''
  const loading = isValid && !result && !error
  const priceAfterRepair = result?.scenarios.repair_and_sell.price_after_repair
  const difference = priceAfterRepair === undefined ? null : priceAfterRepair - price
  const repairCost = Math.round((estimate.min_price + estimate.max_price) / 2)
  const showError = !isValid && (touched || priceAsIs.length > 0)

  useEffect(() => {
    if (!isValid) return
    const controller = new AbortController()
    const timer = window.setTimeout(() => {
      void api<ScenariosResult>('/calculations/scenarios', { method: 'POST', body: { car_id: car.id, problem_text: problem.trim(), car_price: price }, signal: controller.signal })
        .then((data) => { if (!controller.signal.aborted) { setPreview({ price, result: data }); setFailure(null) } })
        .catch((reason) => { if (!controller.signal.aborted) setFailure({ price, message: errorMessage(reason) }) })
    }, 300)
    return () => { window.clearTimeout(timer); controller.abort() }
  }, [car.id, problem, price, isValid, attempt])

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!isValid) {
      setTouched(true)
      event.currentTarget.querySelector('input')?.focus()
      return
    }
    if (!result) return
    onCalculated(result)
    void navigate('/scenarios')
  }

  return (
    <>
      <section aria-labelledby="valuation-title">
        <p className="text-[13px] leading-4 text-muted">
          <Link to="/home" className="rounded hover:text-forest">Главная</Link> /{' '}
          <Link to="/car" className="rounded hover:text-forest">Профиль авто</Link> /{' '}
          <Link to="/repair" className="rounded hover:text-forest">Результат</Link> / Оценка авто
        </p>
        <h1 id="valuation-title" tabIndex={-1} className="home-title">Рыночная оценка автомобиля</h1>
      </section>

      <div className="valuation-context">
        <CarFront size={22} strokeWidth={1} aria-hidden="true" />
        <p>{car.brand} {car.model}, {car.year} • {problem} • Стоимость ремонта: <span className="whitespace-nowrap">~{formatMoney(repairCost)} ₽</span></p>
      </div>

      <div className="valuation-content">
        <form onSubmit={handleSubmit} noValidate className="valuation-form">
          <div className="valuation-form-card">
            <p className="text-[13px] leading-4 font-semibold text-forest">ШАГ 2 ИЗ 2</p>
            <h2 className="valuation-question"><label htmlFor="price-as-is">За сколько можно продать машину сейчас (с поломкой)?</label></h2>
            <div className="relative">
              <input
                id="price-as-is"
                name="priceAsIs"
                type="text"
                inputMode="numeric"
                required
                value={priceAsIs}
                onChange={(event) => onPriceChange(event.target.value)}
                onBlur={() => { setTouched(true); if (isValid) onPriceChange(formatMoney(Number(digits))) }}
                aria-invalid={showError}
                aria-describedby={showError ? 'valuation-hint valuation-error' : 'valuation-hint'}
                className="valuation-input"
              />
              <span aria-hidden="true" className="valuation-currency">₽</span>
            </div>
            <p id="valuation-hint" className="text-sm leading-[1.45] text-muted">Не знаете точную цену? Посмотрите похожие объявления на Авито или Авто.ру и введите среднюю сумму</p>
            {showError && <p id="valuation-error" role="alert" className="text-xs leading-5 text-error">{digits ? 'Введите целую цену от 1 до 100 000 000 ₽.' : 'Укажите цену автомобиля.'}</p>}
          </div>
          <button type="submit" disabled={!result} className="valuation-continue"><ArrowRight size={20} strokeWidth={1} aria-hidden="true" />{loading ? 'Рассчитываем…' : 'Сравнить сценарии'}</button>
          <p className="text-[13px] leading-4 text-muted">Оценка помогает сравнить варианты. Реальная цена зависит от состояния и спроса.</p>
        </form>

        <aside className="valuation-summary" aria-labelledby="valuation-after-title">
          <p className="flex items-center gap-2.5 text-[13px] leading-4 font-medium text-forest"><ChartNoAxesCombined size={22} strokeWidth={1} className="shrink-0" aria-hidden="true" />Ориентир, не гарантия цены</p>
          <h2 id="valuation-after-title" className="text-xl leading-[1.35] font-semibold">Цена после ремонта (оценка системы)</h2>
          <p className="valuation-price">{priceAfterRepair === undefined ? '—' : `≈ ${formatMoney(priceAfterRepair)} ₽`}</p>
          <p className={`valuation-growth ${difference === null || difference < 0 ? 'text-muted' : ''}`} aria-live="polite">
            {difference !== null ? <>{difference < 0 ? 'Изменение' : 'Прирост'} стоимости: {difference > 0 ? '+' : ''}{formatMoney(difference)} ₽</> : loading ? 'Рассчитываем стоимость…' : 'Укажите цену для сравнения'}
          </p>
          <hr className="border-0 border-t border-line" />
          {error ? <div role="alert" className="text-sm leading-5 text-error"><p>{error}</p><button type="button" onClick={() => { setFailure(null); setAttempt(attempt + 1) }} className="mt-3 text-forest underline">Повторить</button></div> : <p className="text-[13px] leading-[1.45] text-muted">Ориентировочная цена с учётом ремонта. Окончательная сумма зависит от состояния автомобиля и спроса.</p>}
        </aside>
      </div>
    </>
  )
}
