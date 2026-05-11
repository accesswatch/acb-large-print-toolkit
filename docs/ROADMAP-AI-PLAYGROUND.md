# GLOW AI Roadmap: High-Value Features for Magical Experiences

**Last Updated:** May 10, 2026  
**Current Release:** 6.0.0 (AI Playground Beta, Personal Provider Models, Streaming Responses, Key Validation Flow, Capability Gating)  
**Next Release:** 6.1.0 (Session Quotas, Follow-up Suggestions, Token Preview)  
**Vision:** Transform GLOW's AI capabilities into a fluid, responsive, and predictable conversation experience that makes accessibility guidance feel native and inevitable.

---

## Phase 1: Fluidity & Responsiveness (6.1.0 follow-ups)

### 1. Follow-Up Suggestions
- **Why:** Open WebUI shows "Here's what you might ask next." Reduces the "blank canvas" problem.
- **Technical:** After first response, have the model generate 2-3 follow-up prompts (separate call, cached). Show as chips.
- **Value:** Conversations feel more like guided workflows than open searches.

### 2. Token Counting & Cost Preview
- **Why:** Transparency matters. Users should know "this conversation will cost ~$0.05" before hitting Send.
- **Technical:** Use provider-aware token counters or implement a rough estimator. Show budget remaining in the meter when the provider exposes cost or quota meaningfully.
- **Value:** Trust. Users feel in control of cost. Prevents surprise usage spikes.

## Phase 2: Intelligence & Context (2-3 Sprints)

### 3. Prompt Templates for Common Tasks
- **Why:** "Summarize this section" or "Extract action items" are patterns we know work.
- **Technical:** Small library of templates stored in YAML or Markdown. Available in playground and Document Chat. Pre-fill text + instructions.
- **Value:** New users don't start from scratch. Templates encode GLOW domain knowledge.

### 4. Conversation History Search
- **Why:** Longer playground sessions become hard to navigate.
- **Technical:** Client-side search within session history. Optional: persist to encrypted local storage (future: cloud backup).
- **Value:** Faster retrieval inside long sessions.

## Phase 3: Robustness & Observability (1-2 Sprints)

### 5. Rate Limiting & Quota Enforcement
- **Why:** Currently meter shows usage, but no hard limits prevent abuse.
- **Technical:** Add `GLOW_AI_QUOTA_PER_SESSION` and `GLOW_AI_QUOTA_RESET_HOURS`. Enforce in middleware. Show countdown timer.
- **Value:** Fair-use model. Prevents one user from exhausting budget for everyone.

### 6. Response Validation Against ACB Guidelines
- **Why:** AI can hallucinate or produce non-compliant output (e.g., italicized text, unjustified layout instructions).
- **Technical:** After each response, run a quick validator: check for disallowed formatting, ACB rule violations. Flag before showing to user.
- **Value:** Prevents bad advice from leaking. Builds trust that AI is ACB-aware.

---

## Phase 4: Accessibility & Inclusivity (Ongoing)

### 7. Automated a11y Audits on Playground Responses
- **Why:** Responses should be checkable for WCAG compliance inline.
- **Technical:** On render, check contrast, semantic structure, heading hierarchy of response content. Badge it.
- **Value:** Teaches users what good accessibility looks like through real examples.

### 8. Alternative Input Modes
- **Why:** Some users may prefer voice or structured forms over free text.
- **Technical:** Extend capability-aware Whisperer integration to playground. Add "guided mode" with form fields instead of textarea.
- **Value:** Removes barriers for diverse users.

---

## Phase 5: Learning & Iteration (Ongoing)

### 9. Conversation Analytics Dashboard
- **Why:** See which models, features, and prompts are most successful.
- **Technical:** Anonymized event tracking (no PII): prompt type, model, success rate, time to response. Admin dashboard.
- **Value:** Data-driven roadmap. Identify which features users actually trust and use.

### 10. A/B Testing Infrastructure
- **Why:** We don't know if streaming or static responses are better. If follow-ups increase engagement or distract.
- **Technical:** Feature flags + randomized user cohorts. Track outcomes (engagement, correctness, satisfaction).
- **Value:** Move from instinct to evidence. Iterate faster.

---

## Implementation Priority

**Tier 1 / 6.1.0 (Do Next - 2 Weeks):**
- Session quota enforcement (fair-use guardrail)
- Follow-up suggestions
- Token preview (trust builder)

**Tier 2 / 6.2.0 (Next Month):**
- Prompt templates
- Conversation search

**Tier 3 / 6.3.0+ (Foundation Work):**
- ACB validation on responses
- Analytics dashboard
- A/B testing infrastructure

### 6.0.0 - What Shipped

✅ AI Playground (Beta) at `/beta/chat/`  
✅ SSE streaming responses with graceful fallback  
✅ Regenerate last response  
✅ In-page playground model switching  
✅ Prompt templates for common tasks  
✅ Session quota meter/warning UI  
✅ Export conversation as Markdown  
✅ Stop generation control  
✅ Per-feature provider/model selection  
✅ H3/H4 heading structure for accessible navigation  
✅ Copy-to-clipboard on responses  
✅ Chat surface feature-flag split (`GLOW_ENABLE_AI_GENERAL_CHAT` vs `GLOW_ENABLE_AI_CHAT`)  
✅ Beta sidebar section with Experimental badge
✅ Delayed screen reader announcements for in-progress and completed long-running replies
✅ Personal provider support for Ollama Cloud, OpenRouter, OpenAI, and Google Gemini
✅ Capability-aware feature filtering for alt-text, Whisperer, playground, and text workflows

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
- `Per-feature provider/model selection` — Completed in this session
- `AI Features settings page` — `/ai/` route
- `Magic Lab` — Advanced experimentation workspace
- `Document Chat` — Document-grounded AI Q&A
