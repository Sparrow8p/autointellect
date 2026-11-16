import { useEffect, useRef, useState } from 'react'
import { Plus, Search, Trash2, X } from 'lucide-react'
import { Link } from 'react-router-dom'
import { api, errorMessage } from '../lib/api'
import type { HistoryItem } from '../lib/api'

const pageSize = 100
const moneyFormatter = new Intl.NumberFormat('ru-RU')
const longDateFormatter = new Intl.DateTimeFormat('ru-RU', { day: '2-digit', month: 'short', year: 'numeric' })
const compactDateFormatter = new Intl.DateTimeFormat('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })
const timeFormatter = new Intl.DateTimeFormat('ru-RU', { hour: '2-digit', minute: '2-digit' })

function itemDetails(item: HistoryItem) {
  const date = new Date(item.created_at)
  const validDate = !Number.isNaN(date.getTime())
  return {
    carLabel: [item.car.brand, item.car.model, item.car.year].join(' '),
    date: validDate ? longDateFormatter.format(date).replace(/\s*г\.$/, '').replaceAll('.', '') : 'Дата не указана',
    compactDate: validDate ? compactDateFormatter.format(date) : 'Дата не указана',
    time: validDate ? timeFormatter.format(date) : '—',
  }
}

function repairRange(item: HistoryItem) {
  return moneyFormatter.format(item.repair_min) + ' — ' + moneyFormatter.format(item.repair_max) + ' ₽'
}

export function History({ onStartNew }: { onStartNew: () => void }) {
  const [items, setItems] = useState<HistoryItem[]>([])
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState<HistoryItem | null>(null)
  const [loading, setLoading] = useState(true)
  const [loaded, setLoaded] = useState(false)
  const [loadError, setLoadError] = useState('')
  const [hasMore, setHasMore] = useState(false)
  const [request, setRequest] = useState({ offset: 0, attempt: 0 })
  const nextOffset = useRef(0)
  const requestPending = useRef(true)
  const dialog = useRef<HTMLDialogElement>(null)

  useEffect(() => {
    const controller = new AbortController()
    requestPending.current = true
    void api<HistoryItem[]>('/history?limit=' + pageSize + '&offset=' + request.offset, { signal: controller.signal })
      .then((batch) => {
        if (controller.signal.aborted) return
        if (!Array.isArray(batch)) throw new Error('Не удалось прочитать историю расчётов.')
        setItems((previous) => {
          const ids = new Set(previous.map((item) => item.id))
          return [...previous, ...batch.filter((item) => {
            if (ids.has(item.id)) return false
            ids.add(item.id)
            return true
          })]
        })
        nextOffset.current = request.offset + batch.length
        setHasMore(batch.length === pageSize)
        setLoaded(true)
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted) setLoadError(errorMessage(error))
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          requestPending.current = false
          setLoading(false)
        }
      })

    return () => controller.abort()
  }, [request])

  useEffect(() => {
    if (selected && !dialog.current?.open) dialog.current?.showModal()
  }, [selected])

  function loadNextPage() {
    if (requestPending.current) return
    requestPending.current = true
    setLoading(true)
    setLoadError('')
    setRequest((previous) => ({ offset: nextOffset.current, attempt: previous.attempt + 1 }))
  }

  const query = search.trim().toLocaleLowerCase('ru-RU')
  const visibleItems = items
    .map((item) => ({ ...item, ...itemDetails(item) }))
    .filter((item) => [item.carLabel, item.date, item.compactDate]
      .some((text) => text.toLocaleLowerCase('ru-RU').includes(query)))
  const selectedDetails = selected ? itemDetails(selected) : null

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
          <table className="history-table" aria-busy={loading}>
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
                  <td data-label="Автомобиль и проблема">
                    <p className="history-car">{item.carLabel}</p>
                    <p className="history-problem">{item.problem_text?.trim() || 'Описание не указано'}</p>
                  </td>
                  <td data-label="Итог и рекомендация">
                    <p className="history-result">{item.recommendation || 'Рекомендация не указана'}</p>
                    <p className="history-result-detail">Ремонт: {repairRange(item)}</p>
                    <p className="history-recommendation text-muted">После ремонта: {moneyFormatter.format(item.price_after_repair)} ₽</p>
                  </td>
                  <td data-label="Действия">
                    <div className="history-row-actions">
                      <button type="button" onClick={() => setSelected(item)} aria-label={'Открыть расчёт: ' + item.carLabel + ', ' + item.date} className="history-open">Открыть</button>
                      <button type="button" disabled aria-label="Удалить расчёт" className="history-delete disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-transparent disabled:hover:text-muted"><Trash2 size={19} strokeWidth={1} aria-hidden="true" /></button>
                    </div>
                  </td>
                </tr>
              ))}
              {visibleItems.length === 0 && <tr><td colSpan={4} className="history-empty">
                {loading && !loaded ? 'Загружаем сохранённые расчёты…'
                  : loadError && !loaded ? 'Не удалось загрузить историю расчётов.'
                    : items.length === 0 ? 'Сохранённых расчётов пока нет.'
                      : 'Среди загруженных расчётов ничего не найдено.'}
              </td></tr>}
            </tbody>
          </table>
        </div>

        {loadError && <div role="alert" className="flex flex-wrap items-center gap-4 rounded-lg border border-line bg-white p-4 text-sm leading-5">
          <p className="flex-1 text-error">{loadError}</p>
          <button type="button" onClick={loadNextPage} disabled={loading} className="history-open disabled:opacity-50">Повторить загрузку</button>
        </div>}

        {loaded && <p role="status" className="text-[13px] leading-4 text-muted">Показано {visibleItems.length} из {items.length} загруженных · Оценки актуальны на дату расчёта</p>}
        {hasMore && !loadError && <div className="flex flex-wrap items-center gap-4">
          <button type="button" onClick={loadNextPage} disabled={loading} className="repair-action repair-action-secondary disabled:cursor-wait disabled:opacity-50">{loading ? 'Загружаем…' : 'Загрузить ещё'}</button>
          {query && <p className="text-xs leading-5 text-muted">Поиск выполняется среди загруженных расчётов.</p>}
        </div>}
      </div>

      <dialog
        ref={dialog}
        aria-labelledby="history-details-title"
        className="history-dialog"
        onClose={() => setSelected(null)}
        onClick={(event) => { if (event.target === event.currentTarget) dialog.current?.close() }}
      >
        {selected && selectedDetails && <>
          <div className="flex items-start justify-between gap-4">
            <h2 id="history-details-title" className="text-xl leading-6 font-semibold">{selectedDetails.carLabel}</h2>
            <button type="button" onClick={() => dialog.current?.close()} aria-label="Закрыть расчёт" className="history-dialog-close"><X size={20} aria-hidden="true" /></button>
          </div>
          <p className="mt-3 text-sm text-muted">{selectedDetails.date} · {selectedDetails.time}</p>
          <dl className="mt-6 grid gap-5 text-sm leading-6">
            <div><dt className="text-muted">Проблема</dt><dd>{selected.problem_text?.trim() || 'Описание не указано'}</dd></div>
            <div><dt className="text-muted">Рекомендация</dt><dd>{selected.recommendation || 'Рекомендация не указана'}</dd></div>
            <div><dt className="text-muted">Стоимость ремонта</dt><dd>{repairRange(selected)}</dd></div>
            <div><dt className="text-muted">Цена автомобиля на дату расчёта</dt><dd>{moneyFormatter.format(selected.price_as_is)} ₽</dd></div>
            <div><dt className="text-muted">Оценка цены после ремонта</dt><dd>{moneyFormatter.format(selected.price_after_repair)} ₽</dd></div>
          </dl>
          <button type="button" onClick={() => dialog.current?.close()} className="repair-action repair-action-primary mt-6 w-full">Закрыть</button>
        </>}
      </dialog>
    </>
  )
}
