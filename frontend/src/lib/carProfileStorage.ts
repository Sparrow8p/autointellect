import { carModels } from '../data/carCatalog'
import { emptyCarProfile } from '../types/carProfile'
import type { CarProfileDraft } from '../types/carProfile'

const storageKey = 'autointellect.car-profile.v1'

function parseCarProfile(value: unknown): CarProfileDraft | null {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) return null
  const draft = value as Record<string, unknown>
  const textFields = ['brand', 'model', 'year', 'mileage', 'region'] as const
  if (!textFields.every((field) => typeof draft[field] === 'string')) return null
  if (typeof draft.saveToProfile !== 'boolean') return null

  const brand = (draft.brand as string).trim()
  const model = (draft.model as string).trim()
  const year = (draft.year as string).trim()
  const mileage = (draft.mileage as string).replace(/[ \u00a0\u202f]/g, '')
  const region = (draft.region as string).trim()

  if (!Object.hasOwn(carModels, brand) || !carModels[brand].includes(model)) return null
  if (!/^\d{4}$/.test(year) || Number(year) < 1900 || Number(year) > new Date().getFullYear()) return null
  if (!/^\d+$/.test(mileage) || !Number.isSafeInteger(Number(mileage)) || Number(mileage) > 2_147_483_647) return null
  if (!region || region.length > 100) return null

  return { brand, model, year, mileage, region, saveToProfile: draft.saveToProfile }
}

export function loadSavedCarProfile(): CarProfileDraft {
  try {
    const stored = localStorage.getItem(storageKey)
    if (!stored) return { ...emptyCarProfile }
    const draft = parseCarProfile(JSON.parse(stored))
    return draft?.saveToProfile ? draft : { ...emptyCarProfile }
  } catch {
    // Storage may be unavailable or may contain an outdated/corrupt draft.
    return { ...emptyCarProfile }
  }
}

export function saveCarProfile(draft: CarProfileDraft): void {
  if (!draft.saveToProfile) {
    let stored: string | null
    try {
      stored = localStorage.getItem(storageKey)
    } catch {
      // Continuing without persistence must also work when storage is inaccessible.
      return
    }
    if (stored === null) return
    // If an existing record is readable, deletion must succeed before reporting success.
    localStorage.removeItem(storageKey)
    return
  }

  const parsed = parseCarProfile(draft)
  if (!parsed) throw new Error('Проверьте данные автомобиля перед сохранением.')
  // Deliberately let write failures reach the form: saving must not report false success.
  localStorage.setItem(storageKey, JSON.stringify(parsed))
}
