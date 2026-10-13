import { test, expect } from '@playwright/test';

test.describe('Autenticación JWT y Control de Acceso Basado en Roles (RBAC)', () => {
  const BASE_URL = 'http://localhost:6001';

  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
  });

  test('Test 1: Redirección forzosa de usuario no autenticado al intentar acceder a /dashboard', async ({ page }) => {
    await page.context().clearCookies();

    // 1. Intentar navegar a /dashboard sin token
    await page.goto(`${BASE_URL}/dashboard`);
    await page.waitForTimeout(1000);

    // 2. Validar redirección forzosa al Login (/)
    const currentUrl = page.url();
    expect(currentUrl).toContain('localhost:6001');
    expect(new URL(currentUrl).pathname).toBe('/');

    // 3. Verificar elementos del formulario y botones RBAC
    await expect(page.locator('h1', { hasText: 'Iniciar sesión' })).toBeVisible();
    await expect(page.locator('button:has-text("ADMIN")')).toBeVisible();
    await expect(page.locator('button:has-text("JEFE OPER.")')).toBeVisible();
    await expect(page.locator('button:has-text("VISUALIZADOR")')).toBeVisible();

    // Screenshot Login Desktop
    await page.screenshot({ path: './tests/screenshots/01-login-screen-desktop.png', fullPage: true });
  });

  test('Test 2: Rol VISUALIZADOR - Acceso de solo lectura y bloqueo de escritura/formularios', async ({ page }) => {
    await page.context().clearCookies();
    await page.goto(`${BASE_URL}/`);

    // 1. Iniciar sesión rápida como Visualizador
    await page.click('button:has-text("VISUALIZADOR")');
    await page.waitForURL('**/dashboard', { timeout: 15000 });

    // 2. Abrir UserDropdown y validar que el badge del usuario indique VISUALIZADOR
    const userTrigger = page.locator('[data-testid="user-dropdown-trigger"]');
    await expect(userTrigger).toBeVisible({ timeout: 10000 });
    await userTrigger.click();
    await page.waitForTimeout(400);

    await expect(page.locator('text=VISUALIZADOR').first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=Dra. Elena Salazar').first()).toBeVisible();

    await page.keyboard.press('Escape');
    await page.waitForTimeout(300);

    // 3. Validar que la sidebar se mantenga limpia (sin botones de captura rápida)
    await expect(page.locator('text=Captura Rápida')).not.toBeVisible();

    // 4. Ir a la pestaña Ambulancias y validar que NO exista el botón de "+ Nueva Asistencia"
    await page.click('[data-testid="nav-ambulancias"]');
    await page.waitForTimeout(600);
    await expect(page.locator('[data-testid="btn-nuevo-registro-amb"]')).not.toBeVisible();

    // 5. Ir a la pestaña Grúas y validar que NO exista el botón de "+ Nueva Orden de Grúa"
    await page.click('[data-testid="nav-gruas"]');
    await page.waitForTimeout(600);
    await expect(page.locator('[data-testid="btn-nuevo-registro-grua"]')).not.toBeVisible();

    // 6. Intentar forzar la navegación por URL a /operaciones/nuevo/ambulancia
    await page.goto(`${BASE_URL}/operaciones/nuevo/ambulancia`);
    await page.waitForTimeout(1200);

    // 7. Comprobar que sea rechazado y redirigido a /dashboard
    const url = page.url();
    expect(url).toContain('/dashboard');

    // Screenshot Visualizador
    await page.screenshot({ path: './tests/screenshots/02-visualizador-dashboard.png', fullPage: true });
  });

  test('Test 3: Rol JEFE_OPERATIVO - Acceso a registro de asistencias y formularios operativos', async ({ page }) => {
    await page.context().clearCookies();
    await page.goto(`${BASE_URL}/`);

    // 1. Iniciar sesión como Jefe Operativo
    await page.click('button:has-text("JEFE OPER.")');
    await page.waitForURL('**/dashboard', { timeout: 15000 });

    // 2. Abrir UserDropdown y validar badge JEFE OPERATIVO
    const userTrigger = page.locator('[data-testid="user-dropdown-trigger"]');
    await expect(userTrigger).toBeVisible({ timeout: 10000 });
    await userTrigger.click();
    await page.waitForTimeout(400);

    await expect(page.locator('text=JEFE OPERATIVO').first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=Myr. Roberto Paredes').first()).toBeVisible();

    await page.keyboard.press('Escape');
    await page.waitForTimeout(300);

    // 3. Ir a Ambulancias y verificar que "+ Nueva Asistencia" SI esté visible
    await page.click('[data-testid="nav-ambulancias"]');
    await page.waitForTimeout(600);
    const btnNuevoAmb = page.locator('[data-testid="btn-nuevo-registro-amb"]');
    await expect(btnNuevoAmb).toBeVisible({ timeout: 10000 });

    // 4. Cliquear para navegar al formulario de ambulancia
    await btnNuevoAmb.click();
    await page.waitForURL('**/operaciones/nuevo/ambulancia', { timeout: 15000 });
    await expect(page.locator('text=Nueva Asistencia')).toBeVisible({ timeout: 10000 });

    // Screenshot Formulario Operativo
    await page.screenshot({ path: './tests/screenshots/03-jefe-operativo-form.png', fullPage: true });
  });

  test('Test 4: Rol ADMIN, responsive móvil y Cierre de Sesión seguro desde UserDropdown', async ({ page }) => {
    await page.context().clearCookies();
    await page.goto(`${BASE_URL}/`);

    // 1. Iniciar sesión como ADMIN
    await page.click('button:has-text("ADMIN")');
    await page.waitForURL('**/dashboard', { timeout: 15000 });

    // 2. Validar UserDropdown con badge ADMIN
    const userTrigger = page.locator('[data-testid="user-dropdown-trigger"]');
    await expect(userTrigger).toBeVisible({ timeout: 10000 });
    await userTrigger.click();
    await page.waitForTimeout(400);

    await expect(page.locator('text=ADMIN').first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=Ing. Carlos Mendoza').first()).toBeVisible();

    await page.keyboard.press('Escape');
    await page.waitForTimeout(300);

    // 3. Validar vista móvil (375x812)
    await page.setViewportSize({ width: 375, height: 812 });
    await page.waitForTimeout(600);
    await page.screenshot({ path: './tests/screenshots/04-admin-mobile-view.png', fullPage: true });

    // 4. Volver a escritorio y presionar Cerrar Sesión desde el UserDropdown
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.waitForTimeout(500);

    await userTrigger.click();
    await page.waitForTimeout(400);

    const btnLogout = page.locator('[data-testid="dropdown-logout-item"]');
    await expect(btnLogout).toBeVisible({ timeout: 10000 });
    await btnLogout.click();

    // 5. Validar que vuelva a la pantalla de Login y las cookies estén limpias
    await page.waitForURL('**/', { timeout: 15000 });
    await page.waitForTimeout(800);
    expect(new URL(page.url()).pathname).toBe('/');

    const cookies = await page.context().cookies();
    const tokenCookie = cookies.find((c) => c.name === 'token_rc');
    expect(tokenCookie).toBeUndefined();

    // Screenshot Final Logout
    await page.screenshot({ path: './tests/screenshots/05-logout-screen-desktop.png', fullPage: true });
  });
});
