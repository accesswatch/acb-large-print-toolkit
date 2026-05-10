# GLOW 6.0.0: Open Source, Easier to Join, Easier to Explain

**FOR IMMEDIATE RELEASE - May 9, 2026**

## Thank You First

GLOW keeps getting better because the community keeps being specific about what matters.

This release continues that pattern. It makes the project easier to contribute to, gives users a clearer AI path when they want one, and keeps the first AI rollout focused on the text workflows that are easiest to trust.

## Executive Summary

GLOW 6.0.0 is now available.

This release does four things clearly:

- it explains the open source contribution process more plainly
- it gives users a personal Ollama Cloud setup path for AI features
- it limits that first AI release to heading detection and MarkItDown support
- it shows AI usage directly in the web app so people can see what is active in the current session

## What Is New in 6.0.0

### Open source contribution process

The project now presents the contribution path more directly. Fork the repository, create a branch, open a pull request, and work through review under branch protection.

Why this matters:

- it lowers the barrier for first-time contributors
- it makes the project feel open and collaborative
- it matches the way the project is already being used in practice

### Personal Ollama Cloud AI support with AI Playground (Beta)

Users can add their own Ollama Cloud API key in GLOW and turn on the AI features that make sense for this release.

What is enabled first:

- **heading detection** in Fix
- **MarkItDown support** for document cleanup and extraction
- **AI Playground (Beta)** -- a new experimental chat surface for testing Ollama models without document context

The AI Playground is the new magic here.

It is a standalone chat designed for exploration. Ask any question, try different Ollama models, see how the AI responds. Conversations stay private to your session. You can copy responses, regenerate them, switch models on the fly. The interface is accessible: your questions appear as headings, the AI responses as sub-headings, so you can navigate directly between them using a keyboard or screen reader.

What stays off for now:

- Document Chat

That choice keeps the first release focused and easier to explain.

### MarkItDown + AI Integration: Smarter Document Extraction

MarkItDown is a powerful text extraction engine from Microsoft. GLOW 6.0.0 adds **LLM-enhanced MarkItDown support** so the text extraction process is smarter and more aware of document structure.

**What you get:**

- **Intelligent text extraction** — MarkItDown + AI understands not just text layout, but context and meaning. It keeps important structure (headings, lists, emphasis) and drops noise (page numbers, repeated headers/footers).
- **Heading detection** — Bold or large text that should be a semantic heading gets converted to the right heading level automatically. No more fake headings made from bold text.
- **Better preparation for accessibility fixes** — When documents come in via MarkItDown + AI, they are already cleaner, more structured, and closer to WCAG compliance. Fix workflows then spend less time on the same structural problems.
- **Extraction quality that scales** — Long documents, complex layouts, mixed formats—MarkItDown + AI handles them more consistently than rule-based extraction alone.

**Why it matters:**

The first AI features in GLOW are text-focused because that is where the trust is highest. Headings and structure are objective—either a text block is a heading or it is not. MarkItDown + AI lets GLOW make that determination more reliably. The result is less manual cleanup, faster accessibility fixes, and better starting material for final output.

**How to use it:**

When you add an Ollama key in GLOW Settings, heading detection and MarkItDown support are on by default. Try it:

1. Upload a document in Word, Excel, PowerPoint, PDF, Markdown, or ePub format
2. Choose Audit or Fix
3. If headings are missing or incorrect, the AI Playground lets you test heading detection with different Ollama models before you trust it in production

### Visible AI usage tracking

The web app now includes a sidebar usage meter that refreshes on page load and after AI actions.

It gives users a quick sense of:

- what AI path is active
- how many requests they have used during the current session
- what they can still do right now without guessing

### Feedback-to-issue follow-through

Feedback can now carry contact information for follow-up and sync into GitHub Issues when configured.

That helps turn direct user feedback into a visible development workflow.

## What Stays Strong

Non-AI workflows remain unchanged.

If you do not use AI, GLOW still audits, fixes, converts, and templates documents exactly as before.

## Where to Read More

- [About GLOW](/about/)
- [User Guide](/guide/)
- [Changelog](/changelog/)

## Closing

GLOW 6.0.0 is not trying to do everything at once.

It is trying to do the next right thing clearly: keep the core workflow strong, make the project easier to join, and make AI useful without making it confusing.
