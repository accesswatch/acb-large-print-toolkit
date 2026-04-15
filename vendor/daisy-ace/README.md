# DAISY Ace -- Vendored Source

Vendored copy of the [DAISY Ace (Accessibility Checker for EPUB)](https://github.com/daisy/ace) source.

Ace is the most comprehensive EPUB accessibility checker available, providing:

- 100+ axe-core HTML accessibility rules applied to EPUB content documents
- EPUB-specific metadata, navigation, page-list, and structure checks
- Machine-readable JSON reports with EARL (Evaluation And Report Language) output

## License

MIT License. See [src/LICENSE.txt](src/LICENSE.txt) for full text.

## Version

Vendored from main branch (CLI v1.4.5-alpha.1), April 2026.

## Integration

The GLOW Accessibility Toolkit uses Ace in two ways:

1. **Runtime CLI** -- The web app Docker image installs `@daisy/ace` via npm (`npm install -g @daisy/ace`) for live EPUB auditing. See `web/Dockerfile`.
2. **Vendored source** -- This directory contains the full Ace source for offline builds, auditing, and reference.

The `desktop/src/acb_large_print/ace_runner.py` module wraps the Ace CLI, runs it on uploaded EPUBs, and maps Ace findings to the toolkit's audit model.

## Building from Vendored Source

To install Ace from the vendored source instead of the npm registry:

```bash
cd vendor/daisy-ace/src
yarn install
yarn build
npm install -g .
```

## Upstream

- Repository: <https://github.com/daisy/ace>
- Documentation: <https://daisy.github.io/ace/>
- npm package: <https://www.npmjs.com/package/@daisy/ace>
