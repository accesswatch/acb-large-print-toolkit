# Playwright Regression Suite

This folder contains browser-based regression tests for the GLOW web app.

## Coverage

The suite in [e2e/tests/regression.spec.mjs](e2e/tests/regression.spec.mjs) covers:

- Home page smoke check (including WCAG 2.2 copy)
- Audit upload flow (`/audit`)
- Fix upload flow (`/fix`)
- Export upload flow with file download (`/export`)
- Convert upload flow with file download (`/convert`)
- Template generation download (`/template`)
- BITS Whisperer sample-audio transcription flow (`/whisperer`)
- Static pages smoke checks (`/guidelines`, `/guide`, `/about`, `/changelog`, `/feedback`)

## Prerequisites

From [web/package.json](web/package.json) scripts:

- `npm install`
- `npx playwright install`

The upload tests require a DOCX file path. By default the suite uses:

- `d:/code/test.docx`

Override with:

```powershell
$env:E2E_UPLOAD_DOCX="D:/path/to/your/file.docx"
```

The Whisperer regression test requires an audio file path. By default it uses:

- `S:/code/bw/Samples/ronaldreaganchallengeraddressatt3232.mp3`

Override with:

```powershell
$env:E2E_UPLOAD_AUDIO="S:/path/to/your/audio.mp3"
```

## Run

```powershell
npm run test:e2e
```

## Generate Issue Report

```powershell
npm run test:e2e:report
```

This writes:

- [e2e/artifacts/ISSUES.md](e2e/artifacts/ISSUES.md)
- [e2e/artifacts/results.json](e2e/artifacts/results.json)
- [e2e/artifacts/junit.xml](e2e/artifacts/junit.xml)
- [e2e/artifacts/html-report/index.html](e2e/artifacts/html-report/index.html)

## Notes

- The Playwright web server is started by [e2e/playwright.config.mjs](e2e/playwright.config.mjs).
- Base URL defaults to `http://127.0.0.1:5100`.
- Override with `E2E_BASE_URL` and `E2E_PORT` when needed.
