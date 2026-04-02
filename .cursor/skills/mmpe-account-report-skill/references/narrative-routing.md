# Narrative Routing — MMPE Account Reports

Classify every account into **one** primary narrative profile before building the HTML.
The profile drives which cards appear, what copy leads, and what gets suppressed.

---

## Profiles

| Profile | Trigger | Lead story | Secondary |
|---------|---------|------------|-----------|
| **AI_LEAD** | `number_of_ai_tools_connected` ≥ 3 **and** `sum_of_ai_tools_total_usage` > 0 | AI adoption depth + expansion seats | User growth, adoption |
| **MULTI_PLAN** | `number_of_associated_paid_zapier_account` > 1 | Consolidation / governance | Users, tasks, AI |
| **ADOPTION_LEAD** | `adoption_rate_pct` < 25% **and** large `users_not_on_zapier` | Adoption runway / whitespace | Tasks, AI if present |
| **GROWTH** | `user_growth_pct` ≥ 15% | Momentum — fast user expansion | Tasks, AI |
| **STANDARD** | Everything else | Balanced: users + tasks + AI | Adoption context |

When multiple profiles could apply, pick the **strongest signal** using this priority:
`MULTI_PLAN` > `AI_LEAD` > `GROWTH` > `ADOPTION_LEAD` > `STANDARD`

Exception: if `paid_plan_count` = 1, **never** use `MULTI_PLAN` regardless of other signals.

---

## Display rules by profile

### AI_LEAD
- Subtitle: "AI-powered automation is accelerating across {{COMPANY_NAME}}."
- Row 1: Users card → AI tools card → Top apps card
- Row 3 AI panel: full detail (tool count + names)
- Task card: show growth % only if ≥ 5%; else 90d volume

### MULTI_PLAN
- Subtitle: "Multiple Zapier plans — opportunity to unify and scale."
- Row 1: Users card → Task/90d card → Paid footprint card (show plan count)
- Top apps card still present
- Row 3 AI panel: standard

### ADOPTION_LEAD
- Subtitle: "Significant room to expand Zapier adoption across the org."
- Row 2 adoption bar is the hero visual
- Suppress task growth % if < 5%
- AI panel: standard or zero-AI CTA

### GROWTH
- Subtitle: "Rapid user growth signals expanding automation impact."
- Lead with user growth % card
- Task card: show growth % if ≥ 5%

### STANDARD
- No subtitle injection
- Balanced card order as in template default

---

## Tone (customer-facing PDF)

- **Always:** growth-oriented, metrics-forward, factual
- **Never:** churn framing, "book a call" sales copy, internal jargon (MMPE, warehouse, Databricks, pipeline)
- **Suppress** task growth % when < 5% — replace with 90d billable tasks volume + positive framing ("active automation volume")
- **Suppress** multi-plan / consolidation when `paid_plan_count` ≤ 1
- **Suppress** spend growth % entirely (unreliable for customer share)
- AI panel: tool count + names only; no per-app run counts; merge OpenAI/ChatGPT into one label
- If AI tools = 0: one underutilization line + 2 top app names for a single CTA sentence

## Rep-only (chat, not HTML)

- Internal IDs, SQL caveats, Genie wording
- Suppression reasons (e.g. "task growth hidden: 2% < 5% threshold")
- Data-lineage notes
