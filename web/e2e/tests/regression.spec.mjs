import fs from 'node:fs';
import path from 'node:path';
import { test, expect } from '@playwright/test';

const uploadDocx = process.env.E2E_UPLOAD_DOCX || 'd:/code/test.docx';
const hasUploadDocx = fs.existsSync(uploadDocx);

function skipIfMissingUploadFile() {
  test.skip(
    !hasUploadDocx,
    `Upload regression tests require a DOCX file. Set E2E_UPLOAD_DOCX or place a file at ${uploadDocx}`,
  );
}

test.describe('GLOW web regression suite', () => {
  test('home page loads and references WCAG 2.2', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { level: 1, name: /GLOW Accessibility Toolkit/i })).toBeVisible();
    await expect(page.getByText(/WCAG 2\.2 AA/i).first()).toBeVisible();
  });

  test('audit flow uploads docx and returns report', async ({ page }) => {
    skipIfMissingUploadFile();

    await page.goto('/audit/');
    await page.locator('#document').setInputFiles(uploadDocx);
    await page.getByRole('button', { name: /Run Audit/i }).click();

    await expect(page.getByRole('heading', { level: 1, name: /Audit Report/i })).toBeVisible();
    await expect(page.getByRole('heading', { level: 2, name: /Compliance Score/i })).toBeVisible();
  });

  test('fix flow uploads docx and returns fix results', async ({ page }) => {
    skipIfMissingUploadFile();

    await page.goto('/fix/');
    await page.locator('#document').setInputFiles(uploadDocx);

    const detectHeadings = page.locator('#detect-headings');
    if (await detectHeadings.count()) {
      await detectHeadings.uncheck();
    }

    await page.getByRole('button', { name: /Fix Document/i }).click();

    await expect(page.getByRole('heading', { level: 1, name: /Fix Results/i })).toBeVisible();
    await expect(page.getByRole('heading', { level: 2, name: /Before and After/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Download/i })).toBeVisible();
  });

  test('export flow uploads docx and downloads CMS html', async ({ page }) => {
    skipIfMissingUploadFile();

    await page.goto('/export/');
    await page.locator('#document').setInputFiles(uploadDocx);
    await page.locator('input[name="mode"][value="cms"]').check();

    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.getByRole('button', { name: /^Export$/i }).click(),
    ]);

    const suggested = download.suggestedFilename();
    expect(suggested.toLowerCase()).toContain('.html');
  });

  test('convert flow uploads docx and downloads markdown', async ({ page }) => {
    skipIfMissingUploadFile();

    await page.goto('/convert/');
    await page.locator('#document').setInputFiles(uploadDocx);

    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.getByRole('button', { name: /Convert My Document/i }).click(),
    ]);

    const suggested = download.suggestedFilename();
    expect(suggested.toLowerCase()).toContain('.md');
  });

  test('template flow downloads dotx', async ({ page }) => {
    await page.goto('/template/');

    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.getByRole('button', { name: /Create Template/i }).click(),
    ]);

    const suggested = download.suggestedFilename();
    expect(suggested.toLowerCase()).toContain('.dotx');
  });

  test('static reference pages load', async ({ page }) => {
    const pages = [
      ['/guidelines/', /Guidelines/i],
      ['/guide/', /User Guide/i],
      ['/about/', /About/i],
      ['/changelog/', /Changelog/i],
      ['/feedback/', /Feedback/i],
    ];

    for (const [url, headingPattern] of pages) {
      await page.goto(url);
      await expect(page.locator('h1', { hasText: headingPattern }).first()).toBeVisible();
    }
  });
});
