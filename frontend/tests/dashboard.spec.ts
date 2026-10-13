import { test, expect } from '@playwright/test';

test.describe('Dashboard Principal de Auditoría y Consulta de Asistencias Viales', () => {
  test('Flujo completo de validación visual e interactiva del Dashboard', async ({ page }) => {
    // 1. Configurar viewport a 1440x900 (Desktop)
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto('http://localhost:6001/');
    await page.click('button:has-text("ADMIN")');
    await page.waitForURL('**/dashboard', { timeout: 15000 });

    // Asegurar modo claro por defecto
    const htmlElement = page.locator('html');
    await expect(htmlElement).not.toHaveClass(/dark/);

    // Navegar a la vista de Ambulancias haciendo clic en el menú del sidebar
    const navAmbulancias = page.getByTestId('nav-ambulancias').first();
    await expect(navAmbulancias).toBeVisible();
    await navAmbulancias.click();

    // Esperar a que la tabla de ambulancias sea visible y monte con Motion
    await expect(page.getByRole('heading', { name: /Registro y Auditoría de Ambulancias/i })).toBeVisible();
    await expect(page.getByText(/AMB-/).first()).toBeVisible();

    // Captura 1: Vista de Ambulancias con Sidebar expandida en modo claro (1440px)
    await page.screenshot({ path: 'tests/screenshots/dashboard-01-ambulancias-light-1440.png', fullPage: true });

    // 2. Colapsar el sidebar usando SidebarTrigger
    const sidebarTrigger = page.locator('button[data-sidebar="trigger"]').first();
    await expect(sidebarTrigger).toBeVisible();
    await sidebarTrigger.click();
    await page.waitForTimeout(500); // esperar animación fluida de colapso de sidebar

    // Captura 2: Sidebar colapsada en modo iconos y tabla expandida
    await page.screenshot({ path: 'tests/screenshots/dashboard-02-sidebar-collapsed-1440.png', fullPage: true });

    // 3. Cambiar a la vista de Grúas con la sidebar colapsada y validar transición con Motion
    const navGruas = page.getByTestId('nav-gruas').first();
    await expect(navGruas).toBeVisible();
    await navGruas.click();
    await page.waitForTimeout(500); // esperar transición suave de Motion

    await expect(page.getByRole('heading', { name: /Registro y Auditoría de Grúas/i })).toBeVisible();
    await expect(page.getByText(/GRU-/).first()).toBeVisible();

    // Captura 3: Vista de Grúas con transición fluida
    await page.screenshot({ path: 'tests/screenshots/dashboard-03-gruas-view-1440.png', fullPage: true });

    // 4. Abrir el diálogo de detalle de un registro (botón "Detalle" de la primera fila)
    const detailButtons = page.getByRole('button', { name: /Detalle/i });
    await expect(detailButtons.first()).toBeVisible();
    await detailButtons.first().click();
    await page.waitForTimeout(500); // esperar apertura del diálogo

    // Validar contenido del modal de auditoría
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByText(/Línea de Tiempo Operativa/i)).toBeVisible();
    await expect(page.getByText(/Odometría y Control de Kilometraje/i)).toBeVisible();
    await expect(page.getByText(/Tripulación y Personal Asignado/i)).toBeVisible();

    // Captura 4: Diálogo de Detalle y Auditoría en Modo Claro
    await page.screenshot({ path: 'tests/screenshots/dashboard-04-detail-dialog-1440.png', fullPage: false });

    // 5. Cambiar a Modo Oscuro mediante el ThemeToggle y verificar contraste
    // Primero cerramos el modal
    const closeDialogBtn = page.getByRole('button', { name: /Cerrar Auditoría/i });
    await expect(closeDialogBtn).toBeVisible();
    await closeDialogBtn.click();
    await page.waitForTimeout(300);

    // Click en ThemeToggle
    const themeBtn = page.getByRole('button', { name: /Cambiar tema/i });
    await expect(themeBtn).toBeVisible();
    await themeBtn.click();
    await page.waitForTimeout(400);

    // Verificar clase "dark" en el html
    await expect(htmlElement).toHaveClass(/dark/);

    // Abrir de nuevo el detalle en Modo Oscuro
    await detailButtons.first().click();
    await page.waitForTimeout(500);

    // Captura 5: Modal de Detalle en Modo Oscuro
    await page.screenshot({ path: 'tests/screenshots/dashboard-05-dark-mode-dialog-1440.png', fullPage: false });

    // Cerrar modal y capturar Dashboard completo en Modo Oscuro
    await page.getByRole('button', { name: /Cerrar Auditoría/i }).click();
    await page.waitForTimeout(300);

    // Re-expandir sidebar para ver el dashboard completo en dark mode
    await sidebarTrigger.click();
    await page.waitForTimeout(500);

    // Ir a Vista General (KPIs Generales)
    const navKpis = page.getByTestId('nav-kpi').first();
    await navKpis.click();
    await page.waitForTimeout(400);

    // Captura 6: Dashboard General completo en Dark Mode
    await page.screenshot({ path: 'tests/screenshots/dashboard-06-dark-mode-dashboard-1440.png', fullPage: true });
  });
});
