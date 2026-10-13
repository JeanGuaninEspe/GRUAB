import { test, expect } from '@playwright/test';

test.describe('Panel Ejecutivo de Operaciones e Histórico - KPIs y Gráficos', () => {
  test('Validación visual en Modo Claro y Modo Oscuro con gráficos interactivos', async ({ page }) => {
    // 1. Configurar viewport a 1440x900 (Desktop estándar)
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto('http://localhost:6001/');
    await page.click('button:has-text("ADMIN")');
    await page.waitForURL('**/dashboard', { timeout: 15000 });

    await page.evaluate(() => {
      localStorage.setItem('theme', 'light');
      document.documentElement.classList.remove('dark');
    });
    await page.waitForTimeout(300);

    const htmlElement = page.locator('html');
    const mainContainer = page.getByRole('main');

    // Verificar que estamos en la vista de KPIs Generales (Panel Ejecutivo)
    await expect(mainContainer.getByRole('heading', { name: /Panel Ejecutivo de Operaciones e Histórico/i })).toBeVisible();

    // Verificar visibilidad de las 4 tarjetas KPI con sus bordes e iconos
    await expect(mainContainer.getByText('Auxilios de Ambulancia', { exact: true })).toBeVisible();
    await expect(mainContainer.getByText('Remolques de Grúa', { exact: true })).toBeVisible();
    await expect(mainContainer.getByText('Rondas e Inspección Vial', { exact: true })).toBeVisible();
    await expect(mainContainer.getByText('Kilómetros Recorridos de Flota', { exact: true })).toBeVisible();

    // Verificar visibilidad de los 2 gráficos analíticos
    await expect(mainContainer.getByText(/Distribución Operativa de Asistencias/i)).toBeVisible();
    await expect(mainContainer.getByText(/Distribución por Causa/i)).toBeVisible();
    await expect(mainContainer.getByText('Falla Mecánica')).toBeVisible();

    // Esperar a que los gráficos SVG y animaciones se estabilicen
    await page.waitForTimeout(800);

    // Captura 1: MODO CLARO - 1440px (KPI cards y Gráficos delimitados)
    await page.screenshot({
      path: 'tests/screenshots/executive-dashboard-01-light-1440.png',
      fullPage: true,
    });

    // 2. Cambiar a MODO OSCURO usando el ThemeToggle
    const themeBtn = page.getByRole('button', { name: /Cambiar tema/i });
    await expect(themeBtn).toBeVisible();
    await themeBtn.click();
    await page.waitForTimeout(600); // esperar transición de tema y paleta de gráficos

    // Verificar que <html> tenga la clase "dark"
    await expect(htmlElement).toHaveClass(/dark/);

    // Captura 2: MODO OSCURO - 1440px (Alto contraste y legibilidad)
    await page.screenshot({
      path: 'tests/screenshots/executive-dashboard-02-dark-1440.png',
      fullPage: true,
    });
  });
});
