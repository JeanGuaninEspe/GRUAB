import { test, expect } from "@playwright/test";
import path from "path";

test.describe("Dashboard Contextual - Sensibilidad a la Unidad Vehicular y UX de Selectores", () => {
  test("debe mostrar ambas grúas (GRUA-01 y GRUA-02) y renderizar etiquetas descriptivas en lugar de IDs numéricos", async ({ page }) => {
    // 1. Configurar Viewport Desktop
    await page.setViewportSize({ width: 1280, height: 850 });
    await page.goto("http://localhost:6001", { waitUntil: "networkidle" });

    // Si estuviera en login, autenticar
    const emailInput = page.locator('input[type="email"]');
    if (await emailInput.isVisible()) {
      await emailInput.fill("operador@concesion.com");
      await page.fill('input[type="password"]', "admin123");
      await page.click('button[type="submit"]');
    }

    const mainContainer = page.getByRole("main");
    await expect(mainContainer.getByRole("heading", { name: /Panel Ejecutivo de Operaciones e Histórico/i })).toBeVisible({ timeout: 15000 });
    await page.waitForTimeout(1000);

    const screenshotDir = path.join(__dirname, "screenshots");

    // Localizar el combobox de Unidad Vehicular (el segundo select)
    const comboboxes = mainContainer.getByRole("combobox");
    const vehiculoSelect = comboboxes.nth(1);

    // 2. Verificar que el trigger inicial muestre "Toda la Flota (Consolidado)" y NO "todos"
    await expect(vehiculoSelect).toHaveText(/Toda la Flota \(Consolidado\)/i);

    // 3. Abrir el desplegable y verificar que aparezcan GRUA-01 y GRUA-02
    await vehiculoSelect.click();
    await page.waitForTimeout(400);

    const grua01Option = page.getByRole("option", { name: /^GRUA-01/i });
    const grua02Option = page.getByRole("option", { name: /^GRUA-02/i });
    const amb01Option = page.getByRole("option", { name: /^AMB-01/i });
    const patr07Option = page.getByRole("option", { name: /^PATR-1807/i });

    await expect(grua01Option).toBeVisible();
    await expect(grua02Option).toBeVisible();
    await expect(amb01Option).toBeVisible();
    await expect(patr07Option).toBeVisible();

    // 4. Seleccionar GRUA-01 y verificar que el trigger muestre el nombre completo (NO "5")
    await grua01Option.click();
    await page.waitForTimeout(1000);
    await expect(vehiculoSelect).toHaveText(/GRUA-01 \(GRUA • GRUA-0202\)/i);
    await expect(mainContainer.getByText("GRUA-01").first()).toBeVisible();
    await expect(mainContainer.getByText("Servicios de Remolque Realizados", { exact: true })).toBeVisible();

    await page.screenshot({ path: path.join(screenshotDir, "select-ux-01-grua-01.png"), fullPage: true });

    // 5. Seleccionar GRUA-02 (Grúa Grande) y verificar que el trigger muestre el nombre completo (NO "6")
    await vehiculoSelect.click();
    await page.waitForTimeout(400);
    await grua02Option.click();
    await page.waitForTimeout(1000);
    await expect(vehiculoSelect).toHaveText(/GRUA-02 \(GRUA • GRUA-0201\)/i);
    await expect(mainContainer.getByText("GRUA-02").first()).toBeVisible();
    await expect(mainContainer.getByText("GRUA GRANDE DE PLATAFORMA", { exact: true })).toBeVisible();

    await page.screenshot({ path: path.join(screenshotDir, "select-ux-02-grua-02.png"), fullPage: true });

    // 6. Seleccionar AMB-01 y verificar que el trigger muestre el nombre completo (NO "4")
    await vehiculoSelect.click();
    await page.waitForTimeout(400);
    await amb01Option.click();
    await page.waitForTimeout(1000);
    await expect(vehiculoSelect).toHaveText(/AMB-01 \(AMBULANCIA • AMB-0101\)/i);
    await expect(mainContainer.getByText("AMB-01").first()).toBeVisible();

    await page.screenshot({ path: path.join(screenshotDir, "select-ux-03-amb-01.png"), fullPage: true });

    // 7. Seleccionar PATR-1807 y verificar que el trigger muestre el nombre completo (NO "2")
    await vehiculoSelect.click();
    await page.waitForTimeout(400);
    await patr07Option.click();
    await page.waitForTimeout(1000);
    await expect(vehiculoSelect).toHaveText(/PATR-1807 \(PATRULLA • TBK-1807\)/i);
    await expect(mainContainer.getByText("PATR-1807").first()).toBeVisible();

    await page.screenshot({ path: path.join(screenshotDir, "select-ux-04-patr-1807.png"), fullPage: true });

    // 8. Verificar Mobile (375px) sin overflow
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForTimeout(800);
    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    const clientWidth = await page.evaluate(() => document.documentElement.clientWidth);
    expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 2);

    await page.screenshot({ path: path.join(screenshotDir, "select-ux-05-mobile-375px.png"), fullPage: true });
  });
});
