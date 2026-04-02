#!/usr/bin/env python3
"""
MMPE Account Report Generator
Reads CSV rows of company data and produces one Zapier-branded HTML dashboard per row.
Layout v4: no blue strips, no spend card. See .cursor/skills/mmpe-account-report-skill/SKILL.md
"""

import csv
import html
import hashlib
import io
import math
import os
import re
import sys
from datetime import datetime
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent
OUTPUT_DIR = WORKSPACE / "outputs" / "mmpe-account-reports"

ACCENT_COLORS = ["#0891B2", "#7C3AED", "#059669", "#D97706", "#DC2626"]

COLUMN_NAMES = [
    "hubspot_company_name",
    "hubspot_company_domain",
    "midmarket_rep_assigned",
    "t1_linkedin_note_completed",
    "t2_loom_email_completed",
    "t3_day5_6_followup_completed",
    "primary_outreach_contact",
    "primary_outreach_contact_email",
    "primary_outreach_contact_title",
    "account_id",
    "account_name",
    "zapier_account_owner_email",
    "user_growth_pct",
    "task_growth_pct",
    "total_billable_tasks_last_90d",
    "number_of_ai_tools_connected",
    "sum_of_ai_tools_total_usage",
    "number_of_associated_paid_zapier_account",
    "dim_hs_company_country",
    "users_jan2025",
    "users_jan2026",
    "user_delta",
    "total_billable_tasks_last_365d",
    "tasks_jan2025",
    "company_number_of_employees",
    "tasks_jan2026",
    "task_delta",
    "avg_daily_billable_tasks_last_365d",
    "days_with_usage_in_last_90d",
    "days_with_usage_in_last_365d",
    "usage_rollups_as_of_date",
    "domain_company_size",
    "hubspot_vertical",
    "hubspot_industry",
    "outreach_contact_hubspot_id",
    "dim_hs_company_state_region",
    "dim_hs_company_country_region_code",
    "dim_hs_company_state_region_code",
    "hubspot_company_id",
    "dim_hs_country_region_summary",
    "routing_prior_hubspot_owner_email",
]


def safe_int(val, default=0):
    if val is None:
        return default
    val = str(val).strip().replace(",", "").replace("%", "")
    if val in ("", "-", "—", "N/A", "null", "None"):
        return default
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default


def safe_float(val, default=0.0):
    if val is None:
        return default
    val = str(val).strip().replace(",", "").replace("%", "")
    if val in ("", "-", "—", "N/A", "null", "None"):
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def fmt_num(n):
    return f"{n:,.0f}" if isinstance(n, (int, float)) else str(n)


def sanitize_domain(domain):
    d = domain.lower().strip()
    d = re.sub(r'^https?://', '', d)
    d = re.sub(r'^www\.', '', d)
    d = d.rstrip('/')
    return d


def accent_for_domain(domain):
    h = int(hashlib.md5(domain.encode()).hexdigest(), 16)
    return ACCENT_COLORS[h % 5]


def tier_label(employees):
    if employees < 200:
        return "SMB"
    if employees < 1000:
        return "Mid-Market"
    if employees < 5000:
        return "Enterprise"
    if employees < 20000:
        return "Large Enterprise"
    return "Strategic"


def classify_profile(row_data):
    ai_tools = safe_int(row_data.get("number_of_ai_tools_connected"))
    ai_usage = safe_int(row_data.get("sum_of_ai_tools_total_usage"))
    paid_plans = safe_int(row_data.get("number_of_associated_paid_zapier_account"))
    users_now = safe_int(row_data.get("users_jan2026"))
    employees = safe_int(row_data.get("company_number_of_employees"), 1)
    adoption_pct = (users_now / employees * 100) if employees > 0 else 0
    user_growth = safe_float(row_data.get("user_growth_pct"))

    if paid_plans > 1:
        return "MULTI_PLAN"
    if ai_tools >= 3 and ai_usage > 0:
        return "AI_LEAD"
    if user_growth >= 15:
        return "GROWTH"
    if adoption_pct < 25 and (employees - users_now) > 50:
        return "ADOPTION_LEAD"
    return "STANDARD"


def narrative_subtitle(profile, company_name):
    subs = {
        "AI_LEAD": f"AI-powered automation is accelerating across {company_name}.",
        "MULTI_PLAN": f"Multiple Zapier plans — opportunity to unify and scale.",
        "ADOPTION_LEAD": f"Significant room to expand Zapier adoption across the org.",
        "GROWTH": f"Rapid user growth signals expanding automation impact.",
        "STANDARD": "",
    }
    txt = subs.get(profile, "")
    if txt:
        return f'<div class="narrative-subtitle">{html.escape(txt)}</div>'
    return ""


def build_second_card(task_growth_pct, total_90d):
    if task_growth_pct >= 5:
        return f"""
      <div class="kpi-label">Task Growth</div>
      <div class="kpi-value">{task_growth_pct:.1f}%</div>
      <div class="kpi-sub">year-over-year</div>
      <div class="kpi-change up">↑ growing automation volume</div>"""
    else:
        return f"""
      <div class="kpi-label">Billable Tasks (90 days)</div>
      <div class="kpi-value">{fmt_num(total_90d)}</div>
      <div class="kpi-sub">active automation volume</div>
      <div class="kpi-change neutral">📊 baseline to build on</div>"""


def build_top_apps_card(row_data):
    apps = []
    for field in ["hubspot_vertical", "hubspot_industry"]:
        val = row_data.get(field, "")
        if val and val not in ("-", "—", "N/A", "", "null", "None"):
            apps.append(str(val).strip())

    domain = sanitize_domain(row_data.get("hubspot_company_domain", ""))
    name = row_data.get("hubspot_company_name", "")

    if not apps:
        apps = ["Automation workflows", "Connected integrations"]

    items_html = "\n".join(f"      <li>{html.escape(a)}</li>" for a in apps[:4])
    return f'<ul class="top-apps-list">\n{items_html}\n    </ul>'


def build_paid_footprint(paid_plans):
    if paid_plans <= 1:
        return ""
    return f"""<div class="kpi-card">
      <div class="kpi-label">Paid Zapier Plans</div>
      <div class="kpi-value">{paid_plans}</div>
      <div class="kpi-sub">active paid accounts</div>
      <div class="kpi-change neutral">🔗 consolidation opportunity</div>
    </div>"""


def build_ai_panel(ai_tools_connected, ai_usage_total, row_data):
    if ai_tools_connected == 0:
        vertical = row_data.get("hubspot_vertical", "")
        industry = row_data.get("hubspot_industry", "")
        app1 = vertical if vertical and vertical not in ("-", "—", "N/A", "", "null", "None") else "your current tools"
        app2 = industry if industry and industry not in ("-", "—", "N/A", "", "null", "None") else "existing workflows"
        return f"""
      <div class="ai-stat-grid">
        <div class="ai-stat-box"><div class="num">0</div><div class="lbl">AI tools connected</div></div>
        <div class="ai-stat-box"><div class="num">—</div><div class="lbl">interactions (30d)</div></div>
      </div>
      <div class="ai-tools-list" style="margin-top:14px; color:#92400E; background:#FFFBEB; padding:12px; border-radius:8px;">
        Your team's automation could be enhanced with AI-powered workflows — a quick way to save time on repetitive tasks.
      </div>"""

    users_now = safe_int(row_data.get("users_jan2026"), 1)
    ai_per_user = round(ai_usage_total / users_now) if users_now > 0 else 0
    return f"""
      <div class="ai-stat-grid">
        <div class="ai-stat-box"><div class="num">{ai_tools_connected}</div><div class="lbl">AI tools connected</div></div>
        <div class="ai-stat-box"><div class="num">{fmt_num(ai_usage_total)}</div><div class="lbl">interactions (30d)</div></div>
      </div>
      <div class="ai-stat-grid">
        <div class="ai-stat-box"><div class="num">{ai_per_user}</div><div class="lbl">AI interactions / user</div></div>
        <div class="ai-stat-box"><div class="num">—</div><div class="lbl">&nbsp;</div></div>
      </div>"""


def build_insight_callout(adoption_pct, employees_not_on):
    if adoption_pct < 50 and employees_not_on > 0:
        return f"""<div class="insight-callout">
    <strong>💡 Opportunity:</strong> With {fmt_num(employees_not_on)} employees not yet on Zapier, there's significant room to expand automation impact across the organization.
  </div>"""
    return ""


def generate_report(row_data):
    company_name = row_data.get("hubspot_company_name", "Unknown Company")
    domain_raw = row_data.get("hubspot_company_domain", "unknown.com")
    domain = sanitize_domain(domain_raw)

    users_jan = safe_int(row_data.get("users_jan2025"))
    users_now = safe_int(row_data.get("users_jan2026"))
    user_growth_pct = safe_float(row_data.get("user_growth_pct"))
    task_growth_pct = safe_float(row_data.get("task_growth_pct"))
    total_90d = safe_int(row_data.get("total_billable_tasks_last_90d"))
    employees = safe_int(row_data.get("company_number_of_employees"), 1)
    ai_tools = safe_int(row_data.get("number_of_ai_tools_connected"))
    ai_usage = safe_int(row_data.get("sum_of_ai_tools_total_usage"))
    paid_plans = safe_int(row_data.get("number_of_associated_paid_zapier_account"))

    adoption_pct = round(users_now / employees * 100, 1) if employees > 0 else 0
    employees_not = max(employees - users_now, 0)
    adoption_pct_round = f"{int(round(adoption_pct))}%"
    ai_per_user = round(ai_usage / users_now) if users_now > 0 else 0
    ai_usage_raw = ai_usage if ai_usage > 0 else 0

    accent = accent_for_domain(domain)
    tier = tier_label(employees)
    profile = classify_profile(row_data)

    as_of = row_data.get("usage_rollups_as_of_date", "")
    if as_of and as_of not in ("-", "—", "N/A", "", "null", "None"):
        try:
            for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%Y%m%d"):
                try:
                    dt = datetime.strptime(str(as_of).strip(), fmt)
                    as_of = dt.strftime("%B %Y")
                    break
                except ValueError:
                    continue
            else:
                as_of = str(as_of)
        except Exception:
            as_of = str(as_of)
    else:
        as_of = datetime.now().strftime("%B %Y")

    sub_html = narrative_subtitle(profile, company_name)
    second_card = build_second_card(task_growth_pct, total_90d)
    top_apps = build_top_apps_card(row_data)
    paid_foot = build_paid_footprint(paid_plans)
    ai_panel = build_ai_panel(ai_tools, ai_usage, row_data)
    insight = build_insight_callout(adoption_pct, employees_not)

    template = get_template()

    replacements = {
        "{{COMPANY_NAME}}": html.escape(company_name),
        "{{DOMAIN}}": html.escape(domain),
        "{{USERS_JAN}}": str(users_jan),
        "{{USERS_NOW}}": str(users_now),
        "{{USER_GROWTH_PCT}}": f"{user_growth_pct:.1f}",
        "{{ADOPTION_PCT}}": f"{adoption_pct:.1f}",
        "{{ADOPTION_PCT_ROUND}}": adoption_pct_round,
        "{{EMPLOYEES}}": fmt_num(employees),
        "{{EMPLOYEES_NOT_ON_ZAPIER}}": fmt_num(employees_not),
        "{{AS_OF_DATE}}": html.escape(as_of),
        "{{ROW1_SECOND_CARD_INNER_HTML}}": second_card,
        "{{TOP_APPS_CARD_INNER_HTML}}": top_apps,
        "{{PAID_FOOTPRINT_CARD_HTML}}": paid_foot,
        "{{AI_DETAIL_PANEL_HTML}}": ai_panel,
        "{{AI_USAGE}}": fmt_num(ai_usage),
        "{{AI_PER_USER}}": str(ai_per_user),
        "{{AI_USAGE_RAW}}": str(ai_usage_raw),
        "{{ACCENT_COLOR}}": accent,
        "{{NARRATIVE_SUBTITLE}}": sub_html,
        "{{TIER_LABEL}}": tier,
        "{{INSIGHT_CALLOUT_HTML}}": insight,
        "{{TOTAL_TASKS_90D}}": fmt_num(total_90d),
        "{{TASK_GROWTH_PCT}}": f"{task_growth_pct:.1f}",
    }

    out = template
    for placeholder, value in replacements.items():
        out = out.replace(placeholder, value)

    filename = re.sub(r'[^a-zA-Z0-9._-]', '-', domain) + "-report.html"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filepath = OUTPUT_DIR / filename
    filepath.write_text(out, encoding="utf-8")

    suppressions = []
    if task_growth_pct < 5:
        suppressions.append(f"task growth % hidden ({task_growth_pct:.1f}% < 5% threshold) — showing 90d volume instead")
    if paid_plans <= 1:
        suppressions.append("multi-plan / consolidation suppressed (single plan)")

    return {
        "filepath": str(filepath),
        "company_name": company_name,
        "domain": domain,
        "tier": tier,
        "profile": profile,
        "users_now": users_now,
        "users_jan": users_jan,
        "user_growth_pct": user_growth_pct,
        "adoption_pct": adoption_pct,
        "employees": employees,
        "ai_tools": ai_tools,
        "ai_usage": ai_usage,
        "task_growth_pct": task_growth_pct,
        "total_90d": total_90d,
        "paid_plans": paid_plans,
        "suppressions": suppressions,
    }


def get_template():
    return """<!DOCTYPE html>
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
  .header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
  .header-left { display: flex; align-items: center; gap: 16px; }
  .zapier-logo { width: 36px; height: 36px; }
  .header h1 { font-size: 22px; font-weight: 700; color: #0F172A; }
  .header .domain { font-size: 13px; color: #64748B; font-weight: 500; }
  .header .date { font-size: 12px; color: #94A3B8; }
  .narrative-subtitle { font-size: 14px; color: #475569; margin-bottom: 20px; font-style: italic; padding-left: 52px; }
  .impact-banner { background: linear-gradient(135deg, {{ACCENT_COLOR}}11 0%, {{ACCENT_COLOR}}05 100%); border: 1px solid {{ACCENT_COLOR}}33; border-radius: 12px; padding: 20px 24px; margin-bottom: 24px; display: flex; align-items: center; gap: 16px; }
  .impact-dot { width: 48px; height: 48px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: 800; color: white; flex-shrink: 0; }
  .impact-text h2 { font-size: 16px; font-weight: 700; color: #0F172A; }
  .impact-text p { font-size: 13px; color: #475569; margin-top: 2px; }
  .insight-callout { background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 10px; padding: 14px 18px; margin-bottom: 24px; font-size: 13px; color: #92400E; }
  .insight-callout strong { font-weight: 600; }
  .kpi-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 16px; margin-bottom: 28px; }
  .kpi-card { background: white; border-radius: 12px; padding: 20px; border: 1px solid #E2E8F0; transition: box-shadow 0.2s; }
  .kpi-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.06); }
  .kpi-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: #94A3B8; font-weight: 600; margin-bottom: 8px; }
  .kpi-value { font-size: 28px; font-weight: 800; color: #0F172A; }
  .kpi-sub { font-size: 12px; color: #64748B; margin-top: 4px; }
  .kpi-change { display: inline-flex; align-items: center; gap: 4px; font-size: 12px; font-weight: 600; margin-top: 6px; padding: 2px 8px; border-radius: 9999px; }
  .kpi-change.up { background: #DCFCE7; color: #166534; }
  .kpi-change.neutral { background: #F1F5F9; color: #475569; }
  .section { background: white; border-radius: 12px; padding: 24px; border: 1px solid #E2E8F0; margin-bottom: 20px; }
  .section-title { font-size: 15px; font-weight: 700; color: #0F172A; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }
  .section-title .icon { font-size: 18px; }
  .chart-container { position: relative; height: 200px; margin: 16px 0; }
  canvas { width: 100% !important; max-height: 200px; }
  .adoption-bar-wrap { margin: 16px 0; }
  .adoption-bar-bg { height: 32px; background: #F1F5F9; border-radius: 16px; overflow: hidden; position: relative; }
  .adoption-bar-fill { height: 100%; border-radius: 16px; transition: width 0.8s ease; }
  .adoption-big { font-size: 36px; font-weight: 800; color: #0F172A; text-align: center; margin-top: 12px; }
  .adoption-big-label { font-size: 13px; color: #64748B; text-align: center; }
  .ai-stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 12px; }
  .ai-stat-box { background: #F8FAFC; border-radius: 10px; padding: 14px; text-align: center; }
  .ai-stat-box .num { font-size: 24px; font-weight: 800; color: #0F172A; }
  .ai-stat-box .lbl { font-size: 11px; color: #64748B; margin-top: 2px; }
  .ai-tools-list { margin-top: 12px; font-size: 13px; color: #475569; }
  .top-apps-list { list-style: none; padding: 0; }
  .top-apps-list li { padding: 6px 0; font-size: 14px; color: #334155; display: flex; align-items: center; gap: 8px; }
  .top-apps-list li::before { content: "⚡"; font-size: 14px; }
  .footer { text-align: center; padding: 24px 0 8px; font-size: 11px; color: #94A3B8; }
  .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
  @media (max-width: 700px) { .two-col { grid-template-columns: 1fr; } }
  @media print { body { background: white; } .container { padding: 16px; } .kpi-card:hover { box-shadow: none; } }
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div class="header-left">
      <svg class="zapier-logo" viewBox="0 0 36 36" fill="none"><circle cx="18" cy="18" r="18" fill="#FF4A00"/><path d="M25.5 18L20.12 13.5V16.5H10.5V19.5H20.12V22.5L25.5 18Z" fill="white"/></svg>
      <div>
        <h1>{{COMPANY_NAME}}</h1>
        <span class="domain">{{DOMAIN}} &middot; {{TIER_LABEL}}</span>
      </div>
    </div>
    <span class="date">{{AS_OF_DATE}}</span>
  </div>
  {{NARRATIVE_SUBTITLE}}
  <div class="impact-banner">
    <div class="impact-dot" id="adoptionDot">{{ADOPTION_PCT_ROUND}}</div>
    <div class="impact-text">
      <h2>{{ADOPTION_PCT}}% Zapier adoption across the org</h2>
      <p>{{USERS_NOW}} active users out of {{EMPLOYEES}} employees</p>
    </div>
  </div>
  {{INSIGHT_CALLOUT_HTML}}
  <div class="kpi-row">
    <div class="kpi-card">
      <div class="kpi-label">Active Users</div>
      <div class="kpi-value">{{USERS_NOW}}</div>
      <div class="kpi-sub">from {{USERS_JAN}} in Jan 2025</div>
      <div class="kpi-change up">&uarr; {{USER_GROWTH_PCT}}% growth</div>
    </div>
    <div class="kpi-card">
      {{ROW1_SECOND_CARD_INNER_HTML}}
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Top Apps</div>
      {{TOP_APPS_CARD_INNER_HTML}}
    </div>
    {{PAID_FOOTPRINT_CARD_HTML}}
  </div>
  <div class="two-col">
    <div class="section">
      <div class="section-title"><span class="icon">📈</span> User Growth</div>
      <div class="chart-container"><canvas id="userChart"></canvas></div>
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
  <div class="two-col">
    <div class="section">
      <div class="section-title"><span class="icon">🤖</span> AI Tool Usage (30 days)</div>
      <div class="chart-container"><canvas id="aiChart"></canvas></div>
    </div>
    <div class="section">
      <div class="section-title"><span class="icon">✨</span> AI &amp; Automation</div>
      {{AI_DETAIL_PANEL_HTML}}
    </div>
  </div>
  <div class="footer">Powered by Zapier &middot; {{DOMAIN}} &middot; Generated {{AS_OF_DATE}}</div>
</div>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<script>
(function(){
  var pct={{ADOPTION_PCT}};
  var dot=document.getElementById('adoptionDot');
  function ac(p){if(p<=10)return'#DC2626';if(p<=25)return'#F97316';if(p<=50)return'#EAB308';if(p<=75)return'#84CC16';return'#16A34A';}
  dot.style.background=ac(pct);
})();
(function(){
  var ctx=document.getElementById('userChart');if(!ctx)return;
  new Chart(ctx,{type:'bar',data:{labels:['Jan 2025','Current'],datasets:[{label:'Active Users',data:[{{USERS_JAN}},{{USERS_NOW}}],backgroundColor:['#CBD5E1','{{ACCENT_COLOR}}'],borderRadius:8,barThickness:48}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{y:{beginAtZero:true,grid:{color:'#F1F5F9'}},x:{grid:{display:false}}}}});
})();
(function(){
  var ctx=document.getElementById('aiChart');if(!ctx)return;
  var raw={{AI_USAGE_RAW}};
  new Chart(ctx,{type:'bar',data:{labels:['AI Tool Interactions (30d)'],datasets:[{label:'AI Usage',data:[raw],backgroundColor:['#7C3AED'],borderRadius:8,barThickness:48}]},options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{beginAtZero:true,grid:{color:'#F1F5F9'}},y:{grid:{display:false}}}}});
})();
</script>
</body>
</html>"""


def parse_row(raw_values):
    """Parse a list of raw string values into a dict keyed by COLUMN_NAMES."""
    row = {}
    for i, col in enumerate(COLUMN_NAMES):
        if i < len(raw_values):
            row[col] = raw_values[i].strip() if raw_values[i] else ""
        else:
            row[col] = ""
    return row


def print_summary(result):
    profile = result["profile"]
    adoption = result["adoption_pct"]
    if adoption <= 25:
        signal = "🔴"
    elif adoption <= 50:
        signal = "🟡"
    else:
        signal = "🟢"

    print(f"\n📊 {result['company_name']} · {result['tier']} · {result['domain']} · [{profile}]")

    lines = {
        "AI_LEAD": f"   AI adoption ({result['ai_tools']} tools, {fmt_num(result['ai_usage'])} interactions) + {result['users_now']} active users",
        "MULTI_PLAN": f"   {result['paid_plans']} paid plans — consolidation opportunity + {result['users_now']} active users",
        "ADOPTION_LEAD": f"   {fmt_num(result['employees'] - result['users_now'])} employees not yet on Zapier — adoption runway",
        "GROWTH": f"   {result['user_growth_pct']:.1f}% user growth — strong expansion momentum",
        "STANDARD": f"   {result['users_now']} active users across {fmt_num(result['employees'])} employees",
    }
    print(lines.get(profile, ""))
    print(f"   👥 Users: {result['users_now']} (from {result['users_jan']}, +{result['user_growth_pct']:.1f}%)")
    print(f"   {signal} Adoption: {adoption:.1f}%")

    if result["suppressions"]:
        print(f"   Customer PDF excludes: {'; '.join(result['suppressions'])}")

    print(f"   📁 Saved: {result['filepath']}")


def process_csv_string(csv_text):
    """Process a multi-line CSV string (rows of comma-separated values)."""
    results = []
    reader = csv.reader(io.StringIO(csv_text))
    for row_values in reader:
        if not row_values or all(v.strip() == "" for v in row_values):
            continue
        row_data = parse_row(row_values)
        if not row_data.get("hubspot_company_domain") or row_data["hubspot_company_domain"] in ("", "-", "N/A"):
            print(f"⚠ Skipping row — missing domain: {row_values[:2]}")
            continue
        result = generate_report(row_data)
        results.append(result)
        print_summary(result)
    return results


def main():
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
        with open(csv_path, "r", encoding="utf-8") as f:
            csv_text = f.read()
    else:
        print("MMPE Account Report Generator")
        print("=" * 50)
        print("Paste rows (one per line, comma-separated values matching the MMPE column order).")
        print("Press Ctrl+D (Unix) or Ctrl+Z (Windows) when done.\n")
        csv_text = sys.stdin.read()

    results = process_csv_string(csv_text)
    print(f"\n✅ Generated {len(results)} report(s) in {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
