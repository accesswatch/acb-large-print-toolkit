# GLOW AI Roadmap: High-Value Features for Magical Experiences

**Last Updated:** May 10, 2026  
**Vision:** Transform GLOW's AI capabilities into a fluid, responsive, and predictable conversation experience that makes accessibility guidance feel native and inevitable.

---

## Phase 1: Fluidity & Responsiveness (Next Sprint)

### 1. Streaming Responses
- **Why:** Current playground shows "Thinking…" then full response. Streaming makes responses feel more immediate and less like a "wait wall."
- **Technical:** Modify `/playground/send` to use Server-Sent Events (SSE) instead of JSON polling. Frontend can render tokens as they arrive.
- **Value:** Users see progress. Feels less like a black box. Works better over slow connections.

### 2. Response Regeneration for Playground
- **Why:** Users should be able to re-ask with different models or settings without clearing history.
- **Technical:** Add a "Regenerate" button on assistant messages that replays the last user message. Swap model if needed.
- **Value:** Exploration becomes low-friction. "What would Claude say vs. Ollama?" becomes a click away.

### 3. Per-Feature Model Switching (Live)
- **Why:** Currently requires navigating to Settings. Should be in-context.
- **Technical:** Add a small model picker overlay in the playground UI that updates `session["ollama_feature_models"]` without page reload via AJAX.
- **Value:** Experimentation velocity. Users can A/B test models mid-conversation.

---

## Phase 2: Intelligence & Context (2-3 Sprints)

### 4. Follow-Up Suggestions
- **Why:** Open WebUI shows "Here's what you might ask next." Reduces the "blank canvas" problem.
- **Technical:** After first response, have the model generate 2-3 follow-up prompts (separate call, cached). Show as chips.
- **Value:** Conversations feel more like guided workflows than open searches.

### 5. Prompt Templates for Common Tasks
- **Why:** "Summarize this section" or "Extract action items" are patterns we know work.
- **Technical:** Small library of templates stored in YAML or Markdown. Available in playground and Document Chat. Pre-fill text + instructions.
- **Value:** New users don't start from scratch. Templates encode GLOW domain knowledge.

### 6. Token Counting & Cost Preview
- **Why:** Transparency matters. Users should know "this conversation will cost ~$0.05" before hitting Send.
- **Technical:** Use Ollama token counter or implement a rough estimator. Show budget remaining in the meter.
- **Value:** Trust. Users feel in control of cost. Prevents surprise usage spikes.

---

## Phase 3: Robustness & Observability (1-2 Sprints)

### 7. Response Validation Against ACB Guidelines
- **Why:** AI can hallucinate or produce non-compliant output (e.g., italicized text, unjustified layout instructions).
- **Technical:** After each response, run a quick validator: check for disallowed formatting, ACB rule violations. Flag before showing to user.
- **Value:** Prevents bad advice from leaking. Builds trust that AI is ACB-aware.

### 8. Conversation History Search & Export
- **Why:** Longer playground sessions become hard to navigate. Users may want to save insights.
- **Technical:** Client-side search within session history. Export as Markdown. Optional: persist to encrypted local storage (future: cloud backup).
- **Value:** Conversations become a knowledge artifact, not disposable chats.

### 9. Rate Limiting & Quota Enforcement
- **Why:** Currently meter shows usage, but no hard limits prevent abuse.
- **Technical:** Add `GLOW_AI_QUOTA_PER_SESSION` and `GLOW_AI_QUOTA_RESET_HOURS`. Enforce in middleware. Show countdown timer.
- **Value:** Fair-use model. Prevents one user from exhausting budget for everyone.

---

## Phase 4: Accessibility & Inclusivity (Ongoing)

### 10. Automated a11y Audits on Playground Responses
- **Why:** Responses should be checkable for WCAG compliance inline.
- **Technical:** On render, check contrast, semantic structure, heading hierarchy of response content. Badge it.
- **Value:** Teaches users what good accessibility looks like through real examples.

### 11. Alternative Input Modes
- **Why:** Some users may prefer voice or structured forms over free text.
- **Technical:** Extend Whisperer integration to playground. Add "guided mode" with form fields instead of textarea.
- **Value:** Removes barriers for diverse users.

---

## Phase 5: Learning & Iteration (Ongoing)

### 12. Conversation Analytics Dashboard
- **Why:** See which models, features, and prompts are most successful.
- **Technical:** Anonymized event tracking (no PII): prompt type, model, success rate, time to response. Admin dashboard.
- **Value:** Data-driven roadmap. Identify which features users actually trust and use.

### 13. A/B Testing Infrastructure
- **Why:** We don't know if streaming or static responses are better. If follow-ups increase engagement or distract.
- **Technical:** Feature flags + randomized user cohorts. Track outcomes (engagement, correctness, satisfaction).
- **Value:** Move from instinct to evidence. Iterate faster.

---

## Implementation Priority

**Tier 1 (Do First - 2 Weeks):**
- Streaming responses (biggest UX leap)
- Response regeneration (low friction, high value)
- Token preview (trust builder)

**Tier 2 (Next Month):**
- Follow-up suggestions
- Prompt templates
- Conversation search

**Tier 3 (Foundation Work):**
- ACB validation on responses
- Rate limiting & quotas
- Analytics dashboard

---

## Why These, Not Others?

- **Streaming & regeneration:** Open WebUI taught us that perceived performance (fluidity) matters more than features.
- **Suggestions & templates:** Reduce cognitive load. Make playground feel like a guided workflow, not a search engine.
- **Validation & quotas:** Build trust. Users should feel GLOW is guardrails-aware and fair.
- **Analytics & A/B testing:** Without data, roadmap is opinion. These are the instruments.

---

## Out of Scope (For Now)

- ❌ RAG over documents in playground (Document Chat owns that)
- ❌ Custom tool-calling workflows (Magic Lab owns experimentation)
- ❌ Multi-turn reasoning agents (beyond conversation context)
- ❌ Fine-tuning or custom model training
- ❌ Mobile app (web first)

---

## Related Work

See also:
- `GLOW AI Playground (Beta)` — Completed in this session
- `Per-feature Ollama model selection` — Completed in this session
- `AI Features settings page` — `/ai/` route
- `Magic Lab` — Advanced experimentation workspace
- `Document Chat` — Document-grounded AI Q&A
