# Dashboard Template v4 — MMPE Account Report

The HTML below is the **single-file** template. Replace `{{PLACEHOLDERS}}` with computed values.

## Placeholder Reference

| Placeholder | Type | Description |
|-------------|------|-------------|
| `{{COMPANY_NAME}}` | string | Display name of the company |
| `{{DOMAIN}}` | string | Company domain (lowercase, no protocol) |
| `{{USERS_JAN}}` | int | Users as of Jan 2025 |
| `{{USERS_NOW}}` | int | Users current |
| `{{USER_GROWTH_PCT}}` | float | User growth % (1 decimal) |
| `{{ADOPTION_PCT}}` | float | Adoption rate % (1 decimal) |
| `{{EMPLOYEES}}` | int | Total employee count |
| `{{EMPLOYEES_NOT_ON_ZAPIER}}` | int | Employees − current users |
| `{{AS_OF_DATE}}` | string | e.g. "March 2026" |
| `{{ROW1_SECOND_CARD_INNER_HTML}}` | html | Task growth % card OR 90d task volume card |
| `{{TOP_APPS_CARD_INNER_HTML}}` | html | 3–4 app names |
| `{{PAID_FOOTPRINT_CARD_HTML}}` | html | Full card block (or empty if paid_plan_count ≤ 1) |
| `{{AI_DETAIL_PANEL_HTML}}` | html | AI tools detail content |
| `{{AI_USAGE}}` | string | Formatted AI usage (e.g. "1,234 interactions") |
| `{{AI_PER_USER}}` | int | AI interactions per user |
| `{{AI_USAGE_RAW}}` | int | Raw numeric AI usage for chart |
| `{{ACCENT_COLOR}}` | hex | Brand accent color |
| `{{NARRATIVE_SUBTITLE}}` | html | Profile-driven subtitle (or empty for STANDARD) |
| `{{TIER_LABEL}}` | string | SMB / Mid-Market / Enterprise / etc. |
| `{{USER_GROWTH_CHART_DATA}}` | json | Array for user chart |
| `{{AI_CHART_DATA}}` | json | Array for AI chart |
| `{{TOTAL_TASKS_90D}}` | string | Formatted 90d billable tasks |
| `{{TASK_GROWTH_PCT}}` | float | Task growth % (only used if ≥ 5) |

## HTML Template

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{COMPANY_NAME}} — Zapier Account Report</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; background: #F8FAFC; color: #1E293B; line-height: 1.6; }
  .container { max-width: 900px; margin: 0 auto; padding: 32px 24px; }

  /* Header */
  .header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
  .header-left { display: flex; align-items: center; gap: 16px; }
  .zapier-logo { width: 36px; height: 36px; }
  .header h1 { font-size: 22px; font-weight: 700; color: #0F172A; }
  .header .domain { font-size: 13px; color: #64748B; font-weight: 500; }
  .header .date { font-size: 12px; color: #94A3B8; }

  .narrative-subtitle { font-size: 14px; color: #475569; margin-bottom: 20px; font-style: italic; padding-left: 52px; }

  /* Impact Banner */
  .impact-banner {
    background: linear-gradient(135deg, {{ACCENT_COLOR}}11 0%, {{ACCENT_COLOR}}05 100%);
    border: 1px solid {{ACCENT_COLOR}}33;
    border-radius: 12px; padding: 20px 24px; margin-bottom: 24px;
    display: flex; align-items: center; gap: 16px;
  }
  .impact-dot { width: 48px; height: 48px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 20px; font-weight: 800; color: white; flex-shrink: 0; }
  .impact-text h2 { font-size: 16px; font-weight: 700; color: #0F172A; }
  .impact-text p { font-size: 13px; color: #475569; margin-top: 2px; }

  /* Insight callout */
  .insight-callout { background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 10px; padding: 14px 18px; margin-bottom: 24px; font-size: 13px; color: #92400E; }
  .insight-callout strong { font-weight: 600; }

  /* KPI Cards Row */
  .kpi-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 16px; margin-bottom: 28px; }
  .kpi-card {
    background: white; border-radius: 12px; padding: 20px;
    border: 1px solid #E2E8F0; transition: box-shadow 0.2s;
  }
  .kpi-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.06); }
  .kpi-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: #94A3B8; font-weight: 600; margin-bottom: 8px; }
  .kpi-value { font-size: 28px; font-weight: 800; color: #0F172A; }
  .kpi-sub { font-size: 12px; color: #64748B; margin-top: 4px; }
  .kpi-change { display: inline-flex; align-items: center; gap: 4px; font-size: 12px; font-weight: 600; margin-top: 6px; padding: 2px 8px; border-radius: 9999px; }
  .kpi-change.up { background: #DCFCE7; color: #166534; }
  .kpi-change.neutral { background: #F1F5F9; color: #475569; }

  /* Content sections */
  .section { background: white; border-radius: 12px; padding: 24px; border: 1px solid #E2E8F0; margin-bottom: 20px; }
  .section-title { font-size: 15px; font-weight: 700; color: #0F172A; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }
  .section-title .icon { font-size: 18px; }

  /* Charts */
  .chart-container { position: relative; height: 200px; margin: 16px 0; }
  canvas { width: 100% !important; max-height: 200px; }

  /* Adoption bar */
  .adoption-bar-wrap { margin: 16px 0; }
  .adoption-bar-bg { height: 32px; background: #F1F5F9; border-radius: 16px; overflow: hidden; position: relative; }
  .adoption-bar-fill { height: 100%; border-radius: 16px; transition: width 0.8s ease; }
  .adoption-stat { display: flex; justify-content: space-between; margin-top: 10px; font-size: 13px; color: #64748B; }
  .adoption-big { font-size: 36px; font-weight: 800; color: #0F172A; text-align: center; margin-top: 12px; }
  .adoption-big-label { font-size: 13px; color: #64748B; text-align: center; }

  /* AI panel */
  .ai-stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 12px; }
  .ai-stat-box { background: #F8FAFC; border-radius: 10px; padding: 14px; text-align: center; }
  .ai-stat-box .num { font-size: 24px; font-weight: 800; color: #0F172A; }
  .ai-stat-box .lbl { font-size: 11px; color: #64748B; margin-top: 2px; }
  .ai-tools-list { margin-top: 12px; font-size: 13px; color: #475569; }

  /* Top apps */
  .top-apps-list { list-style: none; padding: 0; }
  .top-apps-list li { padding: 6px 0; font-size: 14px; color: #334155; display: flex; align-items: center; gap: 8px; }
  .top-apps-list li::before { content: "⚡"; font-size: 14px; }

  /* Footer */
  .footer { text-align: center; padding: 24px 0 8px; font-size: 11px; color: #94A3B8; }

  /* Two-col layout */
  .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
  @media (max-width: 700px) { .two-col { grid-template-columns: 1fr; } }

  /* Print */
  @media print {
    body { background: white; }
    .container { padding: 16px; }
    .kpi-card:hover { box-shadow: none; }
  }
</style>
</head>
<body>
<div class="container">

  <!-- Header -->
  <div class="header">
    <div class="header-left">
      <svg class="zapier-logo" viewBox="0 0 36 36" fill="none"><circle cx="18" cy="18" r="18" fill="#FF4A00"/><path d="M25.5 18L20.12 13.5V16.5H10.5V19.5H20.12V22.5L25.5 18Z" fill="white"/></svg>
      <div>
        <h1>{{COMPANY_NAME}}</h1>
        <span class="domain">{{DOMAIN}} · {{TIER_LABEL}}</span>
      </div>
    </div>
    <span class="date">{{AS_OF_DATE}}</span>
  </div>

  {{NARRATIVE_SUBTITLE}}

  <!-- Impact Banner -->
  <div class="impact-banner">
    <div class="impact-dot" id="adoptionDot">{{ADOPTION_PCT_ROUND}}</div>
    <div class="impact-text">
      <h2>{{ADOPTION_PCT}}% Zapier adoption across the org</h2>
      <p>{{USERS_NOW}} active users out of {{EMPLOYEES}} employees</p>
    </div>
  </div>

  {{INSIGHT_CALLOUT_HTML}}

  <!-- Row 1: KPI Cards -->
  <div class="kpi-row">
    <!-- Card 1: Active Users -->
    <div class="kpi-card">
      <div class="kpi-label">Active Users</div>
      <div class="kpi-value">{{USERS_NOW}}</div>
      <div class="kpi-sub">from {{USERS_JAN}} in Jan 2025</div>
      <div class="kpi-change up">↑ {{USER_GROWTH_PCT}}% growth</div>
    </div>

    <!-- Card 2: Task metric (dynamic) -->
    <div class="kpi-card">
      {{ROW1_SECOND_CARD_INNER_HTML}}
    </div>

    <!-- Card 3: Top Apps -->
    <div class="kpi-card">
      <div class="kpi-label">Top Apps</div>
      {{TOP_APPS_CARD_INNER_HTML}}
    </div>

    <!-- Card 4: Paid footprint (conditional) -->
    {{PAID_FOOTPRINT_CARD_HTML}}
  </div>

  <!-- Row 2: Adoption -->
  <div class="two-col">
    <div class="section">
      <div class="section-title"><span class="icon">📈</span> User Growth</div>
      <div class="chart-container">
        <canvas id="userChart"></canvas>
      </div>
    </div>
    <div class="section">
      <div class="section-title"><span class="icon">🏢</span> Users vs. Company Size</div>
      <div class="adoption-bar-wrap">
        <div class="adoption-bar-bg">
          <div class="adoption-bar-fill" id="adoptionBar" style="width: {{ADOPTION_PCT}}%; background: linear-gradient(90deg, {{ACCENT_COLOR}}, {{ACCENT_COLOR}}CC);"></div>
        </div>
      </div>
      <div class="adoption-big" id="notOnZapier">{{EMPLOYEES_NOT_ON_ZAPIER}}</div>
      <div class="adoption-big-label">employees not yet on Zapier</div>
    </div>
  </div>

  <!-- Row 3: AI -->
  <div class="two-col">
    <div class="section">
      <div class="section-title"><span class="icon">🤖</span> AI Tool Usage (30 days)</div>
      <div class="chart-container">
        <canvas id="aiChart"></canvas>
      </div>
    </div>
    <div class="section">
      <div class="section-title"><span class="icon">✨</span> AI & Automation</div>
      {{AI_DETAIL_PANEL_HTML}}
    </div>
  </div>

  <div class="footer">
    Powered by Zapier · {{DOMAIN}} · Generated {{AS_OF_DATE}}
  </div>

</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<script>
  // Adoption dot color
  (function(){
    var pct = {{ADOPTION_PCT}};
    var dot = document.getElementById('adoptionDot');
    function adoptionColor(p){
      if(p<=10) return '#DC2626';
      if(p<=25) return '#F97316';
      if(p<=50) return '#EAB308';
      if(p<=75) return '#84CC16';
      return '#16A34A';
    }
    dot.style.background = adoptionColor(pct);
  })();

  // User Growth Chart
  (function(){
    var ctx = document.getElementById('userChart');
    if(!ctx) return;
    new Chart(ctx, {
      type: 'bar',
      data: {
        labels: ['Jan 2025', 'Current'],
        datasets: [{
          label: 'Active Users',
          data: [{{USERS_JAN}}, {{USERS_NOW}}],
          backgroundColor: ['#CBD5E1', '{{ACCENT_COLOR}}'],
          borderRadius: 8,
          barThickness: 48
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true, grid: { color: '#F1F5F9' } }, x: { grid: { display: false } } }
      }
    });
  })();

  // AI Chart
  (function(){
    var ctx = document.getElementById('aiChart');
    if(!ctx) return;
    var raw = {{AI_USAGE_RAW}};
    new Chart(ctx, {
      type: 'bar',
      data: {
        labels: ['AI Tool Interactions (30d)'],
        datasets: [{
          label: 'AI Usage',
          data: [raw],
          backgroundColor: ['#7C3AED'],
          borderRadius: 8,
          barThickness: 48
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { x: { beginAtZero: true, grid: { color: '#F1F5F9' } }, y: { grid: { display: false } } }
      }
    });
  })();
</script>
</body>
</html>
```
