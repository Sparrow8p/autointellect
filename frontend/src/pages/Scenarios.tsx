import { useState } from 'react'
import { Banknote, Bookmark, CarFront, Check, TrendingUp } from 'lucide-react'
import { Link } from 'react-router-dom'
import type { CarProfileDraft } from '../types/carProfile'

const repairCost = 21000
const priceAfterRepair = 680000
const repairAndSale = priceAfterRepair - repairCost
const formatMoney = (value: number) => value.toLocaleString('ru-RU')
const exampleCar = { brand: 'Hyundai', model: 'Solaris', year: '2018' }

export function Scenarios({ car, priceAsIs, onStartNew }: {
  car: CarProfileDraft
  priceAsIs: string
  onStartNew: () => void
}) {
  const [expanded, setExpanded] = useState(true)
  const [notice, setNotice] = useState('')
  const hasCar = Boolean(car.brand && car.model && car.year && car.region && /^\d+$/.test(car.mileage.replace(/\s/g, '')))
  const selectedCar = hasCar ? car : exampleCar
  const digits = priceAsIs.replace(/\s/g, '')
  const priceNow = /^\d+$/.test(digits) && Number.isSafeInteger(Number(digits)) ? Number(digits) : null
  const benefit = priceNow === null ? null : repairAndSale - priceNow
  const recommended = benefit === null || benefit === 0 ? null : benefit > 0 ? 'repair-sale' : 'sell'
  const conclusion = benefit === null ? 'Укажите цену для сравнения'
    : benefit > 0 ? `Ремонт окупится. Выгода ~${formatMoney(benefit)} ₽`
      : benefit < 0 ? 'Выгоднее продать как есть' : 'Варианты равноценны по сумме'

  const scenarios = [
    { id: 'sell', icon: Banknote, title: 'Продать как есть', amount: priceNow, text: 'Получите деньги сразу, но без вложений в машину' },
    { id: 'repair-sale', icon: TrendingUp, title: 'Ремонт → Продажа', amount: repairAndSale, text: recommended === 'repair-sale' ? 'Максимальная выгода. Вкладываете в ремонт, продаёте дороже' : 'Вкладываете в ремонт, затем продаёте автомобиль' },
    { id: 'keep', icon: CarFront, title: 'Ремонт → Эксплуатация', amount: -repairCost, text: 'Остаётесь на машине. Тратите на ремонт, но не продаёте' },
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
          <p>{selectedCar.brand} {selectedCar.model}, {selectedCar.year} • Стоимость ремонта: ~{formatMoney(repairCost)} ₽ • Цена авто сейчас: {priceNow === null ? <Link to="/valuation" className="text-forest underline">Указать цену</Link> : `${formatMoney(priceNow)} ₽`}</p>
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
              <p className="scenario-amount">{amount === null ? '—' : `${amount < 0 ? '−' : '+'} ${formatMoney(Math.abs(amount))} ₽`}</p>
              <p className="scenario-description">{text}</p>
            </article>
          ))}
        </div>

        <section className="scenario-reason" aria-label="Обоснование рекомендации">
          <div className="scenario-conclusion">
            <h2>{conclusion}</h2>
            <div id="scenario-math" className={expanded ? 'scenario-math' : 'hidden'}>
              <p>{formatMoney(priceAfterRepair)} − {formatMoney(repairCost)} = {formatMoney(repairAndSale)} ₽</p>
              <p>{priceNow === null ? 'Укажите цену на предыдущем шаге.' : `${formatMoney(Math.max(repairAndSale, priceNow))} − ${formatMoney(Math.min(repairAndSale, priceNow))} = ${formatMoney(Math.abs(repairAndSale - priceNow))} ₽`}</p>
            </div>
          </div>
          <div className="min-w-0">
            <button type="button" className="scenario-why" aria-expanded={expanded} aria-controls="scenario-math scenario-explanation" onClick={() => setExpanded(!expanded)}>Почему так?</button>
            <p id="scenario-explanation" className={expanded ? 'scenario-explanation' : 'hidden'}>
              {priceNow === null ? <Link to="/valuation" className="text-forest underline">Вернитесь к оценке авто и укажите корректную цену продажи.</Link> : <>Если продать сейчас, вы получите {formatMoney(priceNow)} ₽. Если вложить {formatMoney(repairCost)} ₽ в ремонт, вы продадите машину за {formatMoney(priceAfterRepair)} ₽</>}
            </p>
          </div>
        </section>

        <div className="scenario-actions">
          <button type="button" disabled={priceNow === null} onClick={() => setNotice('Сохранение расчётов пока недоступно.')} className="scenario-save"><Bookmark size={20} strokeWidth={1} aria-hidden="true" />Сохранить расчёт</button>
          <Link to="/home" onClick={onStartNew} className="scenario-new">Начать новый расчёт</Link>
        </div>
        {notice && <p role="status" className="text-sm leading-5 text-muted">{notice}</p>}
      </div>
      <p className="mt-6 text-xs leading-5 text-muted">Пример из макета. Реальный расчёт и рекомендация пока не подключены.</p>
    </>
  )
}
