import { test, expect } from '@playwright/test';

test.describe('Light & Dark Mode Theme Toggle - VehículosRC', () => {
  test('Desktop (1280px): Initial Light Mode, Toggle to Dark Mode, and Capture Screenshots', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    // Iniciar sesión para acceder al dashboard
    await page.goto('http://localhost:6001/');
    await page.click('button:has-text("ADMIN")');
    await page.waitForURL('**/dashboard', { timeout: 15000 });

    // 1. Check initial Light Mode: <html> element should NOT have class "dark"
    const htmlElement = page.locator('html');
    await expect(htmlElement).not.toHaveClass(/dark/);

    // Verify key elements are visible with high contrast in Light Mode
    await expect(page.getByRole('heading', { name: /Panel Ejecutivo de Operaciones e Histórico/i })).toBeVisible();

    // 2. Capture Light Mode Desktop Screenshot
    await page.screenshot({ path: 'tests/screenshots/light-mode-1280.png', fullPage: true });

    // 3. Find and Click ThemeToggle Button
    const themeBtn = page.getByRole('button', { name: /Cambiar tema/i });
    await expect(themeBtn).toBeVisible();
    await themeBtn.click();
    await page.waitForTimeout(400);

    // 4. Check that <html> has acquired the "dark" class
    await expect(htmlElement).toHaveClass(/dark/);

    // 5. Capture Dark Mode Desktop Screenshot
    await page.screenshot({ path: 'tests/screenshots/dark-mode-1280.png', fullPage: true });

    // 6. Click again to switch back to Light Mode
    await themeBtn.click();
    await page.waitForTimeout(300);
    await expect(htmlElement).not.toHaveClass(/dark/);
  });

  test('Mobile (375px): Light Mode and Dark Mode Toggle on Mobile Viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('http://localhost:6001/');
    await page.click('button:has-text("ADMIN")');
    await page.waitForURL('**/dashboard', { timeout: 15000 });

    const htmlElement = page.locator('html');
    await expect(htmlElement).not.toHaveClass(/dark/);

    // Capture Mobile Light Mode
    await page.screenshot({ path: 'tests/screenshots/mobile-light-375.png', fullPage: true });

    // Toggle to Dark Mode
    const themeBtn = page.getByRole('button', { name: /Cambiar tema/i });
    await expect(themeBtn).toBeVisible();
    await themeBtn.click();
    await page.waitForTimeout(400);

    await expect(htmlElement).toHaveClass(/dark/);

    // Capture Mobile Dark Mode
    await page.screenshot({ path: 'tests/screenshots/mobile-dark-375.png', fullPage: true });
  });
});
