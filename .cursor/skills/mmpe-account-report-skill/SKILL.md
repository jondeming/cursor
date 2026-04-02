---
name: mmpe-account-report-skill
description: >
  MMPE expansion-style HTML report from screenshot or IDs. Layout v4: no blue strips. Row 1: active users, task growth (if ≥5%) or 90d billable tasks,
  Top apps card (3–4 names from hightouch CRM+AI strings by Zapier account_id—no counts on PDF, no pipeline jargon). No spend/investment card.
  paid footprint only if paid_plan_count>1. Row 2: user chart + adoption. Row 3: AI chart + AI panel. SQL: mmpe-top-apps-by-account.sql; mmpe-ai-tools-hightouch.sql.
  Outputs outputs/mmpe-account-reports/.
---

# MMPE Account Report Skill

Generates a Zapier-branded, shareable HTML dashboard for a single customer account. **MMPE** = **Midmarket Proactive Outreach Experiment**—this is a **positioning narrative** for **expansion and follow-up**, not a neutral audit.

### How reps usually invoke this (default workflow)

**Most common:** the rep **screenshots one row** from their MMPE / spreadsheet (company + metrics), **pastes the image into Cursor**, and asks for the report (e.g. “MMPE report”, “run the account report”, or `company.com report`).

- **Treat the pasted screenshot as the primary source of truth** when the model can read the values (domain, users, tasks, AI, employees, paid-plan count, etc.).
- **Databricks / SQL** is optional enrichment when the warehouse is reachable—**do not** block the report if only the screenshot is available; never invent missing numbers.
- **Zapier account ID + HubSpot company ID:** When the user provides **both** (from the row or explicitly), run **`references/mmpe-enrichment-by-ids.sql`** (substitute literals) **before** domain-only fallbacks. That returns `production_modeled` metrics (users, tasks, rollups, HubSpot, outreach) for charts and cards—see [Step 2a](#step-2a--enrichment-by-zapier-account-id--hubspot-company-id).

### Adaptive narrative (read this first)

Use **`references/narrative-routing.md`** for routing, tone, and what to show vs omit.

- Lead with **momentum** and **expansion logic**; **enterprise consolidation** where it fits—**never** frame toward churn.
- **Paid Zapier plans:** show **multi-plan / consolidation** messaging **only** when **`paid_plan_count` > 1**. If there is a single plan (or only one paid plan), **omit** consolidation framing—there is no case to merge into one enterprise plan.
- **Task growth % (customer-facing HTML):** display **only** when **task growth % ≥ 5%**. If **task growth % &lt; 5%** (including negative or flat), **do not** show that percentage on the report; instead show **tasks used over the last 90 days** (or the best available **90d task total / volume** field from the row or SQL)—see Step 3b.
- **AI detail (v3):** Tool count + optional **names** from sync (no run counts); if **0** tools, use **two top apps** for CTA only—see **`references/narrative-routing.md`**.

The **primary** story remains **users vs company size** (adoption), with secondary metrics chosen to support a **strong headline**.

---

## Report layout — customer PDF (v4)

**Do not** add blue **Account snapshot** or **AI & automation alignment** strips—sales team feedback: too salesy for a customer PDF.

**Opening:** **Impact banner** (adoption heat) only, then optional **yellow insight** when adoption &lt; 50% (template default).

**Three content rows:**

| Row | Content |
|-----|---------|
| **1 — Top KPIs** | **Active users** + user growth %. **Second card:** **task growth %** only if **`task_growth_pct` ≥ 5%**; else **Billable tasks (trailing 90d)**. **Third card:** **Top apps** — **3–4** app display names for this **Zapier `account_id`** (the ID tied to the HubSpot company on the MMPE row). Use **`references/mmpe-top-apps-by-account.sql`** against the HubSpot sync table; merge and rank **internally** from `top_5_crm_last_30_days` + `top_5_ai_tools_last_30_days`. **Do not** print task counts next to app names. **Do not** mention **Databricks**, **tables**, **warehouses**, or **queries** on the PDF—customer-safe copy only. **Removed:** estimated investment / spend card. **Never** show **spend growth %** on the customer PDF. **Fourth card (optional):** paid footprint **only if `paid_plan_count` > 1**. |
| **2 — Adoption** | **User growth** chart + **Users vs. company size** (adoption % + bar). **Only** the large **“Not yet on Zapier”** count remains under the bar—**remove** “On Zapier” row and **never** append **user growth %** or **spend growth %** under this card. |
| **3 — AI** | **AI tool usage (30d)** chart + detail panel: **`number_of_ai_tools_connected`** (from row or HubSpot sync). Parse **`top_5_ai_tools_last_30_days`** for **names only**—**no per-app run counts** on the PDF. **Merge** OpenAI + ChatGPT into one label (e.g. “OpenAI”). If **`number_of_ai_tools_connected` = 0**: state underutilization; use **`ask_data`** (or approved SQL) for **two top app names** only and a single CTA line—see **`references/mmpe-top-apps-for-cta.md`**. **Do not** list top Zaps or full app/Zap activity (PII policy). |

---

## Workspace rules (Data team)

Follow the shared Cursor rules in `.cursor/rules/` while executing this skill:

| Rule file | How this skill complies |
|-----------|-------------------------|
| **`sql-metric-types.mdc`** | `user_count`, `employee_count`, and `annual_spend` are **point-in-time (balance-sheet style)** fields: only read them at the **specific `date_partition` keys** in the queries below—never blend or sum across snapshot dates for the same metric. `credit_usage_90d` and `ai_tool_usage_30d` are **period-activity values as-of** that snapshot row; baseline comparisons use two partition dates, not a sum over daily fact tables. |
| **`databricks-genie.mdc`** | Target **`production_refined`** on the **production** workspace. Reference config from that rule: host `https://dbc-37d560c2-40fd.cloud.databricks.com`, CLI profile **`production`** when using the CLI. If the Databricks MCP is wired to the **development** host (`DEFAULT` profile per that rule), only use it when it can read `production_refined`; otherwise use CLI **`-p production`** or Zapier `databricks_query_sql_warehouse` against a production warehouse. For open-ended account questions *outside* these fixed queries, Zapier Account Genie (**ZAG**, space `01f0cf03ff95191e992d5268cf57686f`) is the trusted discovery path—but **keep the SQL below** for the MMPE dashboard so output stays reproducible. |
| **`zapier-mcp.mdc`** | Any Zapier MCP tool call must include **`instructions`** and **`output_hint`** explicitly. For `databricks_query_sql_warehouse`, add **`sql_statement`** (full query text) and **`warehouse_id`** as required by the tool schema. |

### Execution order for SQL

1. **Databricks MCP** (`user-databricks-agent`): read the tool descriptor(s) under the MCP filesystem, then run the warehouse/SQL tool per schema (e.g. warehouse id + statement). If the server is unavailable, say so briefly and fall back.
2. **Zapier MCP** `databricks_query_sql_warehouse`: same SQL, with **`instructions`**, **`output_hint`**, **`sql_statement`**, **`warehouse_id`** per the rows above.
3. **Databricks CLI**: `databricks sql execute` (or equivalent) with **`-p production`** when executing against production.

---

## Step 0 — Data at hand + narrative intent

1. **Screenshot (default)** — If the user pasted an **image** of a spreadsheet row, **extract** domain, account name, user counts, task fields, `task_growth_pct`, **`total_billable_tasks_last_90d`**, AI usage (e.g. 30d interactions), **`number_of_ai_tools_connected`** when present, employees, **`paid_plan_count`**. Use these values for Steps 3–4 even if SQL is skipped.
2. **Text paste / file** — Same fields if pasted as text or referenced from an open CSV row.
3. **Gaps** — Missing credits, AI, or spend is fine; **do not** fabricate. Route narrative per **`references/narrative-routing.md`**.
4. **Audience** — Default: **customer-facing** HTML (growth-oriented, rules below). Internal-only caveats go in **chat**.

### Customer-facing PDF (default)

The saved HTML is **printed or shared with the customer**—metrics-forward, **no** blue narrative strips, **no** “book a call” sales copy unless the team explicitly asks for a custom build.

- **On the HTML/PDF:** No **MMPE**, **warehouse**, **Databricks**, row IDs, or internal suppression explanations. No **spend growth %** (unreliable for customer share).
- **Task growth %:** Step 3b—if **`task_growth_pct` &lt; 5%**, omit the %; lead with **90-day billable** volume.
- **Top apps card:** Names only; no internal data-lineage language on the PDF.
- **Rep-only:** IDs, SQL caveats, Genie wording in **chat**—see **`references/narrative-routing.md`**.

**Classify** a **narrative profile** (e.g. `AI_LEAD`, `MULTI_PLAN`, `ADOPTION_LEAD`, `STANDARD`) using **`references/narrative-routing.md`**. **`MULTI_PLAN`** applies **only** when **`paid_plan_count` > 1**.

---

## Step 1 — Extract domain and optional IDs

1. **Domain** — Parse from the message or screenshot (`hubspot_company_domain`). Strip protocol/`www.`, lowercase. If missing, ask: _"What's the account domain?"_

2. **Zapier account ID** — Integer **`account_id`** on MMPE exports and in `fact_daily_account_*` / `user_growth` (e.g. `4766988`). This is **`dha.zapier_account_id`** in `dim_hubspot_account`—**not** the same as HubSpot’s internal `hubspot_account_id` unless your spreadsheet labels them; use the column that matches **Zapier’s account key**.

3. **HubSpot company ID** — Integer **`hubspot_company_id`** (CRM company record).

When **both** (1) Zapier account id and (2) HubSpot company id are present, use [Step 2a](#step-2a--enrichment-by-zapier-account-id--hubspot-company-id). When only the domain is present, use Step 2b (`production_refined` by domain) or screenshot-only.

---

## Step 2 — Query Databricks

**Order:**

1. If **`zapier_account_id`** and **`hubspot_company_id`** are both available → **Step 2a** (enrichment SQL).
2. Else → **Step 2b** (domain queries on `production_refined`, or skip if no warehouse).

Use the **execution order** in [Workspace rules (Data team)](#workspace-rules-data-team) for tool calls.

### Step 2a — Enrichment by Zapier account ID + HubSpot company ID

- Run **`references/mmpe-enrichment-by-ids.sql`** against Databricks (`production_modeled`). Replace the example literals at the bottom with the rep’s **`account_id`** (Zapier) and **`hubspot_company_id`**. This **joins** `user_growth` to HubSpot via `dim_hubspot_account` / bridge and **filters** so the company matches the Zapier account—catching bad joins early if the pair is wrong.
- **Map results** into the report:
  - Users / tasks / rollups / adoption vs HubSpot headcount as in that row.
  - **Top apps (Row 1):** Run **`references/mmpe-top-apps-by-account.sql`** (substitute **`account_id`** — Zapier account id from the MMPE row, paired with HubSpot company id in enrichment). Build **`{{TOP_APPS_CARD_INNER_HTML}}`** per **`dashboard-template.md`**. If the query returns no row, fall back to **chat** for the rep—do **not** invent app names on the PDF.
  - Template **v4** has **no** credit chart, **no** spend/investment card, **no** `#spendPill`.
- Optional: **`references/mmpe-chart-series-monthly.sql`** for richer time-series charts (replace `account_id` literal); use when the rep wants trend visuals beyond the default template.

If the query returns **no rows**, the ID pair may not match CRM bridges—tell the rep and fall back to screenshot-only or domain SQL.

### Step 2a (continued) — AI tools detail (`hightouch`)

When building **AI tool** sections or charts beyond the spreadsheet row, run **`references/mmpe-ai-tools-hightouch.sql`** (adjust `WHERE` if your table uses a different account column name—confirm with `DESCRIBE` / Catalog Explorer).

**Table:** `production_modeled.hightouch.stg_dwh_to_hubspot_account`  
**Filter:** Zapier **`account_id`** (same ID as MMPE export / `fact_daily_account_*`).

| Column | Use in report |
|--------|----------------|
| `total_usage_last_30_days_ai_tools` | 30d AI tool execution volume (tasks + triggers); use for **`{{AI_USAGE_RAW}}`** / narrative when you want Databricks-grounded counts vs spreadsheet `sum_of_ai_tools_total_usage`. Prefer **one** source per report—if both exist, prefer **hightouch** for AI-specific charts when the query succeeds. |
| `top_5_ai_tools_last_30_days` | Parse for **app names only**; **omit** run counts on the PDF. Merge **OpenAI** / **ChatGPT** into one label. |
| Tool count | Prefer **`number_of_ai_tools_connected`** from the **MMPE row** if the hightouch table does not expose it. |

**Notes:** If **`number_of_ai_tools_connected` = 0**, do **not** substitute top Zaps—use **`references/mmpe-top-apps-for-cta.md`** (two app names + CTA only).

### Step 2b — Domain-based snapshot (`production_refined`)

Use when Step 2a is not used.

### Account snapshot table (FQN)

All queries below read one logical table: **account-level snapshots** with at least `domain`, `date_partition`, `user_count`, `annual_spend`, `credit_usage_90d`, `ai_tool_usage_30d`, `employee_count` (or equivalents you map in Step 3).

**Default fully qualified name** (from the original Cowork skill—**confirm or replace** with what your org actually exposes):

`production_refined.accounts.account_snapshots`

- If Data gives a **different** `catalog.schema.table`, update **every** `FROM` / subquery in queries A–D to that FQN (find/replace in this file).
- If Data gives **different SQL** that still produces the same metrics, replace queries A–D entirely and adjust Step 3 to match the **column aliases** in the new result set.

### Cannot see `production_refined` in Catalog Explorer?

Work through these in order:

1. **Confirm workspace URL** matches **production** in `.cursor/rules/databricks-genie.mdc` (not the development / MCP host). Catalogs differ by workspace.
2. **Permissions** — Unity Catalog can hide catalogs you are not granted. If peers see `production_refined` and you do not, request **USE CATALOG** / **SELECT** on the relevant catalog and schema from Data / IT. No amount of SQL fixes missing grants.
3. **Name drift** — The table may have moved (new catalog, `dbt_` schema, renamed view). Use internal discovery:
   - **Data Index QA** Genie space `01f0c581067117ad8e1184e06bfd7956` — ask where the **account snapshot** (or domain-level user / employee) table lives.
   - **Zapier Account Genie (ZAG)** `01f0cf03ff95191e992d5268cf57686f` — ask for the recommended table/view for **account metrics by domain**.
4. **Explorer search** — In Catalog Explorer, search for `account_snapshots` or `account_snap` across catalogs you *can* see; your org may use a different catalog prefix than `production_refined`.
5. **Warehouse** — You can lack Explorer visibility but still run SQL if someone shares the exact FQN; if `SELECT 1 FROM <fqn> LIMIT 1` works in a SQL editor, use that FQN in this skill.

---

Use `date_partition = (SELECT MAX(date_partition) FROM [same snapshot FQN])` for current snapshots. Use `TRY_CAST` for amount fields.

Run these queries. Replace `'{{domain}}'` with the extracted domain each time.

### Query A — User counts (Jan 2025 baseline vs current)
```sql
SELECT
  SUM(CASE WHEN date_partition = 20250101 THEN user_count ELSE 0 END) AS users_jan_2025,
  SUM(CASE WHEN date_partition = (SELECT MAX(date_partition) FROM production_refined.accounts.account_snapshots) THEN user_count ELSE 0 END) AS users_current
FROM production_refined.accounts.account_snapshots
WHERE domain = '{{domain}}'
  AND date_partition IN (20250101, (SELECT MAX(date_partition) FROM production_refined.accounts.account_snapshots))
```

### Query B — Annual spend (Jan 2025 baseline vs current)
```sql
SELECT
  SUM(CASE WHEN date_partition = 20250101 THEN TRY_CAST(annual_spend AS DOUBLE) ELSE 0 END) AS spend_jan_2025,
  SUM(CASE WHEN date_partition = (SELECT MAX(date_partition) FROM production_refined.accounts.account_snapshots) THEN TRY_CAST(annual_spend AS DOUBLE) ELSE 0 END) AS spend_current
FROM production_refined.accounts.account_snapshots
WHERE domain = '{{domain}}'
  AND date_partition IN (20250101, (SELECT MAX(date_partition) FROM production_refined.accounts.account_snapshots))
```

### Query C — 90-day credits (Dec 31 2024 vs current)
```sql
SELECT
  SUM(CASE WHEN date_partition = 20241231 THEN credit_usage_90d ELSE 0 END) AS credits_dec31,
  SUM(CASE WHEN date_partition = (SELECT MAX(date_partition) FROM production_refined.accounts.account_snapshots) THEN credit_usage_90d ELSE 0 END) AS credits_current
FROM production_refined.accounts.account_snapshots
WHERE domain = '{{domain}}'
  AND date_partition IN (20241231, (SELECT MAX(date_partition) FROM production_refined.accounts.account_snapshots))
```

### Query D — AI tool usage (last 30 days) + employee count
```sql
SELECT
  ai_tool_usage_30d,
  employee_count
FROM production_refined.accounts.account_snapshots
WHERE domain = '{{domain}}'
  AND date_partition = (SELECT MAX(date_partition) FROM production_refined.accounts.account_snapshots)
LIMIT 1
```

### If queries return no results
- Try matching on `LOWER(domain) LIKE LOWER('%{{domain}}%')` as a fallback
- If still no results, tell the user: _"I couldn't find data for [domain] in Databricks. Is this the correct domain?"_

---

## Step 3 — Calculate derived metrics

From the query results, compute:

| Metric | Formula |
|--------|---------|
| `user_growth_pct` | `(users_current - users_jan_2025) / users_jan_2025 * 100` |
| `spend_growth_pct` | `(spend_current - spend_jan_2025) / spend_jan_2025 * 100` |
| `credit_growth_pct` | `(credits_current - credits_dec31) / credits_dec31 * 100` |
| `ai_per_user` | `ai_tool_usage_30d / users_current` |
| `adoption_rate_pct` | `users_current / employee_count * 100` |
| `users_not_on_zapier` | `employee_count - users_current` |

Round all percentages to 1 decimal place. Round `ai_per_user` to nearest integer.

### Company size tier (for impact framing)
Classify the account based on `employee_count`:

| Tier label | Employee count |
|------------|----------------|
| SMB | < 200 |
| Mid-Market | 200–999 |
| Enterprise | 1,000–4,999 |
| Large Enterprise | 5,000–19,999 |
| Strategic | 20,000+ |

This tier label is used in the dashboard headline and chat summary to frame the user count in context.

### Adoption heat color (sliding scale)
The template computes `adoptionColor(pct)` in JavaScript — a smooth interpolation across these bands:

- **0–10%**: Very red → `#B91C1C` to `#DC2626`
- **11–25%**: Red → `#DC2626` to `#F97316`
- **26–50%**: Orange/yellow → `#F97316` to `#EAB308`
- **51–75%**: Yellow-green → `#EAB308` to `#84CC16`
- **76–100%**: Bright green → `#84CC16` to `#16A34A`

You do not need to compute a hex value yourself — just supply `{{ADOPTION_PCT}}` as a raw number and the template JS handles the rest.

### Step 3b — Apply narrative profile + display rules (after metrics)

Using **`references/narrative-routing.md`**:

- Pick **one lead story** (e.g. AI + expansion, multi-plan consolidation, adoption opportunity).
- **Task growth % (tasks only, customer-facing HTML):**
  - Show **task growth %** on the report **only if** `task_growth_pct` **≥ 5%** (use the rep’s row or computed value).
  - If `task_growth_pct` **&lt; 5%** (negative, zero, or weak positive), **do not** display that percentage. Instead, lead the task story with **tasks used in the last 90 days** (e.g. `total_billable_tasks_last_90d` or the closest field in the row/SQL) and growth-oriented copy (“active automation volume,” “baseline to build on”)—**not** “decline” language.
- **Paid Zapier plans:** include **multi-plan / consolidation** blocks **only** when **`paid_plan_count` > 1**. If count is **1** or unknown, **omit** paid-plan-count and consolidation sections—no enterprise-merge story without multiple plans.
- If **AI is strong** and a **single** paid plan, you can lead with AI + user expansion; keep adoption in support.

- **AI panel (customer-facing):** Factual only—**tool count**, **30d interaction total** (chart), and **“including tools like X, Y …”** from parsed top-5 **names** (no run counts). **Do not** add generic “book a call” AI alignment paragraphs on the PDF. If **0** tools connected, one line on underutilization + **two** top apps for a **single** CTA sentence per **`references/mmpe-top-apps-for-cta.md`**.

Document in **chat** (not on the HTML) anything suppressed and why (e.g. task % hidden because &lt; 5%).

---

## Step 4 — Render & save the HTML dashboard

Read the template from **`references/dashboard-template.md`** in this skill directory (same folder as this `SKILL.md`).

**Adaptive layout:** For non-`STANDARD` profiles, **edit the generated HTML** per **`references/narrative-routing.md`**: inject a 1–2 line **narrative subtitle** under the header, swap card copy, or remove/hide chart blocks when a metric is suppressed — **never** substitute fake numbers; use “—”, neutral copy, or conversation prompts.

### JavaScript-safe numbers (charts)

The template’s `<script>` block must only reference **numeric** placeholders where charts exist (**user growth**, **AI bar**). **Template v2** removes the credit chart—do not leave dangling `getElementById('creditChart')` calls.

Legacy note: older templates used **`{{CREDITS_DEC_NUM}}`** / **`{{CREDITS_NOW_NUM}}`** for a credit line chart; **v2** omits that chart entirely.

Substitution rules (v4 template):
- `{{COMPANY_NAME}}`, `{{DOMAIN}}`, `{{USERS_JAN}}`, `{{USERS_NOW}}`, `{{USER_GROWTH_PCT}}`, `{{ADOPTION_PCT}}`, `{{EMPLOYEES}}`, `{{EMPLOYEES_NOT_ON_ZAPIER}}`, `{{AS_OF_DATE}}`
- `{{ROW1_SECOND_CARD_INNER_HTML}}`, `{{TOP_APPS_CARD_INNER_HTML}}`, `{{PAID_FOOTPRINT_CARD_HTML}}`, `{{AI_DETAIL_PANEL_HTML}}`
- `{{AI_USAGE}}`, `{{AI_PER_USER}}`, `{{AI_USAGE_RAW}}` → chart + panel
- `{{ACCENT_COLOR}}` → pick from the list below based on domain hash (mod 5):
  - 0: `#0891B2` (teal/blue)
  - 1: `#7C3AED` (purple)
  - 2: `#059669` (green)
  - 3: `#D97706` (amber)
  - 4: `#DC2626` (red)

**Output path (Cursor / local workspace):**

1. Ensure the folder exists: `outputs/mmpe-account-reports/` at the **workspace root** (create it if missing).
2. Save the file as: `outputs/mmpe-account-reports/{domain}-report.html` (sanitize `{domain}` for filenames: replace `/` and odd characters with `-`).
3. Tell the user the absolute path to the file. On macOS, offer to open it: `open "/path/to/...html"`.

### Sharing the skill for rep testing

Reps do **not** need the full Cursor workspace. Pick one:

- **HTML-only:** Send the generated `outputs/mmpe-account-reports/{domain}-report.html`; they open in Chrome and **Save as PDF**. Easiest for “does this read well?” feedback.
- **Skill folder:** Zip **`.cursor/skills/mmpe-account-report-skill/`** (or copy to Google Drive / Slack) so another Cursor user can drop it under their project’s `.cursor/skills/` and invoke by name.
- **Single doc:** Paste **`SKILL.md`** into a Google Doc or internal wiki if the goal is **process review** without running the skill locally.

Remind testers that Databricks access from **their** machine may differ from yours—screenshot-first still works without warehouse access.

---

## Troubleshooting (Cursor vs Claude Cowork)

The original skill was built for **Claude Cowork** (or similar): a managed environment where a **production-capable SQL warehouse** was already wired up, outputs went to `/mnt/user-data/outputs/`, and the agent could run the queries without extra setup.

In **Cursor**, nothing automatically connects to Zapier production Databricks. You must attach a path that can execute SQL against Unity Catalog **`production_refined`**.

### That yellow “Partial run” banner is not a browser bug

If the agent could not read `production_refined.accounts.account_snapshots`, it may inject a short **disclosure** into the HTML so you do not mistake spend/credits/AI for real zeros. Fix connectivity below, then regenerate the report—the banner should disappear once all queries succeed.

### Symptom: `TABLE_OR_VIEW_NOT_FOUND` for `production_refined...account_snapshots`

This almost always means: **the SQL warehouse used for the query does not have that catalog in scope** (wrong workspace, wrong warehouse, or missing UC grant)—not that the SQL is wrong.

### Checklist

1. **Confirm the table exists (production workspace)**  
   In Databricks UI on **production** (see `.cursor/rules/databricks-genie.mdc` for host / profile): **Catalog Explorer** → `production_refined` → `accounts` → `account_snapshots`. If you cannot see it, your user needs catalog/schema access—ask Data / IT.

2. **Databricks MCP (`user-databricks-agent`)**  
   - **Cursor Settings → MCP**: ensure `databricks-agent` is connected (not red / errored).  
   - If it only talks to the **development** host (per `databricks-genie.mdc`), it may not expose `production_refined`. Prefer a config that can run SQL against **production** UC, or use CLI / Zapier with production.

3. **Zapier MCP `databricks_query_sql_warehouse`**  
   The tool accepts an optional **`warehouse_id`**. If empty, Zapier may use a **default warehouse that is not on production UC** → `TABLE_OR_VIEW_NOT_FOUND`.  
   - In Databricks **production**: **SQL Warehouses** → copy the warehouse **ID** (UUID) that analysts use for `production_refined`.  
   - Pass that `warehouse_id` on every `databricks_query_sql_warehouse` call (along with `instructions`, `output_hint`, `sql_statement` per `.cursor/rules/zapier-mcp.mdc`).

4. **Databricks CLI**  
   Install/configure CLI with a **`production`** profile pointing at the production host and run the skill SQL with `databricks sql execute -p production ...` (or equivalent). See `databricks-genie.mdc` for workspace host.

5. **Quick validation query** (after warehouse is correct)  
   `SELECT COUNT(*) AS n FROM production_refined.accounts.account_snapshots WHERE domain = 'honeybook.com' LIMIT 1`  
   If this fails, fix warehouse/catalog access before running the full MMPE queries.

---

## How to prompt (for reps)

**Typical (screenshot workflow):** Paste the **screenshot** of the spreadsheet row, then say e.g. **“MMPE report”**, **“account report”**, or **`company.com report`**. The agent reads visible columns from the image.

**Optional text** alongside the image helps (e.g. “lead with users + AI” or “multi-plan account”).

Examples:

- *[Image pasted]* “Run the MMPE report for this row.”
- *[Image pasted]* `honeybook.com report`
- No image: type the domain and key numbers in text if the screenshot isn’t available.

The agent applies **`references/narrative-routing.md`**, Step 3b (task **%** only if ≥ 5%; else 90d tasks; **multi-plan** only if **&gt; 1**; **Top apps** from SQL; AI detail—tool names only, or zero-AI CTA with two apps).

---

## Testing matrix (QA)

| # | Scenario | Must see | Must not see (customer HTML) |
|---|----------|----------|------------------------------|
| 1 | Screenshot row pasted + “MMPE report” | Domain/metrics from image; headline | Invented fields |
| 2 | `task_growth_pct` = 2% (or negative) | 90d task volume story; **no** task growth % | Task growth % |
| 3 | `task_growth_pct` = 10% | Task growth % allowed (≥ 5%) | — |
| 4 | `paid_plan_count` = 1 | No consolidation / multi-plan block | “Multiple plans” CTA |
| 5 | `paid_plan_count` = 3 | Multi-plan / governance angle | N/A |
| 6 | Missing credits/AI | “—” or omit | Fabricated numbers |
| 7 | AI tools > 0 | Tool count + “including tools like …” (no run counts) | Ranked Zap list; per-app run counts |
| 8 | AI tools = 0 | Underutilization line + 2 app names for CTA | Top Zaps list; full app activity dump |
| 9 | Template v2 (no credit chart) | User + AI charts + adoption JS run | Dangling `creditChart` references |
| 10 | Both IDs + enrichment SQL | Row from `mmpe-enrichment-by-ids.sql` | N/A |
| 11 | Default customer PDF | Charts render; Top apps card (3–4 names) | Spend/investment card; Databricks/table names on PDF |
| 12 | Adoption card | Large “not yet on Zapier” only | User growth % or spend growth % under that card |
| 13 | Top apps | Parsed from hightouch strings; ranked internally | Per-app task counts; “query” / “warehouse” copy |

---

## Display in chat

After saving the file, show a brief summary that **matches the chosen narrative profile** (not always the same order):

```
📊 [Company Name] · [Tier] · [DOMAIN] · [Narrative profile: e.g. AI_LEAD]

[Lead line — e.g. adoption, AI+seats, or multi-plan]

👥 Users: … (if central to story)
🔴/🟡/🟢 Adoption signal: … (when relevant)
[Optional: 💰 ⚡ only if shown on HTML]
```

If anything was **suppressed** from the customer file, add one line: _“Customer PDF excludes: [metric] (reason).”_

Do not paste the full HTML in chat. The HTML file is the deliverable.
