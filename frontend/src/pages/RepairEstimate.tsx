import { Bookmark, CarFront, ChevronDown, Info } from 'lucide-react'
import { Link } from 'react-router-dom'
import type { ApiCar, EstimateResult } from '../lib/api'

export function RepairEstimate({ car: selectedCar, problem: selectedProblem, estimate }: { car: ApiCar; problem: string; estimate: EstimateResult }) {
  const mileage = selectedCar.mileage.toLocaleString('ru-RU')

  return (
    <>
      <section aria-labelledby="repair-title">
        <p className="text-[13px] leading-4 text-muted">
          <Link to="/home" className="rounded hover:text-forest">Главная</Link> /{' '}
          <Link to="/car" className="rounded hover:text-forest">Профиль авто</Link> / Результат
        </p>
        <h1 id="repair-title" tabIndex={-1} className="home-title">Стоимость ремонта</h1>
      </section>

      <div className="repair-content">
        <section className="repair-estimate" aria-label="Оценка ремонта">
          <div className="repair-range">
            <p className="text-[13px] leading-4 font-medium text-muted">ОРИЕНТИРОВОЧНАЯ СТОИМОСТЬ</p>
            <p className="repair-price">Обычно от {estimate.min_price.toLocaleString('ru-RU')} до {estimate.max_price.toLocaleString('ru-RU')} ₽</p>
            <p className="repair-context">Для вашего {selectedCar.brand} {selectedCar.model} {selectedCar.year} {selectedCar.region === 'Москва' ? 'в Москве' : `· ${selectedCar.region}`}</p>
          </div>

          <div className="repair-confidence">
            <Info size={22} strokeWidth={1} aria-hidden="true" />
            <div>
              <h2 className="text-sm leading-[17px] font-semibold text-forest">Уверенность: {estimate.recognized ? 'Средняя' : 'Низкая'}</h2>
              <p className="mt-1 text-[13px] leading-4 text-muted">{estimate.recognized ? 'Расчёт сделан по описанию, без осмотра автомобиля.' : 'Проблему не удалось распознать. В сумму включена только диагностика.'}</p>
            </div>
          </div>

          <details className="repair-details">
            <summary><h2>Что может изменить цену</h2><ChevronDown size={20} strokeWidth={1} aria-hidden="true" /></summary>
            <ul className="repair-details-body list-disc space-y-2 pl-10">
              <li>Скрытые повреждения, которые обнаружатся при осмотре.</li>
              <li>Выбор оригинальных запчастей или аналогов.</li>
              <li>Объём и стоимость работ в выбранном сервисе.</li>
            </ul>
          </details>

          <details className="repair-details">
            <summary><h2>Что НЕ входит в эту сумму</h2><ChevronDown size={20} strokeWidth={1} aria-hidden="true" /></summary>
            <p className="repair-details-body">Дополнительные неисправности и работы, не связанные с описанной проблемой. Окончательный состав работ уточняется после диагностики.</p>
          </details>
        </section>

        <aside className="repair-summary" aria-labelledby="repair-summary-title">
          <h2 id="repair-summary-title" className="text-xl leading-6 font-semibold">Ваш расчёт</h2>
          <div className="repair-car">
            <span className="repair-car-icon"><CarFront size={28} strokeWidth={1} aria-hidden="true" /></span>
            <div className="min-w-0 wrap-anywhere">
              <p className="text-base leading-[19px] font-semibold">{selectedCar.brand} {selectedCar.model}</p>
              <p className="mt-1 text-[13px] leading-4 text-muted">{selectedCar.year} · {mileage} км · {selectedCar.region}</p>
            </div>
          </div>
          <hr className="border-0 border-t border-line" />
          <div>
            <p className="text-[13px] leading-4 text-muted">Проблема</p>
            <p className="mt-1.5 text-base leading-[19px] wrap-anywhere">{selectedProblem}</p>
          </div>
          <div className="grid gap-3">
            <Link to="/valuation" className="repair-action repair-action-primary">Оценить стоимость авто</Link>
            <Link to="/valuation" className="repair-action repair-action-secondary"><Bookmark size={20} strokeWidth={1} aria-hidden="true" />Сохранить расчёт</Link>
          </div>
          <p className="text-xs leading-[1.45] text-muted">Сравните стоимость ремонта и продажи, прежде чем принимать решение.</p>
        </aside>
      </div>
    </>
  )
}
