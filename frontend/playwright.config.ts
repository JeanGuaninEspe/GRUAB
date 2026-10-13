import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  workers: 1,
  timeout: 45000,
  use: {
    /* Usa el Chrome instalado en tu sistema en lugar del binario descargado */
    channel: 'chrome', // o 'msedge'
    headless: true,
  },
  projects: [
    {
      name: 'Google Chrome',
      use: { ...devices['Desktop Chrome'], channel: 'chrome' },
    },
  ],
});