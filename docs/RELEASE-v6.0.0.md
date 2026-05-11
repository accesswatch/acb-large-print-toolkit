# GLOW 6.0.0 Release Notes - May 9, 2026

## Overview

GLOW 6.0.0 is the release where the project becomes easier to join and easier to explain.

It introduces a cleaner open source contribution story, a focused Ollama-first AI setup path, a live sidebar usage indicator, and better release messaging across the website and docs.

This version is intentionally narrower than the long-term AI plan. The first release of personal AI support is limited to the text workflows that are easiest to trust: heading detection and MarkItDown support, plus General Chat in AI Playground. Document Chat remains intentionally separate and disabled by default.

## Highlights

### 1. Open source contribution flow

The project now explains the contribution path more clearly:

- fork the repository
- create a topic branch
- open a pull request
- work through branch protection and review

Why this matters:

- makes the project feel open to contribution, not just consumption
- helps new contributors understand the expected workflow
- aligns the release story with the open source contribution process already used in practice

### 2. Personal Ollama Cloud AI setup with AI Playground (Beta)

Users can bring their own Ollama Cloud account and key, then enable the AI features that make sense for this release:

- heading detection for Fix
- MarkItDown support for document cleanup and extraction
- **AI Playground (Beta)** -- a new standalone chat surface for experimenting with any Ollama model without document context

The AI Playground introduces an experimental testing ground where users can explore model capabilities, try different Ollama models, and verify behavior before using AI in production workflows.

What makes it magical:

- Accessible conversation structure: questions appear as H3 headings, answers as H4, so you can navigate directly between them with a keyboard or screen reader
- Smart response states: pending assistant messages show "Thinking…" while fetching, then transition seamlessly to the actual response with a copy button and model name
- Streaming token-by-token responses with graceful fallback to standard response mode when streaming is unavailable
- Regenerate last response without clearing conversation history
- Stop generation control for long-running responses
- In-page model switcher for playground without leaving the chat page
- Prompt template shortcuts for common tasks (summary, action items, plain language, ACB check, heading structure)
- Session quota/status meter and warning indicators in the playground UI
- Export conversation to Markdown for documentation handoff
- Per-feature model selection: choose different Ollama models for heading detection, MarkItDown, and the playground in one unified AI Features settings page
- Temporary session history: conversations stay in your session only, never persisted by default, so exploration is safe and private
- Typing indicator and smooth thinking animation: you see progress and feel heard while waiting for a response

AI setup improvements in this release:

- Key validation now accepts valid Ollama API keys even when they do not use the historical `ollama_` prefix
- Save is disabled until key validation succeeds, reducing accidental misconfiguration
- Document Chat and General Chat are explicitly separated via feature flags

Document Chat remains off by default in this release. The Playground stays as Beta to keep expectations clear while we refine the experience.

Why this matters:

- keeps the first AI release focused and understandable
- gives users a safe place to build confidence in Ollama before relying on AI in document workflows
- makes it easier to explain what AI is for inside GLOW
- the accessible heading structure (H3/H4) serves both sighted users navigating long conversations and screen reader users jumping between questions and answers

### 2.5 MarkItDown + AI Integration: Smarter Document Extraction

GLOW now offers **LLM-enhanced MarkItDown support** — Microsoft's MarkItDown library combined with an LLM to produce better text extraction.

What is enabled by default:

- **Heading detection** — converts bold or large text into semantic headings
- **Intelligent extraction** — MarkItDown + AI understands context and structure, not just layout
- **Cleaner documents** — page numbers, repeated footers, and noise are dropped automatically

How it works:

- When you audit or fix a document, heading detection runs if configured
- Text is extracted with AI awareness of structure and importance
- The result is cleaner input for accessibility workflows

Why this matters:

- headings and structure are objective problems (text is either a heading or not)
- MarkItDown + AI solves these consistently across formats (Word, PDF, Markdown, Excel, PowerPoint, ePub)
- the combined approach catches heading relationships that rule-based extraction misses
- less manual structure cleanup means more time for real accessibility fixes

Try it:

- Upload a document with missing or incorrect headings
- Use the AI Playground to test different Ollama models on a few headings first
- Then run Fix with heading detection on and see the full result

### 3. Visible AI usage tracking

The web app now shows a lightweight AI usage meter in the sidebar.

What it does:

- refreshes when the page loads
- refreshes after AI actions
- shows current-session request counts
- keeps the user oriented without forcing them to look elsewhere

### 4. Feedback-to-issue workflow

Feedback can now capture contact details for follow-up and sync into GitHub Issues when configured.

Why this matters:

- helps the project convert feedback into actionable work
- supports a clearer community support loop

### 5. Public release messaging aligned

The About page, changelog, user guide, and combined announcement now describe the new release in a shared language.

Why this matters:

- users see one coherent story across the site
- the release notes match the live product surface

## Compatibility and operations

- Non-AI workflows continue to work normally.
- Ollama AI features are intentionally limited in scope for 6.0.0.
- Shared OpenRouter-based AI paths remain available only where deployments already use them.

## Primary artifacts

- `CHANGELOG.md`
- `docs/announcement-v6.0.0-combined.md`
- `docs/announcement-v6.0.0-combined.html`
- `docs/user-guide.md`
- `web/src/acb_large_print_web/templates/about.html`
