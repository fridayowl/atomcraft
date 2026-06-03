import { test, expect } from '@playwright/test'

test.describe('AION Platform Smoke Tests', () => {
  test('home page redirects to login when unauthenticated', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('text=AION')).toBeVisible()
    await expect(page.locator('text=Sign In')).toBeVisible()
  })

  test('can sign up a new user', async ({ page }) => {
    await page.goto('/')
    await page.click('text=Sign Up')
    await page.fill('input[type="email"]', `test-${Date.now()}@aion.ai`)
    await page.fill('input[name="username"]', `user-${Date.now()}`)
    await page.fill('input[type="password"]', 'testpass123')
    await page.click('button:has-text("Create Account")')
    await expect(page.locator('text=Materials Database')).toBeVisible({ timeout: 10000 })
  })

  test('can navigate to all pages', async ({ page }) => {
    const pages = ['Materials Database', 'Generator', 'Predictor', 'Experiments', 'AION Chat']
    for (const p of pages) {
      await page.goto('/')
      await page.click(`text=${p}`)
      await expect(page.locator(`h1:has-text("${p}")`).first()).toBeVisible({ timeout: 5000 })
    }
  })
})
