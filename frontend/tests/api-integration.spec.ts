import { test, expect } from '@playwright/test';

test.describe('Integración Frontend con Backend FastAPI y Correcciones de UI', () => {
  test('Verifica llamadas a la API REST (status 200), headbar limpia, filtros de periodo, nueva card de km y tablas sin MTOP', async ({ page }) => {
    // Escuchar peticiones a la API
    const apiCalls: { url: string; status: number }[] = [];
    page.on('response', (response) => {
      const url = response.url();
      if (url.includes('/api/v1/')) {
        apiCalls.push({ url, status: response.status() });
      }
    });

    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto('http://localhost:6001/');
    await page.click('button:has-text("ADMIN")');
    await page.waitForURL('**/dashboard', { timeout: 15000 });

    // Esperar a que la carga del dashboard finalice y se ejecuten las peticiones
    await page.waitForResponse(
      (r) => r.url().includes('/analitica/dashboard-ejecutivo') && r.status() === 200,
      { timeout: 10000 }
    ).catch(() => null);

    await page.waitForTimeout(1000);

    // 1. Validar que se realizaron las peticiones clave al backend FastAPI y respondieron 200
    const dashboardCall = apiCalls.find((c) => c.url.includes('/analitica/dashboard-ejecutivo'));
    expect(dashboardCall).toBeDefined();
    expect(dashboardCall?.status).toBe(200);

    const ambulanciasCall = apiCalls.find((c) => c.url.includes('/operaciones/ambulancias'));
    expect(ambulanciasCall).toBeDefined();
    expect(ambulanciasCall?.status).toBe(200);

    // 2. Validar Headbar Limpia (Sin badges técnicos y con perfil de usuario en la esquina derecha)
    await expect(page.getByText('FastAPI & SQL Server: Activo')).not.toBeVisible();
    await expect(page.getByText(/Sin conexión con el servicio de analítica/i)).not.toBeVisible();

    const header = page.locator('header');
    await expect(header.locator('[data-testid="user-dropdown-trigger"]')).toBeVisible();
    await expect(header.getByRole('button', { name: /Cambiar tema/i })).toBeVisible();

    // 3. Validar Barra de Filtros del Dashboard Principal
    const main = page.getByRole('main');
    await expect(main.getByText('Periodo de Consulta')).toBeVisible();
    await expect(main.getByText('Unidad Vehicular')).toBeVisible();
    await expect(main.getByText('Turno Operativo')).toBeVisible();
    await expect(main.getByText(/Ventana de datos activa/i)).toBeVisible();

    // 4. Validar Banner de Recomendación Estratégica (sin modelos técnicos como Qwen 2.5)
    await expect(main.getByText('Recomendación Estratégica Preventiva')).toBeVisible();
    await expect(main.getByText('Análisis Inteligente')).toBeVisible();
    await expect(main.getByText(/Qwen/i)).not.toBeVisible();

    // 5. Validar KPIs Superiores (incluyendo la nueva Card de Kilómetros de Flota)
    await expect(main.getByText('Auxilios de Ambulancia', { exact: true })).toBeVisible();
    await expect(main.getByText('Remolques de Grúa', { exact: true })).toBeVisible();
    await expect(main.getByText('Rondas e Inspección Vial', { exact: true })).toBeVisible();
    await expect(main.getByText('Kilómetros Recorridos de Flota', { exact: true })).toBeVisible();
    await expect(main.getByText('Sincronización MTOP', { exact: true })).not.toBeVisible();

    // 6. Validar presencia de los gráficos dinámicos
    await expect(main.getByText(/Distribución Operativa de Asistencias/i)).toBeVisible();
    await expect(main.getByText(/Distribución por Causa/i)).toBeVisible();

    // Captura 1: Dashboard Principal con Filtros y Headbar limpia en Modo Claro
    await page.screenshot({
      path: 'tests/screenshots/api-dashboard-01-live-light.png',
      fullPage: true,
    });

    // 7. Probar interacción con un filtro Select del Dashboard
    const periodoTrigger = main.locator('[data-slot="select-trigger"]').first();
    await periodoTrigger.click();
    await page.waitForTimeout(300);

    // Captura 2: Select abierto con fondo opaco y opciones delimitadas
    await page.screenshot({
      path: 'tests/screenshots/api-dashboard-02-select-dropdown.png',
      fullPage: true,
    });

    // Seleccionar opción
    await page.getByRole('option', { name: /Últimos 30 días/i }).click();
    await page.waitForTimeout(400);

    // 8. Cambiar a vista de Ambulancias y validar que NO existe la columna "Estado MTOP"
    await page.getByTestId('nav-ambulancias').first().click();
    await page.waitForTimeout(600);

    // Validar encabezado y que no exista columna "Estado MTOP"
    await expect(main.getByRole('heading', { name: /Registro y Auditoría de Ambulancias/i })).toBeVisible();
    await expect(main.getByRole('columnheader', { name: /Estado MTOP/i })).not.toBeVisible();

    // Captura 3: Tabla de Ambulancias sin columna MTOP
    await page.screenshot({
      path: 'tests/screenshots/api-dashboard-03-ambulancias-table.png',
      fullPage: true,
    });

    // 9. Cambiar a vista de Grúas y validar que tampoco existe "Estado MTOP"
    await page.getByTestId('nav-gruas').first().click();
    await page.waitForTimeout(600);

    await expect(main.getByRole('heading', { name: /Registro y Auditoría de Grúas/i })).toBeVisible();
    await expect(main.getByRole('columnheader', { name: /Estado MTOP/i })).not.toBeVisible();

    // Captura 4: Tabla de Grúas sin columna MTOP
    await page.screenshot({
      path: 'tests/screenshots/api-dashboard-04-gruas-table.png',
      fullPage: true,
    });

    // 10. Cambiar a Modo Oscuro y volver al Dashboard
    await page.getByTestId('nav-kpi').first().click();
    await page.waitForTimeout(400);

    const themeBtn = page.getByRole('button', { name: /Cambiar tema/i });
    await themeBtn.click();
    await page.waitForTimeout(500);

    // Captura 5: Dashboard en Modo Oscuro con Headbar limpia y Usuario en esquina derecha
    await page.screenshot({
      path: 'tests/screenshots/api-dashboard-05-live-dark.png',
      fullPage: true,
    });
  });
});
