import { expect, test } from '@playwright/test'
import type { Page, Route } from '@playwright/test'

const saved = {
  id: 1,
  created_at: '2026-10-12T12:30:00Z',
  car: { id: 7, brand: 'Hyundai', model: 'Solaris', year: 2018 },
  problem_text: 'Стучит подвеска',
  repair_min: 13900,
  repair_max: 18500,
  price_as_is: 400000,
  price_after_repair: 470000,
  recommendation: 'Ремонт окупится. Выгода: 53 800 ₽',
}

async function openHistory(page: Page, history: (route: Route) => Promise<void>) {
  await page.route('**/api/**', async (route) => {
    const path = new URL(route.request().url()).pathname
    expect(route.request().headers().authorization).toBe('Bearer history-regression-token')
    if (path === '/api/users/me') {
      await route.fulfill({ json: { id: 3, email: 'history@example.ru', phone: null } })
    } else if (path === '/api/history') await history(route)
    else await route.fulfill({ status: 404, json: { detail: 'Unexpected API request' } })
  })
  await page.goto('/')
  await page.evaluate(() => sessionStorage.setItem('autointellect.access-token', 'history-regression-token'))
  await page.goto('/history')
}

test('opens exact saved data and searches API history by car and date', async ({ page }) => {
  await openHistory(page, (route) => route.fulfill({ json: [saved, {
    ...saved, id: 2, created_at: '2026-10-09T12:00:00Z',
    car: { id: 8, brand: 'Kia', model: 'Rio', year: 2016 }, problem_text: null,
  }] }))
  const openButtons = page.getByRole('button', { name: /^Открыть расчёт:/ })
  await expect(openButtons).toHaveCount(2)
  await page.getByRole('button', { name: /^Открыть расчёт: Hyundai/ }).click()
  const details = page.getByRole('dialog')
  await expect(details.getByRole('heading')).toHaveText('Hyundai Solaris 2018')
  for (const text of [saved.problem_text, saved.recommendation, '13 900 — 18 500 ₽', '400 000 ₽', '470 000 ₽']) {
    await expect(details.getByText(text, { exact: true })).toBeVisible()
  }
  await expect(details.getByText(/12 окт 2026/)).toBeVisible()
  await details.getByRole('button', { name: 'Закрыть', exact: true }).click()
  const search = page.getByRole('searchbox', { name: 'Поиск по марке авто или дате' })
  await search.fill('KIA')
  await expect(openButtons).toHaveCount(1)
  await expect(page.getByText('Описание не указано', { exact: true })).toBeVisible()
  await search.fill('12.10.2026')
  await expect(openButtons).toHaveCount(1)
  await expect(page.getByRole('button', { name: /^Открыть расчёт: Hyundai/ })).toBeVisible()
  await search.fill('Нет такого автомобиля')
  await expect(openButtons).toHaveCount(0)
  await expect(page.getByText('Среди загруженных расчётов ничего не найдено.')).toBeVisible()
})

test('preserves loaded rows on a failed next page and retries the same offset', async ({ page }) => {
  const offsets: number[] = []
  let nextPageAttempts = 0
  await openHistory(page, async (route) => {
    const params = new URL(route.request().url()).searchParams
    expect(params.get('limit')).toBe('100')
    const offset = Number(params.get('offset'))
    offsets.push(offset)
    if (offset === 0) {
      await route.fulfill({ json: Array.from({ length: 100 }, (_, index) => ({ ...saved, id: index + 1 })) })
    } else if (++nextPageAttempts === 1) {
      await route.fulfill({ status: 503, json: { detail: 'Temporarily unavailable' } })
    } else {
      await route.fulfill({ json: [{ ...saved, id: 101, car: { id: 9, brand: 'Toyota', model: 'Camry', year: 2021 } }] })
    }
  })
  const openButtons = page.getByRole('button', { name: /^Открыть расчёт:/ })
  await expect(openButtons).toHaveCount(100)
  await expect(page.getByRole('status')).toContainText('100 из 100 загруженных')
  await page.getByRole('button', { name: 'Загрузить ещё', exact: true }).click()
  await expect(page.getByRole('alert')).toBeVisible()
  await expect(openButtons).toHaveCount(100)
  await page.getByRole('button', { name: 'Повторить загрузку', exact: true }).click()
  await expect(openButtons).toHaveCount(101)
  await expect(page.getByRole('button', { name: /^Открыть расчёт: Toyota Camry 2021/ })).toBeVisible()
  await expect(page.getByRole('status')).toContainText('101 из 101 загруженных')
  await expect(page.getByRole('button', { name: 'Загрузить ещё', exact: true })).not.toBeVisible()
  expect(offsets.filter((offset) => offset === 100)).toEqual([100, 100])
})

test('a history 401 clears the session and keeps private history behind login', async ({ page }) => {
  await openHistory(page, (route) => route.fulfill({ status: 401, json: { detail: 'Could not validate credentials' } }))
  await expect(page).toHaveURL('/')
  await expect(page.getByRole('heading', { name: 'Вход в аккаунт', exact: true })).toBeVisible()
  expect(await page.evaluate(() => sessionStorage.getItem('autointellect.access-token'))).toBeNull()
  await page.goto('/history')
  await expect(page).toHaveURL('/')
  await expect(page.getByRole('button', { name: /^Открыть расчёт:/ })).toHaveCount(0)
})
