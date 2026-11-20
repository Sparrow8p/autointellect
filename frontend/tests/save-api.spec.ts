import { expect, test } from '@playwright/test'

test('saving a calculation blocks duplicate requests and allows retry after failure', async ({ page }) => {
  const car = { id: 11, brand: 'Hyundai', model: 'Solaris', year: 2018, mileage: 85000, region: 'Moscow' }
  const estimate = { recognized: true, min_price: 13900, max_price: 18500, works: [] }
  const comparison = {
    recognized: true,
    repair: { ...estimate, repair_cost: 16200 },
    scenarios: {
      sell_as_is: { value: 580000, recommended: false },
      repair_and_sell: { value: 665300, recommended: true, repair_cost: 16200, price_after_repair: 681500, price_growth_percent: 17.5 },
      repair_and_keep: { value: -62600, recommended: false, repair_cost: 16200, running_costs: 46400, years: 1 },
    },
    profit: 85300,
    recommendation: 'Repair and sell',
  }
  const saved = {
    id: 101, created_at: '2026-11-16T12:00:00Z', car,
    problem_text: 'Steering noise', repair_min: 13900, repair_max: 18500,
    price_as_is: 580000, price_after_repair: 681500, recommendation: comparison.recommendation,
  }
  const responses: Record<string, unknown> = {
    '/api/auth/login': { access_token: 'save-test-token', token_type: 'bearer' },
    '/api/users/me': { id: 1, email: 'review@example.com', phone: null },
    '/api/reference/brands': [{ id: 1, name: 'Hyundai' }],
    '/api/reference/models': [{ id: 1, name: 'Solaris', brand: 'Hyundai' }],
    '/api/reference/regions': [{ id: 1, name: 'Moscow' }],
    '/api/cars': car,
    '/api/calculations/estimate': estimate,
    '/api/calculations/scenarios': comparison,
    '/api/history': [saved],
  }
  let saveCalls = 0
  const saveBodies: unknown[] = []
  let releaseFailure = () => {}
  const firstResponseGate = new Promise<void>((resolve) => { releaseFailure = resolve })

  await page.route('**/api/**', async (route) => {
    const path = new URL(route.request().url()).pathname
    if (path === '/api/history/save') {
      saveCalls += 1
      saveBodies.push(route.request().postDataJSON())
      expect(route.request().headers().authorization).toBe('Bearer save-test-token')
      if (saveCalls === 1) {
        await firstResponseGate
        await route.fulfill({ status: 503, json: { detail: 'Temporary error' } })
      } else await route.fulfill({ status: 201, json: saved })
      return
    }
    expect(responses, 'Unexpected API request: ' + path).toHaveProperty(path)
    await route.fulfill({ json: responses[path] })
  })

  try {
    await page.goto('/')
    await page.locator('#identifier').fill('review@example.com')
    await page.locator('#password').fill('test-password')
    await page.locator('.login-continue').click()
    await page.locator('#problem').fill('Steering noise')
    await page.locator('.home-calculate').click()
    await page.locator('#car-brand').selectOption('Hyundai')
    await page.locator('#car-model').selectOption('Solaris')
    await page.locator('#car-year').selectOption('2018')
    await page.locator('#car-mileage').fill('85000')
    await page.locator('#car-region').selectOption('Moscow')
    await page.locator('.car-continue').click()
    await page.locator('a[href="/valuation"]').first().click()
    await page.locator('#price-as-is').fill('580000')
    await expect(page.locator('.valuation-continue')).toBeEnabled()
    await page.locator('.valuation-continue').click()

    const saveButton = page.locator('.scenario-save')
    await saveButton.evaluate((button: HTMLButtonElement) => { button.click(); button.click() })
    await expect.poll(() => saveCalls).toBe(1)
    await expect(saveButton).toBeDisabled()
    releaseFailure()
    await expect(page.getByRole('alert')).toBeVisible()
    await expect(page).toHaveURL(/\/scenarios$/)
    await expect(saveButton).toBeEnabled()
    expect(saveCalls).toBe(1)

    await saveButton.click()
    await expect(page).toHaveURL(/\/history$/)
    await expect(page.locator('.history-row')).toHaveCount(1)
    expect(saveCalls).toBe(2)
    expect(saveBodies).toEqual([
      { car_id: 11, problem_text: 'Steering noise', car_price: 580000 },
      { car_id: 11, problem_text: 'Steering noise', car_price: 580000 },
    ])
  } finally { releaseFailure() }
})
