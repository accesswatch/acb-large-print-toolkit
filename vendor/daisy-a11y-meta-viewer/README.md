# DAISY a11y-meta-viewer -- Vendored Source

Vendored copy of the [DAISY Consortium Accessibility Metadata Viewer](https://github.com/daisy/a11y-meta-viewer) JavaScript source.

This viewer implements the [W3C Accessibility Metadata Display Guide 2.0](https://w3c.github.io/publ-a11y/a11y-meta-display-guide/2.0/draft/techniques/epub-metadata/) algorithm for generating human-readable accessibility metadata statements from EPUB and ONIX records.

## License

CC BY-NC-SA 4.0 (Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International).  
See [LICENSE.md](LICENSE.md) for full text.

The language vocabulary files in `js/lang/` are licensed separately -- see [js/lang/LICENSE.md](js/lang/LICENSE.md).

## Integration

The GLOW Accessibility Toolkit includes a Python port of this algorithm in `desktop/src/acb_large_print/epub_meta_display.py`. The Python implementation follows the same W3C specification independently and is used to enhance EPUB audit reports with human-readable accessibility metadata summaries.

The vendored JS source is retained for:

- Reference and verification against the canonical implementation
- Attribution and license compliance
- Potential future use in the Office Add-in (TypeScript port)

## Version

Vendored from commit `b7d7bff` (main branch), April 2026.

## Upstream

- Repository: <https://github.com/daisy/a11y-meta-viewer>
- W3C Spec (EPUB): <https://w3c.github.io/publ-a11y/a11y-meta-display-guide/2.0/draft/techniques/epub-metadata/>
- W3C Spec (ONIX): <https://w3c.github.io/publ-a11y/a11y-meta-display-guide/2.0/draft/techniques/onix-metadata/>
