import { spawnSync } from 'node:child_process';
import path from 'node:path';

const repoRoot = path.resolve(process.cwd(), '..');

const diff = spawnSync(
    'git',
    ['diff', '--cached', '--name-only', '--diff-filter=ACMRT'],
    { cwd: repoRoot, encoding: 'utf8' }
);

if (diff.status !== 0) {
    console.error(diff.stderr || 'Could not determine staged files.');
    process.exit(diff.status || 1);
}

const changed = diff.stdout
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

const routeMap = [
    { prefix: 'web/src/acb_large_print_web/templates/about', path: '/about/' },
    { prefix: 'web/src/acb_large_print_web/templates/changelog', path: '/changelog/' },
    { prefix: 'web/src/acb_large_print_web/templates/faq', path: '/faq/' },
    { prefix: 'web/src/acb_large_print_web/templates/guidelines', path: '/guidelines/' },
    { prefix: 'web/src/acb_large_print_web/templates/privacy', path: '/privacy/' },
    { prefix: 'web/src/acb_large_print_web/templates/status', path: '/status/' },
    { prefix: 'web/src/acb_large_print_web/templates/index', path: '/' },
    { prefix: 'web/src/acb_large_print_web/templates/audit', path: '/audit/' },
    { prefix: 'web/src/acb_large_print_web/templates/fix', path: '/fix/' },
    { prefix: 'web/src/acb_large_print_web/templates/convert', path: '/convert/' },
    { prefix: 'web/src/acb_large_print_web/templates/template', path: '/template/' },
    { prefix: 'web/src/acb_large_print_web/templates/speech', path: '/speech/' },
    { prefix: 'web/src/acb_large_print_web/templates/braille', path: '/braille/' },
    { prefix: 'web/src/acb_large_print_web/templates/settings', path: '/settings/' },
    { prefix: 'web/src/acb_large_print_web/templates/guide', path: '/guide/' },
    { prefix: 'web/src/acb_large_print_web/templates/feedback', path: '/feedback/' },
    { prefix: 'web/src/acb_large_print_web/templates/rules', path: '/rules/' },
    { prefix: 'web/src/acb_large_print_web/static/', path: '/' },
    { prefix: 'web/src/acb_large_print_web/app.py', path: '/' },
    { prefix: 'web/src/acb_large_print_web/routes/', path: '/' },
];

const impacted = new Set();
for (const file of changed) {
    for (const entry of routeMap) {
        if (file.startsWith(entry.prefix)) {
            impacted.add(entry.path);
        }
    }
}

if (impacted.size === 0) {
    console.log('No impacted web routes detected; skipping impacted axe audit.');
    process.exit(0);
}

const routeList = Array.from(impacted);
console.log(`Running impacted axe audit for routes: ${routeList.join(', ')}`);

const result = spawnSync(
    'npm',
    ['run', 'test:axe'],
    {
        cwd: process.cwd(),
        stdio: 'inherit',
        env: {
            ...process.env,
            E2E_AXE_PATHS: routeList.join(','),
            E2E_AXE_FAIL_INCOMPLETE: '1',
        },
        shell: true,
    }
);

process.exit(result.status || 0);
