import { defineConfig } from '@playwright/test';

const baseURL = process.env.E2E_BASE_URL || 'http://127.0.0.1:5100';
const port = process.env.E2E_PORT || '5100';

export default defineConfig({
  testDir: './tests',
  timeout: 90000,
  expect: {
    timeout: 15000,
  },
  fullyParallel: false,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['list'],
    ['html', { open: 'never', outputFolder: 'artifacts/html-report' }],
    ['json', { outputFile: 'artifacts/results.json' }],
    ['junit', { outputFile: 'artifacts/junit.xml' }],
  ],
  use: {
    baseURL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  webServer: {
    command: `python -m flask --app acb_large_print_web.app:create_app run --no-debugger --no-reload --port ${port}`,
    url: `${baseURL}/health`,
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});