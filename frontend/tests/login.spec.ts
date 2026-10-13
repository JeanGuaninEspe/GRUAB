import { test, expect } from '@playwright/test';

test.describe('SaaS Split-Screen Login & Dashboard Auth Flow - VehículosRC', () => {
  test('Desktop (1280px): Login and Logout flow via UserDropdown', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto('http://localhost:6001/');
    // Limpiar localStorage y cookies para garantizar pantalla de login
    await page.evaluate(() => {
      localStorage.clear();
      document.cookie.split(";").forEach((c) => {
        document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
      });
    });
    await page.context().clearCookies();
    await page.goto('http://localhost:6001/', { waitUntil: 'networkidle' });

    // 1. Left Column: Brand, Title, Subtitle on Split-Screen Login
    await expect(page.getByText('VehículosRC').first()).toBeVisible();
    await expect(page.getByText('Control Operativo y RBAC')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Iniciar sesión', exact: true })).toBeVisible();

    // 2. Form Inputs & Actions
    const emailInput = page.getByLabel(/Correo electrónico/i);
    await expect(emailInput).toBeVisible();

    const submitBtn = page.getByRole('button', { name: /Ingresar al Panel/i });
    await expect(submitBtn).toBeVisible();

    // 3. Capture Desktop Login Screenshot
    await page.screenshot({ path: 'tests/screenshots/desktop-1280.png', fullPage: true });

    // 4. Test Login via Preset Button (ADMIN)
    await page.click('button:has-text("ADMIN")');
    await page.waitForURL('**/dashboard', { timeout: 15000 });
    await expect(page.getByRole('heading', { name: /Panel Ejecutivo de Operaciones e Histórico/i })).toBeVisible({ timeout: 5000 });

    // 5. Test Logout via Topbar UserDropdown
    const avatarTrigger = page.locator('[data-testid="user-dropdown-trigger"]');
    await expect(avatarTrigger).toBeVisible();
    await avatarTrigger.click();

    const logoutItem = page.locator('[data-testid="dropdown-logout-item"]');
    await expect(logoutItem).toBeVisible();
    await logoutItem.click();

    // 6. Confirms redirection back to login
    await page.waitForURL('**/', { timeout: 10000 });
    await expect(page.getByRole('heading', { name: 'Iniciar sesión', exact: true })).toBeVisible();
  });

  test('Mobile (375px): Responsive Login Form on Mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('http://localhost:6001/');
    await page.evaluate(() => {
      localStorage.clear();
      document.cookie.split(";").forEach((c) => {
        document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
      });
    });
    await page.context().clearCookies();
    await page.goto('http://localhost:6001/', { waitUntil: 'networkidle' });

    await expect(page.getByRole('heading', { name: 'Iniciar sesión', exact: true })).toBeVisible();
    await page.screenshot({ path: 'tests/screenshots/mobile-375.png', fullPage: true });
  });
});
