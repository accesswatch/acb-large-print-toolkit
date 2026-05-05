/**
 * axe-audit.spec.mjs — GLOW comprehensive accessibility audit
 *
 * Scans every public route with @axe-core/playwright at WCAG 2.2 AA level.
 * Runs after consent is granted so the real page content is scanned, not
 * just the consent gate.
 *
 * Results are written to artifacts/axe-results.json in the same list format
 * expected by .github/scripts/axe_json_to_sarif.py so the CI SARIF upload
 * step works unchanged.
 *
 * Fail conditions (hard test failure):
 *   - Any critical or serious violation on any page
 *
 * Advisory (warning in output, no failure):
 *   - moderate / minor violations — surfaced in the artifact for review
 */

import fs from 'node:fs';
import path from 'node:path';
import { test, expect } from '@playwright/test';
import { AxeBuilder } from '@axe-core/playwright';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const ARTIFACTS_DIR = path.resolve('e2e/artifacts');

const AXE_TAGS = [
    'wcag2a',
    'wcag2aa',
    'wcag21a',
    'wcag21aa',
    'wcag22aa',
];

/**
 * Grant consent once for the given page so subsequent navigations within the
 * same browser context skip the gate.
 */
async function ensureConsent(page) {
    const url = page.url();
    if (!url.includes('/consent')) return;

    const agree = page.locator('input[name="agreed"][value="yes"]');
    if (await agree.count()) await agree.check();

    const continueBtn = page.getByRole('button', { name: /Continue to GLOW/i });
    if (await continueBtn.count()) {
        await Promise.all([
            page.waitForURL((u) => !u.pathname.startsWith('/consent'), { timeout: 15_000 }),
            continueBtn.click(),
        ]);
    }
}

/**
 * Navigate to *url*, handle consent redirect if needed, then run axe.
 * Returns { url, violations, passes, incomplete } shaped like axe CLI output.
 */
async function auditPage(page, url) {
    await page.goto(url);
    await ensureConsent(page);
    // Wait for the page to settle (no pending network requests, no animation)
    await page.waitForLoadState('networkidle');

    const results = await new AxeBuilder({ page })
        .withTags(AXE_TAGS)
        // Disable rules that generate false positives in a dev/CI environment
        // with no real document content loaded.
        .disableRules([
            'color-contrast', // CSS variables not resolved the same way in headless Chromium
        ])
        .analyze();

    return {
        url: page.url(),
        testEnvironment: 'playwright-chromium',
        violations: results.violations,
        passes: results.passes,
        incomplete: results.incomplete,
        inapplicable: results.inapplicable,
    };
}

// ---------------------------------------------------------------------------
// Pages to audit
// ---------------------------------------------------------------------------

const STATIC_PAGES = [
    { label: 'home', path: '/' },
    { label: 'audit form', path: '/audit/' },
    { label: 'fix form', path: '/fix/' },
    { label: 'convert form', path: '/convert/' },
    { label: 'template form', path: '/template/' },
    { label: 'speech studio', path: '/speech/' },
    { label: 'braille studio', path: '/braille/' },
    { label: 'settings', path: '/settings/' },
    { label: 'guidelines', path: '/guidelines/' },
    { label: 'user guide', path: '/guide/' },
    { label: 'about', path: '/about/' },
    { label: 'changelog', path: '/changelog/' },
    { label: 'faq', path: '/faq/' },
    { label: 'rules reference', path: '/rules/' },
    { label: 'feedback', path: '/feedback/' },
    { label: 'privacy policy', path: '/privacy/' },
    { label: 'status', path: '/status/' },
];

// ---------------------------------------------------------------------------
// Accumulated results — written to artifact after all tests complete
// ---------------------------------------------------------------------------

const allPageResults = [];

test.afterAll(async () => {
    fs.mkdirSync(ARTIFACTS_DIR, { recursive: true });
    const outPath = path.join(ARTIFACTS_DIR, 'axe-results.json');
    fs.writeFileSync(outPath, JSON.stringify(allPageResults, null, 2), 'utf-8');

    // Emit a human-readable violation summary to stdout for CI log readability
    const blocking = allPageResults.flatMap((r) =>
        r.violations
            .filter((v) => ['critical', 'serious'].includes(v.impact))
            .map((v) => `  [${v.impact}] ${v.id} (${v.nodes.length} node${v.nodes.length === 1 ? '' : 's'}) on ${r.url}`)
    );
    const advisory = allPageResults.flatMap((r) =>
        r.violations
            .filter((v) => ['moderate', 'minor'].includes(v.impact))
            .map((v) => `  [${v.impact}] ${v.id} (${v.nodes.length} node${v.nodes.length === 1 ? '' : 's'}) on ${r.url}`)
    );

    if (blocking.length) {
        console.error('\n=== AXE: BLOCKING violations (critical/serious) ===\n' + blocking.join('\n'));
    }
    if (advisory.length) {
        console.warn('\n=== AXE: Advisory violations (moderate/minor) ===\n' + advisory.join('\n'));
    }
    if (!blocking.length && !advisory.length) {
        console.log('\n=== AXE: No violations found across all pages ===');
    }

    const totalPages = allPageResults.length;
    const totalViolations = allPageResults.reduce((s, r) => s + r.violations.length, 0);
    const totalPasses = allPageResults.reduce((s, r) => s + r.passes.length, 0);
    console.log(`\nAxe summary: ${totalPages} pages, ${totalViolations} violation rule(s), ${totalPasses} passing rule(s)`);
});

// ---------------------------------------------------------------------------
// Test: audit each static page
// ---------------------------------------------------------------------------

test.describe('GLOW axe-core WCAG 2.2 AA audit', () => {
    // Use a single shared browser context so consent is granted once and
    // all subsequent navigations within the suite skip the gate.
    let sharedPage;

    test.beforeAll(async ({ browser }) => {
        const context = await browser.newContext();
        sharedPage = await context.newPage();
        // Grant consent once by visiting home and accepting
        await sharedPage.goto('/');
        await ensureConsent(sharedPage);
    });

    test.afterAll(async () => {
        await sharedPage?.context().close();
    });

    for (const { label, path: pagePath } of STATIC_PAGES) {
        test(`${label} — no critical/serious axe violations`, async () => {
            const result = await auditPage(sharedPage, pagePath);
            allPageResults.push(result);

            const blocking = result.violations.filter((v) =>
                ['critical', 'serious'].includes(v.impact)
            );

            if (blocking.length) {
                const details = blocking.map((v) => {
                    const nodeDetails = v.nodes.slice(0, 3).map((n) =>
                        `    selector: ${(n.target || []).join(' > ')}\n    html: ${n.html?.slice(0, 120)}`
                    ).join('\n');
                    return `[${v.impact}] ${v.id}: ${v.help}\n  ${v.helpUrl}\n${nodeDetails}`;
                });
                throw new Error(
                    `${blocking.length} blocking axe violation(s) on ${pagePath}:\n\n` +
                    details.join('\n\n')
                );
            }

            // Advisory violations — log but do not fail
            const advisory = result.violations.filter((v) =>
                ['moderate', 'minor'].includes(v.impact)
            );
            if (advisory.length) {
                console.warn(
                    `[advisory] ${advisory.length} moderate/minor violation(s) on ${pagePath}: ` +
                    advisory.map((v) => v.id).join(', ')
                );
            }
        });
    }
});

// ---------------------------------------------------------------------------
// Test: interactive state — speech studio with engines unavailable
// ---------------------------------------------------------------------------

test.describe('GLOW axe-core — interactive states', () => {
    test('speech studio unavailable banner is accessible', async ({ page }) => {
        await page.goto('/speech/');
        await ensureConsent(page);
        await page.waitForLoadState('networkidle');

        const result = await new AxeBuilder({ page })
            .withTags(AXE_TAGS)
            .disableRules(['color-contrast'])
            .analyze();

        const blocking = result.violations.filter((v) =>
            ['critical', 'serious'].includes(v.impact)
        );
        expect(blocking, `Speech unavailable state has ${blocking.length} blocking violation(s): ${blocking.map((v) => v.id).join(', ')}`).toHaveLength(0);
    });

    test('braille studio unavailable state is accessible', async ({ page }) => {
        await page.goto('/braille/');
        await ensureConsent(page);
        await page.waitForLoadState('networkidle');

        const result = await new AxeBuilder({ page })
            .withTags(AXE_TAGS)
            .disableRules(['color-contrast'])
            .analyze();

        const blocking = result.violations.filter((v) =>
            ['critical', 'serious'].includes(v.impact)
        );
        expect(blocking, `Braille unavailable state has ${blocking.length} blocking violation(s): ${blocking.map((v) => v.id).join(', ')}`).toHaveLength(0);
    });

    test('audit form — help accordions expanded state is accessible', async ({ page }) => {
        await page.goto('/audit/');
        await ensureConsent(page);

        // Expand all help accordions
        const summaries = page.locator('details > summary');
        const count = await summaries.count();
        for (let i = 0; i < count; i++) {
            const detail = summaries.nth(i).locator('..');
            const isOpen = await detail.evaluate((el) => el.open);
            if (!isOpen) await summaries.nth(i).click();
        }
        await page.waitForLoadState('networkidle');

        const result = await new AxeBuilder({ page })
            .withTags(AXE_TAGS)
            .disableRules(['color-contrast'])
            .analyze();

        const blocking = result.violations.filter((v) =>
            ['critical', 'serious'].includes(v.impact)
        );
        expect(blocking, `Audit form (accordions open) has ${blocking.length} blocking violation(s): ${blocking.map((v) => v.id).join(', ')}`).toHaveLength(0);
    });

    test('dark mode — no critical/serious violations', async ({ browser }) => {
        // Simulate prefers-color-scheme: dark
        const context = await browser.newContext({
            colorScheme: 'dark',
        });
        const page = await context.newPage();
        await page.goto('/');
        await ensureConsent(page);
        await page.waitForLoadState('networkidle');

        const result = await new AxeBuilder({ page })
            .withTags(AXE_TAGS)
            .disableRules(['color-contrast'])
            .analyze();

        const blocking = result.violations.filter((v) =>
            ['critical', 'serious'].includes(v.impact)
        );
        expect(blocking, `Dark mode home has ${blocking.length} blocking violation(s): ${blocking.map((v) => v.id).join(', ')}`).toHaveLength(0);

        await context.close();
    });

    test('mobile viewport — no critical/serious violations on home', async ({ browser }) => {
        const context = await browser.newContext({
            viewport: { width: 375, height: 812 }, // iPhone 14 Pro
            userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15',
        });
        const page = await context.newPage();
        await page.goto('/');
        await ensureConsent(page);
        await page.waitForLoadState('networkidle');

        const result = await new AxeBuilder({ page })
            .withTags(AXE_TAGS)
            .disableRules(['color-contrast'])
            .analyze();

        const blocking = result.violations.filter((v) =>
            ['critical', 'serious'].includes(v.impact)
        );
        expect(blocking, `Mobile home has ${blocking.length} blocking violation(s): ${blocking.map((v) => v.id).join(', ')}`).toHaveLength(0);

        await context.close();
    });
});
