import { useEffect, useRef, useState } from 'react'
import { Banknote, Bookmark, CarFront, Check, TrendingUp } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import { api, errorMessage } from '../lib/api'
import type { ApiCar, HistoryItem, ScenariosResult } from '../lib/api'

const formatMoney = (value: number) => value.toLocaleString('ru-RU')

export function Scenarios({ car, problem, result, onStartNew }: {
  car: ApiCar
  problem: string
  result: ScenariosResult
  onStartNew: () => void
}) {
  const navigate = useNavigate()
  const [expanded, setExpanded] = useState(true)
  const [error, setError] = useState('')
  const [pending, setPending] = useState(false)
  const request = useRef<AbortController | null>(null)
  const repairCost = result.repair.repair_cost
  const priceNow = result.scenarios.sell_as_is.value
  const priceAfterRepair = result.scenarios.repair_and_sell.price_after_repair
  const repairAndSale = result.scenarios.repair_and_sell.value
  const recommended = result.scenarios.repair_and_sell.recommended ? 'repair-sale' : result.scenarios.sell_as_is.recommended ? 'sell' : null

  useEffect(() => () => request.current?.abort(), [])

  async function saveCalculation() {
    if (request.current) return
    const controller = new AbortController()
    request.current = controller
    setPending(true)
    setError('')
    try {
      await api<HistoryItem>('/history/save', { method: 'POST', body: { car_id: car.id, problem_text: problem.trim(), car_price: priceNow }, signal: controller.signal })
      if (!controller.signal.aborted) void navigate('/history')
    } catch (reason) {
      if (!controller.signal.aborted) setError(errorMessage(reason))
    } finally {
      if (request.current === controller) request.current = null
      if (!controller.signal.aborted) setPending(false)
    }
  }

  const scenarios = [
    { id: 'sell', icon: Banknote, title: 'Продать как есть', amount: priceNow, text: 'Получите деньги сразу, но без вложений в машину' },
    { id: 'repair-sale', icon: TrendingUp, title: 'Ремонт → Продажа', amount: repairAndSale, text: recommended === 'repair-sale' ? 'Максимальная выгода. Вкладываете в ремонт, продаёте дороже' : 'Вкладываете в ремонт, затем продаёте автомобиль' },
    { id: 'keep', icon: CarFront, title: 'Ремонт → Эксплуатация', amount: result.scenarios.repair_and_keep.value, text: `Ремонт и расходы на владение за ${result.scenarios.repair_and_keep.years} год. Автомобиль остаётся у вас` },
  ]

  return (
    <>
      <section aria-labelledby="scenarios-title">
        <p className="text-[13px] leading-4 text-muted">
          <Link to="/home" className="rounded hover:text-forest">Главная</Link> /{' '}
          <Link to="/car" className="rounded hover:text-forest">Профиль авто</Link> /{' '}
          <Link to="/repair" className="rounded hover:text-forest">Результат</Link> / Сравнение сценариев
        </p>
        <h1 id="scenarios-title" tabIndex={-1} className="home-title">Что выгоднее: чинить или продавать?</h1>
      </section>

      <div className="scenarios-content">
        <div className="scenarios-context">
          <CarFront size={20} strokeWidth={1} aria-hidden="true" />
          <p>{car.brand} {car.model}, {car.year} • Стоимость ремонта: ~{formatMoney(repairCost)} ₽ • Цена авто сейчас: {formatMoney(priceNow)} ₽</p>
          <span className="text-xs leading-[15px] text-muted">Все суммы ориентировочные</span>
        </div>

        <div className="scenario-cards">
          {scenarios.map(({ id, icon: Icon, title, amount, text }) => (
            <article key={id} aria-labelledby={`${id}-title`} className={`scenario-card ${recommended === id ? 'scenario-card-recommended' : ''}`}>
              <div className="scenario-status">
                <Icon size={24} strokeWidth={1} aria-hidden="true" />
                {recommended === id && <span className="scenario-badge"><Check size={14} strokeWidth={1} aria-hidden="true" />Рекомендуем</span>}
              </div>
              <h2 id={`${id}-title`}>{title}</h2>
              <p className="scenario-amount">{amount < 0 ? '−' : '+'} {formatMoney(Math.abs(amount))} ₽</p>
              <p className="scenario-description">{text}</p>
            </article>
          ))}
        </div>

        <section className="scenario-reason" aria-label="Обоснование рекомендации">
          <div className="scenario-conclusion">
            <h2>{result.recommendation}</h2>
            <div id="scenario-math" className={expanded ? 'scenario-math' : 'hidden'}>
              <p>{formatMoney(priceAfterRepair)} − {formatMoney(repairCost)} = {formatMoney(repairAndSale)} ₽</p>
              <p>{formatMoney(repairAndSale)} − {formatMoney(priceNow)} = {formatMoney(result.profit)} ₽</p>
            </div>
          </div>
          <div className="min-w-0">
            <button type="button" className="scenario-why" aria-expanded={expanded} aria-controls="scenario-math scenario-explanation" onClick={() => setExpanded(!expanded)}>Почему так?</button>
            <p id="scenario-explanation" className={expanded ? 'scenario-explanation' : 'hidden'}>
              Если продать сейчас, вы получите {formatMoney(priceNow)} ₽. Если вложить {formatMoney(repairCost)} ₽ в ремонт, ориентировочная цена продажи составит {formatMoney(priceAfterRepair)} ₽.
            </p>
          </div>
        </section>

        <div className="scenario-actions">
          <button type="button" disabled={pending} onClick={() => { void saveCalculation() }} className="scenario-save"><Bookmark size={20} strokeWidth={1} aria-hidden="true" />{pending ? 'Сохраняем…' : 'Сохранить расчёт'}</button>
          <Link to="/home" onClick={onStartNew} className="scenario-new">Начать новый расчёт</Link>
        </div>
        {error && <p role="alert" className="text-sm leading-5 text-error">{error}</p>}
      </div>
    </>
  )
}
