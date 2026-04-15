import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const artifactsDir = path.join(root, 'e2e', 'artifacts');
const resultsPath = path.join(artifactsDir, 'results.json');
const reportPath = path.join(artifactsDir, 'ISSUES.md');

function walkSuites(suites, parentTitles = []) {
  const out = [];

  for (const suite of suites || []) {
    const chain = suite.title ? [...parentTitles, suite.title] : [...parentTitles];

    for (const spec of suite.specs || []) {
      const testTitle = [...chain, spec.title].filter(Boolean).join(' > ');
      const results = spec.tests?.flatMap((t) => t.results || []) || [];

      for (const result of results) {
        if (result.status === 'failed' || result.status === 'timedOut') {
          const err = result.error?.message || 'No error message captured.';
          out.push({
            title: testTitle,
            status: result.status,
            error: err,
          });
        }
      }
    }

    out.push(...walkSuites(suite.suites || [], chain));
  }

  return out;
}

if (!fs.existsSync(resultsPath)) {
  console.log(`No Playwright results file found at ${resultsPath}. Skipping issue report generation.`);
  process.exit(0);
}

const raw = fs.readFileSync(resultsPath, 'utf8');
const json = JSON.parse(raw);
const failures = walkSuites(json.suites || []);

fs.mkdirSync(artifactsDir, { recursive: true });

const now = new Date().toISOString();
const lines = [];
lines.push('# E2E Regression Issue Report');
lines.push('');
lines.push(`Generated: ${now}`);
lines.push('');
lines.push(`Total failed tests: ${failures.length}`);
lines.push('');

if (failures.length === 0) {
  lines.push('No failed Playwright tests were found.');
  lines.push('');
} else {
  lines.push('## Failures');
  lines.push('');

  failures.forEach((f, i) => {
    lines.push(`### ${i + 1}. ${f.title}`);
    lines.push('');
    lines.push(`- Status: ${f.status}`);
    lines.push('```text');
    lines.push(f.error.trim());
    lines.push('```');
    lines.push('');
  });
}

lines.push('## Artifacts');
lines.push('');
lines.push('- HTML report: e2e/artifacts/html-report/index.html');
lines.push('- JSON report: e2e/artifacts/results.json');
lines.push('- JUnit report: e2e/artifacts/junit.xml');
lines.push('');

fs.writeFileSync(reportPath, `${lines.join('\n')}\n`, 'utf8');
console.log(`Issue report written to ${reportPath}`);
