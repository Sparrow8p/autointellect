import { useState } from 'react'
import type { FormEvent } from 'react'
import { ArrowRight, CarFront, ChartNoAxesCombined } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import type { CarProfileDraft } from '../types/carProfile'

const exampleCar = { brand: 'Hyundai', model: 'Solaris', year: '2018' }
const priceAfterRepair = 680000
const formatMoney = (value: number) => value.toLocaleString('ru-RU')

export function CarValuation({ car, problem, priceAsIs, onPriceChange }: {
  car: CarProfileDraft
  problem: string
  priceAsIs: string
  onPriceChange: (value: string) => void
}) {
  const navigate = useNavigate()
  const [touched, setTouched] = useState(false)
  const hasCar = Boolean(car.brand && car.model && car.year && car.region && /^\d+$/.test(car.mileage.replace(/\s/g, '')))
  const selectedCar = hasCar ? car : exampleCar
  const selectedProblem = problem.trim() || (hasCar ? 'Проблема не указана' : 'Стук в подвеске')
  const digits = priceAsIs.replace(/\s/g, '')
  const isValid = /^\d+$/.test(digits) && Number.isSafeInteger(Number(digits))
  const difference = isValid ? priceAfterRepair - Number(digits) : 0
  const showError = !isValid && (touched || priceAsIs.length > 0)

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!isValid) {
      setTouched(true)
      event.currentTarget.querySelector('input')?.focus()
      return
    }
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
        <p>{selectedCar.brand} {selectedCar.model}, {selectedCar.year} • {selectedProblem} • Стоимость ремонта: <span className="whitespace-nowrap">~21 000 ₽</span></p>
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
            {showError && <p id="valuation-error" role="alert" className="text-xs leading-5 text-error">{digits ? 'Введите цену только цифрами, без знаков и дробной части.' : 'Укажите цену автомобиля.'}</p>}
          </div>
          <button type="submit" disabled={!isValid} className="valuation-continue"><ArrowRight size={20} strokeWidth={1} aria-hidden="true" />Сравнить сценарии</button>
          <p className="text-[13px] leading-4 text-muted">Оценка помогает сравнить варианты. Реальная цена зависит от состояния и спроса.</p>
        </form>

        <aside className="valuation-summary" aria-labelledby="valuation-after-title">
          <p className="flex items-center gap-2.5 text-[13px] leading-4 font-medium text-forest"><ChartNoAxesCombined size={22} strokeWidth={1} className="shrink-0" aria-hidden="true" />Ориентир, не гарантия цены</p>
          <h2 id="valuation-after-title" className="text-xl leading-[1.35] font-semibold">Цена после ремонта (оценка системы)</h2>
          <p className="valuation-price">≈ {formatMoney(priceAfterRepair)} ₽</p>
          <p className={`valuation-growth ${!isValid || difference < 0 ? 'text-muted' : ''}`} aria-live="polite">
            {isValid ? <>{difference < 0 ? 'Изменение' : 'Прирост'} стоимости: {difference > 0 ? '+' : ''}{formatMoney(difference)} ₽</> : 'Укажите цену для сравнения'}
          </p>
          <hr className="border-0 border-t border-line" />
          <p className="text-[13px] leading-[1.45] text-muted">Пример из макета. Реальная оценка после ремонта пока не подключена.</p>
        </aside>
      </div>
    </>
  )
}
