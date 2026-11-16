import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { CarFront, Check, ChevronDown, Gauge, MapPin } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import { api, ApiError, errorMessage } from '../lib/api'
import type { ApiCar, EstimateResult, ReferenceItem } from '../lib/api'
import { saveCarProfile } from '../lib/carProfileStorage'
import type { CarProfileDraft } from '../types/carProfile'

type FieldName = Exclude<keyof CarProfileDraft, 'saveToProfile'>
type FieldErrors = Partial<Record<FieldName, string>>
type Catalog = { brands: ReferenceItem[]; regions: ReferenceItem[]; attempt: number; error: string }
type ModelCatalog = { items: ReferenceItem[]; brand: string; attempt: number; error: string }

const currentYear = new Date().getFullYear() + 1
const years = Array.from({ length: currentYear - 1899 }, (_, index) => String(currentYear - index))
const fieldOrder: FieldName[] = ['brand', 'model', 'year', 'mileage', 'region']

function validateCar(draft: CarProfileDraft, catalog: Catalog, models: ReferenceItem[]): FieldErrors {
  const errors: FieldErrors = {}
  if (!catalog.brands.some((brand) => brand.name === draft.brand)) errors.brand = 'Выберите марку автомобиля.'
  if (!models.some((model) => model.name === draft.model)) errors.model = 'Выберите модель автомобиля.'
  if (!years.includes(draft.year)) errors.year = 'Выберите год выпуска.'
  const mileage = draft.mileage.replace(/\s/g, '')
  if (!mileage) errors.mileage = 'Укажите пробег. Для нового автомобиля введите 0.'
  else if (!/^\d+$/.test(mileage) || Number(mileage) > 5_000_000) errors.mileage = 'Введите целый пробег от 0 до 5 000 000 км.'
  if (!catalog.regions.some((region) => region.name === draft.region)) errors.region = 'Выберите регион из списка.'
  return errors
}

function formatMileage(value: string) {
  const digits = value.replace(/\s/g, '')
  if (!/^\d+$/.test(digits) || Number(digits) > 5_000_000) return value
  return new Intl.NumberFormat('ru-RU').format(Number(digits)).replace(/[\u00a0\u202f]/g, ' ')
}

const explanations = [
  { icon: CarFront, title: 'Марка и модель', text: 'Нужны для подбора нормо-часов и совместимости запчастей.' },
  { icon: Gauge, title: 'Год и пробег', text: 'Влияют на износ и амортизацию автомобиля.' },
  { icon: MapPin, title: 'Регион', text: 'Определяет стоимость работ: в Москве и Санкт-Петербурге цены выше.' },
]

export function CarProfile({ draft, onDraftChange, problem, onCalculated }: {
  draft: CarProfileDraft
  onDraftChange: (draft: CarProfileDraft) => void
  problem: string
  onCalculated: (car: ApiCar, estimate: EstimateResult) => void
}) {
  const navigate = useNavigate()
  const [errors, setErrors] = useState<FieldErrors>({})
  const [requestError, setRequestError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [catalogAttempt, setCatalogAttempt] = useState(0)
  const [modelAttempt, setModelAttempt] = useState(0)
  const [catalog, setCatalog] = useState<Catalog>({ brands: [], regions: [], attempt: -1, error: '' })
  const [modelCatalog, setModelCatalog] = useState<ModelCatalog>({ items: [], brand: '', attempt: -1, error: '' })
  const submitController = useRef<AbortController | null>(null)
  const createdCar = useRef<{ key: string; car: ApiCar } | null>(null)
  const catalogLoading = catalog.attempt !== catalogAttempt
  const catalogError = catalogLoading ? '' : catalog.error
  const modelsLoading = Boolean(draft.brand) && (modelCatalog.brand !== draft.brand || modelCatalog.attempt !== modelAttempt)
  const models = modelCatalog.brand === draft.brand && !modelsLoading ? modelCatalog.items : []
  const modelsError = draft.brand && !modelsLoading ? modelCatalog.error : ''
  const problemText = problem.trim()
  const validProblem = problemText.length >= 2 && problemText.length <= 2000
  const busy = submitting || catalogLoading || modelsLoading || Boolean(catalogError) || Boolean(modelsError)

  useEffect(() => {
    const controller = new AbortController()
    Promise.all([
      api<ReferenceItem[]>('/reference/brands', { signal: controller.signal }),
      api<ReferenceItem[]>('/reference/regions', { signal: controller.signal }),
    ]).then(([brands, regions]) => {
      if (!controller.signal.aborted) setCatalog({
        brands, regions, attempt: catalogAttempt,
        error: brands.length && regions.length ? '' : 'На сервере пока нет марок или регионов.',
      })
    }).catch((error: unknown) => {
      if (!controller.signal.aborted) setCatalog({ brands: [], regions: [], attempt: catalogAttempt, error: errorMessage(error) })
    })
    return () => controller.abort()
  }, [catalogAttempt])

  useEffect(() => {
    if (!draft.brand) return
    const controller = new AbortController()
    api<ReferenceItem[]>('/reference/models?brand=' + encodeURIComponent(draft.brand), { signal: controller.signal })
      .then((items) => {
        if (!controller.signal.aborted) setModelCatalog({
          items, brand: draft.brand, attempt: modelAttempt,
          error: items.length ? '' : 'Для этой марки пока нет моделей.',
        })
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted) setModelCatalog({ items: [], brand: draft.brand, attempt: modelAttempt, error: errorMessage(error) })
      })
    return () => controller.abort()
  }, [draft.brand, modelAttempt])

  useEffect(() => () => submitController.current?.abort(), [])

  function updateField(field: FieldName, value: string) {
    onDraftChange({ ...draft, [field]: value, ...(field === 'brand' ? { model: '' } : {}) })
    setErrors((previous) => ({ ...previous, [field]: undefined, ...(field === 'brand' ? { model: undefined } : {}) }))
    setRequestError('')
  }

  function goBack() {
    if (typeof window.history.state?.idx === 'number' && window.history.state.idx > 0) void navigate(-1)
    else void navigate('/home', { replace: true })
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (busy || submitController.current) return
    const nextErrors = validateCar(draft, catalog, models)
    setErrors(nextErrors)
    const firstError = fieldOrder.find((field) => nextErrors[field])
    if (firstError) {
      document.getElementById('car-' + firstError)?.focus()
      return
    }
    if (!validProblem) return

    setRequestError('')
    const normalized = { ...draft, mileage: draft.mileage.replace(/\s/g, ''), region: draft.region.trim() }
    try {
      saveCarProfile(normalized)
    } catch {
      setRequestError(draft.saveToProfile
        ? 'Не удалось запомнить данные в браузере. Разрешите локальное хранилище или снимите флажок.'
        : 'Не удалось удалить ранее сохранённый автомобиль. Разрешите изменение локального хранилища и повторите попытку.')
      return
    }

    const payload = { brand: normalized.brand, model: normalized.model, year: Number(normalized.year), mileage: Number(normalized.mileage), region: normalized.region }
    const key = JSON.stringify(payload)
    const controller = new AbortController()
    submitController.current = controller
    setSubmitting(true)
    try {
      let serverCar = createdCar.current?.key === key ? createdCar.current.car : null
      if (!serverCar) {
        serverCar = await api<ApiCar>('/cars', { method: 'POST', body: payload, signal: controller.signal })
        if (controller.signal.aborted) return
        createdCar.current = { key, car: serverCar }
      }
      const estimate = await api<EstimateResult>('/calculations/estimate', {
        method: 'POST', body: { car_id: serverCar.id, problem_text: problemText }, signal: controller.signal,
      })
      if (controller.signal.aborted) return
      onDraftChange({ ...normalized, mileage: formatMileage(normalized.mileage) })
      onCalculated(serverCar, estimate)
      void navigate('/repair')
    } catch (error) {
      if (!controller.signal.aborted) {
        if (error instanceof ApiError && error.status === 404) createdCar.current = null
        setRequestError(errorMessage(error))
      }
    } finally {
      if (submitController.current === controller) submitController.current = null
      if (!controller.signal.aborted) setSubmitting(false)
    }
  }

  return (
    <>
      <section aria-labelledby="car-title">
        <p className="text-[13px] leading-4 text-muted"><Link to="/home" className="rounded hover:text-forest">Главная</Link> / Профиль авто</p>
        <h1 id="car-title" tabIndex={-1} className="home-title">Данные об автомобиле</h1>
      </section>

      <div className="car-content">
        <form onSubmit={handleSubmit} noValidate className="car-form" aria-busy={submitting}>
          <div role="progressbar" aria-label="Прогресс оценки" aria-valuemin={0} aria-valuemax={100} aria-valuenow={50} aria-valuetext="Данные автомобиля: второй этап оценки" className="car-progress"><span /></div>
          {catalogLoading && <p role="status" className="text-sm text-muted">Загружаем марки и регионы…</p>}
          {catalogError && <div role="alert" className="car-submit-error">{catalogError} <button type="button" disabled={submitting} onClick={() => setCatalogAttempt((attempt) => attempt + 1)} className="rounded underline">Повторить загрузку</button></div>}

          <div className="car-form-card">
            <div className="car-field-row">
              <div className="car-field">
                <label htmlFor="car-brand">Марка</label>
                <div className="car-select-wrap">
                  <select id="car-brand" name="brand" required disabled={submitting || catalogLoading || Boolean(catalogError)} value={catalog.brands.some((brand) => brand.name === draft.brand) ? draft.brand : ''} onChange={(event) => updateField('brand', event.target.value)} aria-invalid={Boolean(errors.brand)} aria-describedby={errors.brand ? 'brand-error' : undefined} className="car-control">
                    <option value="">Выберите марку</option>
                    {catalog.brands.map((brand) => <option key={brand.id} value={brand.name}>{brand.name}</option>)}
                  </select>
                  <ChevronDown size={18} strokeWidth={1} aria-hidden="true" />
                </div>
                {errors.brand && <p id="brand-error" className="car-field-error">{errors.brand}</p>}
              </div>

              <div className="car-field">
                <label htmlFor="car-model">Модель</label>
                <div className="car-select-wrap">
                  <select id="car-model" name="model" required disabled={submitting || catalogLoading || Boolean(catalogError) || !draft.brand || modelsLoading || Boolean(modelsError)} value={models.some((model) => model.name === draft.model) ? draft.model : ''} onChange={(event) => updateField('model', event.target.value)} aria-invalid={Boolean(errors.model)} aria-describedby={errors.model ? 'model-error' : modelsError ? 'model-load-error' : undefined} className="car-control">
                    <option value="">{modelsLoading ? 'Загружаем модели…' : draft.brand ? 'Выберите модель' : 'Сначала выберите марку'}</option>
                    {models.map((model) => <option key={model.id} value={model.name}>{model.name}</option>)}
                  </select>
                  <ChevronDown size={18} strokeWidth={1} aria-hidden="true" />
                </div>
                {modelsError && <p id="model-load-error" role="alert" className="car-field-error">{modelsError} <button type="button" disabled={submitting} onClick={() => setModelAttempt((attempt) => attempt + 1)} className="rounded underline">Повторить</button></p>}
                {errors.model && <p id="model-error" className="car-field-error">{errors.model}</p>}
              </div>
            </div>

            <div className="car-field-row">
              <div className="car-field">
                <label htmlFor="car-year">Год выпуска</label>
                <div className="car-select-wrap">
                  <select id="car-year" name="year" required disabled={submitting} value={draft.year} onChange={(event) => updateField('year', event.target.value)} aria-invalid={Boolean(errors.year)} aria-describedby={errors.year ? 'year-error' : undefined} className="car-control">
                    <option value="">Выберите год</option>
                    {years.map((year) => <option key={year} value={year}>{year}</option>)}
                  </select>
                  <ChevronDown size={18} strokeWidth={1} aria-hidden="true" />
                </div>
                {errors.year && <p id="year-error" className="car-field-error">{errors.year}</p>}
              </div>

              <div className="car-field">
                <label htmlFor="car-mileage">Пробег (км)</label>
                <input id="car-mileage" name="mileage" type="text" inputMode="numeric" required disabled={submitting} maxLength={20} placeholder="Например, 85 000" value={draft.mileage} onChange={(event) => updateField('mileage', event.target.value)} onBlur={() => updateField('mileage', formatMileage(draft.mileage))} aria-invalid={Boolean(errors.mileage)} aria-describedby={errors.mileage ? 'mileage-error' : undefined} className="car-control" />
                {errors.mileage && <p id="mileage-error" className="car-field-error">{errors.mileage}</p>}
              </div>
            </div>

            <div className="car-field">
              <label htmlFor="car-region">Регион</label>
              <div className="car-select-wrap">
                <select id="car-region" name="region" required disabled={submitting || catalogLoading || Boolean(catalogError)} value={catalog.regions.some((region) => region.name === draft.region) ? draft.region : ''} onChange={(event) => updateField('region', event.target.value)} aria-invalid={Boolean(errors.region)} aria-describedby={errors.region ? 'region-error' : undefined} className="car-control">
                  <option value="">Выберите регион</option>
                  {catalog.regions.map((region) => <option key={region.id} value={region.name}>{region.name}</option>)}
                </select>
                <ChevronDown size={18} strokeWidth={1} aria-hidden="true" />
              </div>
              {errors.region && <p id="region-error" className="car-field-error">{errors.region}</p>}
            </div>

            <label className="car-save-label" htmlFor="car-save">
              <span className="relative flex shrink-0"><input type="checkbox" id="car-save" disabled={submitting} checked={draft.saveToProfile} onChange={(event) => { onDraftChange({ ...draft, saveToProfile: event.target.checked }); setRequestError('') }} aria-describedby="car-storage-note" className="car-checkbox" />{draft.saveToProfile && <Check size={14} strokeWidth={1} className="pointer-events-none absolute top-[3px] left-[3px] text-white" aria-hidden="true" />}</span>
              Запомнить автомобиль в этом браузере
            </label>
          </div>

          {!validProblem && <p className="car-submit-error">Для расчёта нужно описание проблемы от 2 до 2000 символов. <Link to="/home" className="rounded underline">Укажите проблему на главной.</Link></p>}
          {Object.values(errors).some(Boolean) && <p role="alert" className="car-submit-error">Проверьте отмеченные поля.</p>}
          {requestError && <p role="alert" className="car-submit-error">{requestError}</p>}
          <div className="car-actions">
            <button type="button" onClick={goBack} className="car-back">Назад</button>
            <button type="submit" disabled={busy} className="car-continue disabled:cursor-not-allowed disabled:opacity-50">{submitting ? 'Рассчитываем…' : 'Сохранить и продолжить'}</button>
          </div>
          <p id="car-storage-note" className="car-prototype-note">Запомните автомобиль, чтобы не вводить его данные заново в этом браузере.</p>
        </form>

        <aside className="car-help">
          <section className="car-help-card" aria-labelledby="car-help-title">
            <h2 id="car-help-title">Зачем мы это спрашиваем?</h2>
            {explanations.map(({ icon: Icon, title, text }) => <div key={title} className="car-explanation"><Icon size={20} strokeWidth={1} aria-hidden="true" /><div><h3>{title}</h3><p>{text}</p></div></div>)}
          </section>
          <p className="car-mileage-tip">Не знаете точный пробег? Укажите примерный — это не сильно повлияет на диапазон цены</p>
        </aside>
      </div>
    </>
  )
}
