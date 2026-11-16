import { useRef, useState } from 'react'
import { Plus, Search, Trash2, X } from 'lucide-react'
import { Link } from 'react-router-dom'

const exampleHistory = [
  { id: 1, date: '12 окт 2026', compactDate: '12.10.2026', time: '14:30', car: 'Hyundai Solaris 2018', problem: 'Стук в подвеске', result: 'Ремонт окупится. Выгода +79 000 ₽', detail: '', scenario: 'Ремонт → Продажа', profitable: true },
  { id: 2, date: '09 окт 2026', compactDate: '09.10.2026', time: '10:15', car: 'Kia Rio 2016', problem: 'Замена сцепления', result: 'Выгоднее продать как есть.', detail: 'Ремонт не окупится', scenario: 'Продать как есть', profitable: false },
  { id: 3, date: '04 окт 2026', compactDate: '04.10.2026', time: '18:45', car: 'Škoda Octavia 2020', problem: 'Замена тормозных дисков', result: 'Разумно оставить автомобиль.', detail: 'Ремонт ~32 000 ₽', scenario: 'Ремонт → Эксплуатация', profitable: false },
  { id: 4, date: '28 сен 2026', compactDate: '28.09.2026', time: '12:05', car: 'Renault Duster 2019', problem: 'Не заводится', result: 'Ремонт окупится. Выгода +46 000 ₽', detail: '', scenario: 'Ремонт → Продажа', profitable: true },
]

type HistoryItem = typeof exampleHistory[number]

export function History({ onStartNew }: { onStartNew: () => void }) {
  const [items, setItems] = useState(exampleHistory)
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState<HistoryItem | null>(null)
  const dialog = useRef<HTMLDialogElement>(null)
  const query = search.trim().toLocaleLowerCase('ru-RU')
  const visibleItems = items.filter((item) => [item.car, item.date, item.compactDate].some((text) => text.toLocaleLowerCase('ru-RU').includes(query)))

  return (
    <>
      <section aria-labelledby="history-title">
        <p className="text-[13px] leading-4 text-muted">Ваши сохранённые решения</p>
        <h1 id="history-title" tabIndex={-1} className="home-title">История расчётов</h1>
      </section>

      <div className="history-content">
        <div className="history-toolbar">
          <p className="text-sm leading-[17px] text-muted">Сохранённые расчёты</p>
          <div className="history-tools">
            <div className="history-search">
              <Search size={20} strokeWidth={1} aria-hidden="true" />
              <label htmlFor="history-search" className="sr-only">Поиск по марке авто или дате</label>
              <input id="history-search" type="search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Поиск по марке авто или дате..." />
            </div>
            <Link to="/home" onClick={onStartNew} className="history-new"><Plus size={20} strokeWidth={1} aria-hidden="true" />Новый расчёт</Link>
          </div>
        </div>

        <div className="history-table-wrap">
          <table className="history-table">
            <caption className="sr-only">Сохранённые расчёты автомобилей</caption>
            <colgroup><col className="history-col-date" /><col className="history-col-car" /><col className="history-col-result" /><col className="history-col-actions" /></colgroup>
            <thead><tr><th scope="col">ДАТА</th><th scope="col">АВТОМОБИЛЬ И ПРОБЛЕМА</th><th scope="col">ИТОГ И РЕКОМЕНДАЦИЯ</th><th scope="col">ДЕЙСТВИЯ</th></tr></thead>
            <tbody>
              {visibleItems.map((item) => (
                <tr key={item.id} className="history-row">
                  <td data-label="Дата">
                    <p className="history-long-date">{item.date}</p>
                    <p className="history-compact-date">{item.compactDate}</p>
                    <p className="history-time">{item.time}</p>
                  </td>
                  <td data-label="Автомобиль и проблема"><p className="history-car">{item.car}</p><p className="history-problem">{item.problem}</p></td>
                  <td data-label="Итог и рекомендация">
                    <p className="history-result">{item.result}</p>
                    {item.detail && <p className="history-result-detail">{item.detail}</p>}
                    <p className={`history-recommendation ${item.profitable ? 'text-forest' : 'text-muted'}`}>{item.scenario}</p>
                  </td>
                  <td data-label="Действия">
                    <div className="history-row-actions">
                      <button type="button" onClick={() => { setSelected(item); dialog.current?.showModal() }} aria-label={`Открыть расчёт: ${item.car}, ${item.date}`} className="history-open">Открыть</button>
                      <button type="button" onClick={() => setItems((previous) => previous.filter((row) => row.id !== item.id))} aria-label={`Удалить расчёт: ${item.car}, ${item.date}`} title="Удалить расчёт" className="history-delete"><Trash2 size={19} strokeWidth={1} aria-hidden="true" /></button>
                    </div>
                  </td>
                </tr>
              ))}
              {visibleItems.length === 0 && <tr><td colSpan={4} className="history-empty">{items.length === 0 ? 'Сохранённых расчётов пока нет.' : 'По вашему запросу ничего не найдено.'}</td></tr>}
            </tbody>
          </table>
        </div>

        <p role="status" className="text-[13px] leading-4 text-muted">Показано {visibleItems.length} из {items.length} · Оценки актуальны на дату расчёта</p>
      </div>
      <p className="mt-4 text-xs leading-5 text-muted">Примеры из макета. Поиск и удаление работают в пределах этой страницы.</p>

      <dialog ref={dialog} aria-labelledby="history-details-title" className="history-dialog" onClick={(event) => { if (event.target === event.currentTarget) dialog.current?.close() }}>
        {selected && <>
          <div className="flex items-start justify-between gap-4">
            <h2 id="history-details-title" className="text-xl leading-6 font-semibold">{selected.car}</h2>
            <button type="button" onClick={() => dialog.current?.close()} aria-label="Закрыть расчёт" className="history-dialog-close"><X size={20} aria-hidden="true" /></button>
          </div>
          <p className="mt-3 text-sm text-muted">{selected.date} · {selected.time}</p>
          <dl className="mt-6 grid gap-5 text-sm leading-6">
            <div><dt className="text-muted">Проблема</dt><dd>{selected.problem}</dd></div>
            <div><dt className="text-muted">Итог</dt><dd>{selected.result}</dd>{selected.detail && <dd>{selected.detail}</dd>}</div>
            <div><dt className="text-muted">Сценарий</dt><dd className={selected.profitable ? 'text-forest' : ''}>{selected.scenario}</dd></div>
          </dl>
          <button type="button" onClick={() => dialog.current?.close()} className="repair-action repair-action-primary mt-6 w-full">Закрыть</button>
        </>}
      </dialog>
    </>
  )
}
