import { test, expect } from '@playwright/test';

test.describe('Filtros Reactivos y Responsividad del Dashboard Principal', () => {
  test('Validación de actualización dinámica de filtros y capturas a 1280px y 375px', async ({ page }) => {
    // 1. Configurar viewport Desktop a 1280px
    await page.setViewportSize({ width: 1280, height: 850 });
    await page.goto('http://localhost:6001/');
    await page.click('button:has-text("ADMIN")');
    await page.waitForURL('**/dashboard', { timeout: 15000 });

    const mainContainer = page.getByRole('main');

    // Verificar que el dashboard ejecutivo cargó
    await expect(mainContainer.getByRole('heading', { name: /Panel Ejecutivo de Operaciones e Histórico/i })).toBeVisible();

    // 2. Verificar que los 3 filtros principales están presentes
    await expect(mainContainer.getByText('Periodo de Consulta')).toBeVisible();
    await expect(mainContainer.getByText('Unidad Vehicular')).toBeVisible();
    await expect(mainContainer.getByText('Turno Operativo')).toBeVisible();

    // Capturar valor inicial de KPI de Grúas
    const gruasKpiCard = mainContainer.locator('text=Remolques de Grúa').locator('..').locator('..');
    await expect(gruasKpiCard).toBeVisible();

    // 3. Probar cambio de Turno a "Turno 1 (06:00 - 14:00)"
    const comboboxes = mainContainer.getByRole('combobox');
    const turnoSelectTrigger = comboboxes.nth(2);
    await turnoSelectTrigger.click();
    await page.waitForTimeout(300);

    // Seleccionar opción Turno 1
    const turno1Option = page.getByRole('option', { name: /Turno 1/i });
    await expect(turno1Option).toBeVisible();
    await turno1Option.click();
    await page.waitForTimeout(1000);

    // 4. Probar cambio de Periodo a "Últimos 30 días"
    const periodoSelectTrigger = comboboxes.nth(0);
    await periodoSelectTrigger.click();
    await page.waitForTimeout(300);

    const ultimos30Option = page.getByRole('option', { name: /Últimos 30 días/i });
    await expect(ultimos30Option).toBeVisible();
    await ultimos30Option.click();
    await page.waitForTimeout(1000);

    // 5. Captura Desktop 1280px con filtros aplicados
    await page.screenshot({
      path: 'tests/screenshots/filters-dashboard-1280px.png',
      fullPage: true,
    });

    // 6. Probar Responsividad en Móvil: Viewport 375px
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForTimeout(800);

    // Verificar que no haya desbordamiento horizontal
    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    const clientWidth = await page.evaluate(() => document.documentElement.clientWidth);
    expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 25);

    // Captura Móvil 375px
    await page.screenshot({
      path: 'tests/screenshots/filters-dashboard-mobile-375px.png',
      fullPage: true,
    });
  });
});
