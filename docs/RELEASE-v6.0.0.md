# GLOW 6.0.0 Release Notes - May 9, 2026

## Overview

GLOW 6.0.0 is the release where the project becomes easier to join and easier to explain.

It introduces a cleaner open source contribution story, a focused Ollama-first AI setup path, a live sidebar usage indicator, and better release messaging across the website and docs.

This version is intentionally narrower than the long-term AI plan. The first release of personal AI support is limited to the text workflows that are easiest to trust: heading detection and MarkItDown support. Document Chat is intentionally left for a later step.

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
- Per-feature model selection: choose different Ollama models for heading detection, MarkItDown, and the playground in one unified AI Features settings page
- Temporary session history: conversations stay in your session only, never persisted by default, so exploration is safe and private
- Typing indicator and smooth thinking animation: you see progress and feel heard while waiting for a response

Document Chat remains off by default in this release. The Playground stays as Beta to keep expectations clear while we refine the experience.

Why this matters:

- keeps the first AI release focused and understandable
- gives users a safe place to build confidence in Ollama before relying on AI in document workflows
- makes it easier to explain what AI is for inside GLOW
- the accessible heading structure (H3/H4) serves both sighted users navigating long conversations and screen reader users jumping between questions and answers

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
