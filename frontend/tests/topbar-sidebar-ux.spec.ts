import { test, expect } from '@playwright/test';

test.describe('Refactorización UX de Topbar y Sidebar: Menú Desplegable y Sidebar Limpia', () => {
  const BASE_URL = 'http://localhost:6001';

  test('Validación de Sidebar limpia, Avatar compacto y DropdownMenu en Light y Dark Mode', async ({ page }) => {
    // 1. Iniciar sesión como ADMIN
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto(`${BASE_URL}/`);
    await page.click('button:has-text("ADMIN")');
    await page.waitForURL('**/dashboard', { timeout: 15000 });
    await page.waitForTimeout(1000);

    // 2. Comprobar que en la Sidebar NO haya botones de captura rápida ni duplicidad de usuario
    await expect(page.locator('text=Captura Rápida')).not.toBeVisible();
    await expect(page.locator('button:has-text("+ Ambulancia")')).not.toBeVisible();
    await expect(page.locator('button:has-text("+ Grúa")')).not.toBeVisible();

    // 3. Comprobar que en el footer de la Sidebar solo esté la versión
    const sidebarFooter = page.locator('aside, [data-slot="sidebar"]').locator('text=COSAD 25');
    await expect(sidebarFooter).toBeVisible();

    // 4. Comprobar que el Topbar tenga el Avatar circular compacto (UserDropdown)
    const avatarTrigger = page.locator('[data-testid="user-dropdown-trigger"]');
    await expect(avatarTrigger).toBeVisible();

    // Tomar Screenshot 1: Vista general a 1440px con Sidebar limpia y Topbar minimalista
    await page.screenshot({
      path: './tests/screenshots/ux-01-dashboard-clean-layout-1440px.png',
      fullPage: true,
    });

    // 5. Cliquear en el Avatar para abrir el DropdownMenu
    await avatarTrigger.click();
    await page.waitForTimeout(500);

    // 6. Validar contenido del DropdownMenu (Nombre, Email, Badge ADMIN, Ítems, Logout)
    await expect(page.locator('text=Ing. Carlos Mendoza').first()).toBeVisible();
    await expect(page.locator('text=admin@concesion.com').first()).toBeVisible();
    await expect(page.locator('text=ADMIN').first()).toBeVisible();
    await expect(page.locator('text=Mi Cuenta / Preferencias')).toBeVisible();
    await expect(page.locator('text=Registro de Actividad')).toBeVisible();
    await expect(page.locator('[data-testid="dropdown-logout-item"]')).toBeVisible();

    // Tomar Screenshot 2: DropdownMenu desplegado en Modo Claro
    await page.screenshot({
      path: './tests/screenshots/ux-02-dropdown-menu-light.png',
      fullPage: false,
    });

    // 7. Alternar a Modo Oscuro
    await page.keyboard.press('Escape'); // Cerrar menú para tocar ThemeToggle
    await page.waitForTimeout(300);

    const themeToggle = page.locator('button[aria-label*="tema" i], button:has-text("Toggle theme"), [data-slot="theme-toggle"], header button:has(svg.lucide-sun), header button:has(svg.lucide-moon)').first();
    await themeToggle.click();
    await page.waitForTimeout(600);

    // 8. Reabrir DropdownMenu en Modo Oscuro
    await avatarTrigger.click();
    await page.waitForTimeout(500);

    await expect(page.locator('text=Ing. Carlos Mendoza').first()).toBeVisible();
    await expect(page.locator('[data-testid="dropdown-logout-item"]')).toBeVisible();

    // Tomar Screenshot 3: DropdownMenu desplegado en Modo Oscuro
    await page.screenshot({
      path: './tests/screenshots/ux-03-dropdown-menu-dark.png',
      fullPage: false,
    });

    // 9. Ejecutar Logout desde el DropdownMenu
    await page.locator('[data-testid="dropdown-logout-item"]').click();
    await page.waitForURL('**/', { timeout: 15000 });
    await page.waitForTimeout(800);
    expect(new URL(page.url()).pathname).toBe('/');
  });
});
