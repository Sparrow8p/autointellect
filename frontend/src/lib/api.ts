const apiBase = (import.meta.env.VITE_API_URL || '/api').replace(/\/$/, '')
const tokenKey = 'autointellect.access-token'

export function getToken(): string | null {
  try { return sessionStorage.getItem(tokenKey) } catch { return null }
}

export function setToken(token: string | null) {
  if (token) sessionStorage.setItem(tokenKey, token)
  else sessionStorage.removeItem(tokenKey)
}

export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message) }
}

export async function api<T>(path: string, options: { method?: string; body?: unknown; signal?: AbortSignal } = {}): Promise<T> {
  const token = getToken()
  let response: Response
  try {
    response = await fetch(`${apiBase}${path}`, {
      method: options.method ?? 'GET',
      signal: options.signal,
      headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}), ...(options.body !== undefined ? { 'Content-Type': 'application/json' } : {}) },
      ...(options.body !== undefined ? { body: JSON.stringify(options.body) } : {}),
    })
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') throw error
    throw new Error('Не удалось связаться с сервером. Проверьте подключение и повторите попытку.', { cause: error })
  }
  if (!response.ok) {
    if (response.status === 401 && token && token === getToken() && !path.startsWith('/auth/') && !options.signal?.aborted) {
      setToken(null)
      window.dispatchEvent(new Event('auth-expired'))
    }
    const messages: Record<number, string> = {
      401: path.startsWith('/auth/') ? 'Неверный email или пароль.' : 'Сессия истекла. Войдите снова.',
      404: 'Запись не найдена или недоступна.',
      409: 'Этот email уже зарегистрирован. Войдите в аккаунт.',
      422: 'Проверьте введённые данные.',
    }
    throw new ApiError(response.status, messages[response.status] || 'Не удалось выполнить запрос. Повторите попытку.')
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export const errorMessage = (error: unknown) => error instanceof Error ? error.message : 'Не удалось выполнить запрос.'

export type ApiUser = { id: number; email: string; phone: string | null }
export type ApiCar = { id: number; brand: string; model: string; year: number; mileage: number; region: string }
export type ReferenceItem = { id: number; name: string }
export type EstimateResult = {
  recognized: boolean
  min_price: number
  max_price: number
  works: { id: number; name: string; min_price: number; max_price: number }[]
}
export type ScenariosResult = {
  recognized: boolean
  repair: { min_price: number; max_price: number; repair_cost: number }
  scenarios: {
    sell_as_is: { value: number; recommended: boolean }
    repair_and_sell: { value: number; recommended: boolean; repair_cost: number; price_after_repair: number; price_growth_percent: number }
    repair_and_keep: { value: number; recommended: boolean; repair_cost: number; running_costs: number; years: number }
  }
  profit: number
  recommendation: string
}
export type HistoryItem = {
  id: number
  created_at: string
  car: Pick<ApiCar, 'id' | 'brand' | 'model' | 'year'>
  problem_text: string | null
  repair_min: number
  repair_max: number
  price_as_is: number
  price_after_repair: number
  recommendation: string
}
