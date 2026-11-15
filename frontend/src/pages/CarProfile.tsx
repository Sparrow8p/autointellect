import { useState } from 'react'
import type { FormEvent } from 'react'
import { CarFront, Check, ChevronDown, Gauge, MapPin } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import { carBrands, carModels, carRegions } from '../data/carCatalog'
import { saveCarProfile } from '../lib/carProfileStorage'
import type { CarProfileDraft } from '../types/carProfile'

type FieldName = Exclude<keyof CarProfileDraft, 'saveToProfile'>
type FieldErrors = Partial<Record<FieldName, string>>

const currentYear = new Date().getFullYear()
const years = Array.from({ length: currentYear - 1899 }, (_, index) => String(currentYear - index))
const fieldOrder: FieldName[] = ['brand', 'model', 'year', 'mileage', 'region']

function validateCar(draft: CarProfileDraft): FieldErrors {
  const errors: FieldErrors = {}
  if (!carBrands.includes(draft.brand)) errors.brand = 'Выберите марку автомобиля.'
  if (!carModels[draft.brand]?.includes(draft.model)) errors.model = 'Выберите модель автомобиля.'
  if (!years.includes(draft.year)) errors.year = 'Выберите год выпуска.'
  const mileage = draft.mileage.replace(/\s/g, '')
  if (!mileage) errors.mileage = 'Укажите пробег. Для нового автомобиля введите 0.'
  else if (!/^\d+$/.test(mileage) || Number(mileage) > 2_147_483_647) errors.mileage = 'Введите пробег целым неотрицательным числом.'
  if (!draft.region.trim()) errors.region = 'Выберите или укажите регион.'
  return errors
}

function formatMileage(value: string) {
  const digits = value.replace(/\s/g, '')
  if (!/^\d+$/.test(digits) || Number(digits) > 2_147_483_647) return value
  return new Intl.NumberFormat('ru-RU').format(Number(digits)).replace(/[\u00a0\u202f]/g, ' ')
}

const explanations = [
  { icon: CarFront, title: 'Марка и модель', text: 'Нужны для подбора нормо-часов и совместимости запчастей.' },
  { icon: Gauge, title: 'Год и пробег', text: 'Влияют на износ и амортизацию автомобиля.' },
  { icon: MapPin, title: 'Регион', text: 'Определяет стоимость работ: в Москве и Санкт-Петербурге цены выше.' },
]

export function CarProfile({ draft, onDraftChange }: { draft: CarProfileDraft; onDraftChange: (draft: CarProfileDraft) => void }) {
  const navigate = useNavigate()
  const [errors, setErrors] = useState<FieldErrors>({})
  const [storageError, setStorageError] = useState('')
  const [customRegion, setCustomRegion] = useState(() => Boolean(draft.region) && !carRegions.includes(draft.region))
  const models = carModels[draft.brand] ?? []

  function updateField(field: FieldName, value: string) {
    onDraftChange({ ...draft, [field]: value, ...(field === 'brand' ? { model: '' } : {}) })
    setErrors((previous) => ({ ...previous, [field]: undefined, ...(field === 'brand' ? { model: undefined } : {}) }))
    setStorageError('')
  }

  function goBack() {
    if (typeof window.history.state?.idx === 'number' && window.history.state.idx > 0) void navigate(-1)
    else void navigate('/home', { replace: true })
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const nextErrors = validateCar(draft)
    setErrors(nextErrors)
    const firstError = fieldOrder.find((field) => nextErrors[field])
    if (firstError) {
      document.getElementById(firstError === 'region' && customRegion ? 'car-region-custom' : `car-${firstError}`)?.focus()
      return
    }

    const normalized = { ...draft, mileage: draft.mileage.replace(/\s/g, ''), region: draft.region.trim() }
    try {
      saveCarProfile(normalized)
    } catch {
      setStorageError(draft.saveToProfile
        ? 'Не удалось сохранить данные в браузере. Разрешите локальное хранилище или снимите флажок сохранения.'
        : 'Не удалось удалить ранее сохранённый автомобиль. Разрешите изменение локального хранилища и повторите попытку.')
      return
    }
    onDraftChange({ ...normalized, mileage: formatMileage(normalized.mileage) })
    void navigate('/repair')
  }

  return (
    <>
      <section aria-labelledby="car-title">
        <p className="text-[13px] leading-4 text-muted"><Link to="/home" className="rounded hover:text-forest">Главная</Link> / Профиль авто</p>
        <h1 id="car-title" tabIndex={-1} className="home-title">Данные об автомобиле</h1>
      </section>

      <div className="car-content">
        <form onSubmit={handleSubmit} noValidate className="car-form">
          <div role="progressbar" aria-label="Прогресс оценки" aria-valuemin={0} aria-valuemax={100} aria-valuenow={50} aria-valuetext="Данные автомобиля: второй этап оценки" className="car-progress"><span /></div>

          <div className="car-form-card">
            <div className="car-field-row">
              <div className="car-field">
                <label htmlFor="car-brand">Марка</label>
                <div className="car-select-wrap">
                  <select id="car-brand" name="brand" required value={draft.brand} onChange={(event) => updateField('brand', event.target.value)} aria-invalid={Boolean(errors.brand)} aria-describedby={errors.brand ? 'brand-error' : undefined} className="car-control">
                    <option value="">Выберите марку</option>
                    {carBrands.map((brand) => <option key={brand} value={brand}>{brand}</option>)}
                  </select>
                  <ChevronDown size={18} strokeWidth={1} aria-hidden="true" />
                </div>
                {errors.brand && <p id="brand-error" className="car-field-error">{errors.brand}</p>}
              </div>

              <div className="car-field">
                <label htmlFor="car-model">Модель</label>
                <div className="car-select-wrap">
                  <select id="car-model" name="model" required disabled={!draft.brand} value={draft.model} onChange={(event) => updateField('model', event.target.value)} aria-invalid={Boolean(errors.model)} aria-describedby={errors.model ? 'model-error' : undefined} className="car-control">
                    <option value="">{draft.brand ? 'Выберите модель' : 'Сначала выберите марку'}</option>
                    {models.map((model) => <option key={model} value={model}>{model}</option>)}
                  </select>
                  <ChevronDown size={18} strokeWidth={1} aria-hidden="true" />
                </div>
                {errors.model && <p id="model-error" className="car-field-error">{errors.model}</p>}
              </div>
            </div>

            <div className="car-field-row">
              <div className="car-field">
                <label htmlFor="car-year">Год выпуска</label>
                <div className="car-select-wrap">
                  <select id="car-year" name="year" required value={draft.year} onChange={(event) => updateField('year', event.target.value)} aria-invalid={Boolean(errors.year)} aria-describedby={errors.year ? 'year-error' : undefined} className="car-control">
                    <option value="">Выберите год</option>
                    {years.map((year) => <option key={year} value={year}>{year}</option>)}
                  </select>
                  <ChevronDown size={18} strokeWidth={1} aria-hidden="true" />
                </div>
                {errors.year && <p id="year-error" className="car-field-error">{errors.year}</p>}
              </div>

              <div className="car-field">
                <label htmlFor="car-mileage">Пробег (км)</label>
                <input id="car-mileage" name="mileage" type="text" inputMode="numeric" required maxLength={20} placeholder="Например, 85 000" value={draft.mileage} onChange={(event) => updateField('mileage', event.target.value)} onBlur={() => updateField('mileage', formatMileage(draft.mileage))} aria-invalid={Boolean(errors.mileage)} aria-describedby={errors.mileage ? 'mileage-error' : undefined} className="car-control" />
                {errors.mileage && <p id="mileage-error" className="car-field-error">{errors.mileage}</p>}
              </div>
            </div>

            <div className="car-field">
              <label htmlFor="car-region">Регион</label>
              <div className="car-select-wrap">
                <select id="car-region" name="region" required value={customRegion ? '__other__' : draft.region} onChange={(event) => { const other = event.target.value === '__other__'; setCustomRegion(other); updateField('region', other ? '' : event.target.value) }} aria-invalid={Boolean(errors.region)} aria-describedby={errors.region ? 'region-error' : undefined} className="car-control">
                  <option value="">Выберите регион</option>
                  {carRegions.map((region) => <option key={region} value={region}>{region}</option>)}
                  <option value="__other__">Другой регион — указать вручную</option>
                </select>
                <ChevronDown size={18} strokeWidth={1} aria-hidden="true" />
              </div>
              {customRegion && <><label htmlFor="car-region-custom" className="sr-only">Ваш регион</label><input id="car-region-custom" name="customRegion" maxLength={100} required placeholder="Введите ваш регион" value={draft.region} onChange={(event) => updateField('region', event.target.value)} aria-invalid={Boolean(errors.region)} aria-describedby={errors.region ? 'region-error' : undefined} className="car-control" /></>}
              {errors.region && <p id="region-error" className="car-field-error">{errors.region}</p>}
            </div>

            <label className="car-save-label" htmlFor="car-save">
              <span className="relative flex shrink-0"><input type="checkbox" id="car-save" checked={draft.saveToProfile} onChange={(event) => { onDraftChange({ ...draft, saveToProfile: event.target.checked }); setStorageError('') }} aria-describedby="car-storage-note" className="car-checkbox" />{draft.saveToProfile && <Check size={14} strokeWidth={1} className="pointer-events-none absolute top-[3px] left-[3px] text-white" aria-hidden="true" />}</span>
              Сохранить автомобиль в профиль для будущих расчётов
            </label>
          </div>

          {Object.values(errors).some(Boolean) && <p role="alert" className="car-submit-error">Проверьте отмеченные поля.</p>}
          {storageError && <p role="alert" className="car-submit-error">{storageError}</p>}
          <div className="car-actions">
            <button type="button" onClick={goBack} className="car-back">Назад</button>
            <button type="submit" className="car-continue">Сохранить и продолжить</button>
          </div>
          <p id="car-storage-note" className="car-prototype-note">Пока используется локальный справочник. Автомобиль сохраняется только в этом браузере.</p>
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
