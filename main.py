import streamlit as st
import requests
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime, timezone
from collections import Counter

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GitHub Maintainer Dashboard",
    page_icon="🐙",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Zerve Design System ───────────────────────────────────────────────────────
BG        = "#1D1D20"
TEXT_PRI  = "#fbfbff"
TEXT_SEC  = "#909094"
ACCENT    = "#ffd400"
SUCCESS   = "#17b26a"
WARN      = "#f04438"
COLORS    = ["#A1C9F4", "#FFB482", "#8DE5A1", "#FF9F9B", "#D0BBFF",
             "#1F77B4", "#9467BD", "#8C564B", "#C49C94", "#E377C2"]
GRID_CLR  = "#2e2e33"

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
    html, body, [data-testid="stApp"] {{
        background-color: {BG};
        color: {TEXT_PRI};
    }}
    [data-testid="stSidebar"] {{
        background-color: #141416;
    }}
    [data-testid="stSidebar"] * {{
        color: {TEXT_PRI} !important;
    }}
    .section-header {{
        color: {TEXT_PRI};
        font-size: 18px;
        font-weight: 600;
        margin: 32px 0 16px 0;
        padding-bottom: 8px;
        border-bottom: 1px solid #3a3a40;
    }}
    .rec-section {{
        background: #28282d;
        border-radius: 10px;
        padding: 20px 24px;
        border: 1px solid #3a3a40;
        margin-bottom: 12px;
    }}
    h1, h2, h3, h4 {{
        color: {TEXT_PRI} !important;
    }}
    [data-testid="stDataFrame"] {{
        background: #28282d !important;
    }}
    .stSpinner > div {{ color: {ACCENT} !important; }}
    div[data-testid="metric-container"] {{
        background: #28282d;
        border-radius: 12px;
        padding: 16px;
        border: 1px solid #3a3a40;
    }}
    div[data-testid="metric-container"] label {{
        color: {TEXT_SEC} !important;
        font-size: 13px !important;
    }}
    div[data-testid="metric-container"] [data-testid="stMetricValue"] {{
        color: {TEXT_PRI} !important;
        font-size: 28px !important;
        font-weight: 700 !important;
    }}
    .stButton > button {{
        background: #28282d;
        color: {TEXT_PRI};
        border: 1px solid #3a3a40;
        border-radius: 8px;
        width: 100%;
    }}
    .stButton > button:hover {{
        border-color: {ACCENT};
        color: {ACCENT};
    }}
    .stTextInput input {{
        background: #28282d !important;
        color: {TEXT_PRI} !important;
        border: 1px solid #3a3a40 !important;
    }}
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
DEFAULT_REPO = "facebook/react"
PER_PAGE     = 100
MAX_PAGES    = 5
STALE_DAYS   = 30

GH_HEADERS = {
    "Accept":               "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


# ── GitHub fetch helpers ──────────────────────────────────────────────────────
def gh_fetch_all(base_url: str, endpoint: str, params: dict) -> list:
    """Paginate through GitHub REST API, up to MAX_PAGES × PER_PAGE items."""
    results = []
    for page in range(1, MAX_PAGES + 1):
        params["page"] = page
        r = requests.get(
            f"{base_url}/{endpoint}", headers=GH_HEADERS, params=params, timeout=20
        )
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        results.extend(batch)
        if len(batch) < PER_PAGE:
            break
    return results


def parse_gh_item(item: dict) -> dict:
    is_pr = "pull_request" in item
    return {
        "id":         item["number"],
        "title":      item["title"],
        "state":      item["state"],
        "type":       "pr" if is_pr else "issue",
        "labels":     [l["name"] for l in item.get("labels", [])],
        "assignees":  [a["login"] for a in item.get("assignees", [])],
        "created_at": pd.to_datetime(item["created_at"]),
        "closed_at":  pd.to_datetime(item["closed_at"]) if item.get("closed_at") else pd.NaT,
        "merged_at":  pd.to_datetime(item["pull_request"]["merged_at"])
                      if is_pr and item["pull_request"].get("merged_at") else pd.NaT,
        "comments":   item.get("comments", 0),
        "author":     item["user"]["login"] if item.get("user") else None,
    }


@st.cache_data(ttl=300, show_spinner=False)
def load_repo_data(repo: str) -> dict:
    """Fetch & compute all analytics for `repo`. Cached for 5 minutes."""
    base_url = f"https://api.github.com/repos/{repo}"
    raw = gh_fetch_all(base_url, "issues",
                       {"state": "all", "per_page": PER_PAGE,
                        "sort": "created", "direction": "desc"})

    rows = [parse_gh_item(i) for i in raw]
    df = pd.DataFrame(rows)
    for col in ["created_at", "closed_at", "merged_at"]:
        df[col] = pd.to_datetime(df[col], utc=True)

    issues_df = df[df["type"] == "issue"].copy().reset_index(drop=True)
    prs_df    = df[df["type"] == "pr"].copy().reset_index(drop=True)
    now       = datetime.now(timezone.utc)

    # ── KPIs ──────────────────────────────────────────────────────────────────
    open_issues_df   = issues_df[issues_df["state"] == "open"]
    open_issue_count = len(open_issues_df)

    stale_df    = open_issues_df[(now - open_issues_df["created_at"]).dt.days > STALE_DAYS]
    stale_count = len(stale_df)

    closed_iss = issues_df[issues_df["closed_at"].notna()]
    avg_close  = round(
        ((closed_iss["closed_at"] - closed_iss["created_at"]).dt.total_seconds() / 86400).mean(), 2
    ) if len(closed_iss) else 0.0

    merged_prs_df = prs_df[prs_df["merged_at"].notna()]
    avg_merge     = round(
        ((merged_prs_df["merged_at"] - merged_prs_df["created_at"]).dt.total_seconds() / 86400).mean(), 2
    ) if len(merged_prs_df) else 0.0

    # Open PR count (unmerged + open state)
    open_prs = prs_df[(prs_df["state"] == "open") & prs_df["merged_at"].isna()].copy()
    open_pr_count = len(open_prs)
    open_prs["age_days"] = (now - open_prs["created_at"]).dt.days

    # PRs waiting longest (top 10)
    prs_longest = (
        open_prs[["id", "title", "age_days", "comments", "assignees"]]
        .sort_values("age_days", ascending=False)
        .head(10)
        .reset_index(drop=True)
    )

    # ── Labels & contributors ─────────────────────────────────────────────────
    all_labels   = [l for lbls in issues_df["labels"] for l in lbls]
    top_labels   = dict(Counter(all_labels).most_common(10))

    contr_issues = issues_df["author"].value_counts().to_dict()
    contr_prs    = prs_df["author"].value_counts().to_dict()
    all_authors  = set(contr_issues) | set(contr_prs)
    activity     = {
        a: {"issues": contr_issues.get(a, 0), "prs": contr_prs.get(a, 0),
            "total": contr_issues.get(a, 0) + contr_prs.get(a, 0)}
        for a in all_authors
    }
    top_contributors = dict(
        sorted(activity.items(), key=lambda x: x[1]["total"], reverse=True)[:10]
    )

    return {
        "now":              now,
        "issues_df":        issues_df,
        "prs_df":           prs_df,
        "open_issues_df":   open_issues_df,
        "open_issue_count": open_issue_count,
        "stale_df":         stale_df,
        "stale_count":      stale_count,
        "closed_iss":       closed_iss,
        "avg_close":        avg_close,
        "merged_prs":       merged_prs_df,
        "avg_merge":        avg_merge,
        "open_prs":         open_prs,
        "open_pr_count":    open_pr_count,
        "prs_longest":      prs_longest,
        "top_labels":       top_labels,
        "top_contributors": top_contributors,
        "total_fetched":    len(df),
    }


# ── Chart helpers ─────────────────────────────────────────────────────────────
def apply_dark(ax):
    ax.set_facecolor(BG)
    ax.figure.patch.set_facecolor(BG)
    ax.tick_params(colors=TEXT_PRI, labelsize=10)
    ax.xaxis.label.set_color(TEXT_PRI)
    ax.yaxis.label.set_color(TEXT_PRI)
    ax.title.set_color(TEXT_PRI)
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID_CLR)
    ax.yaxis.grid(True, color=GRID_CLR, linewidth=0.6, linestyle="--", alpha=0.7)
    ax.set_axisbelow(True)


def chart_issue_age(open_issues_df, now):
    """Histogram of open issue ages in days."""
    ages = (now - open_issues_df["created_at"]).dt.total_seconds() / 86400
    fig, ax = plt.subplots(figsize=(7, 4))
    apply_dark(ax)
    bins = min(20, max(5, len(ages)))
    ax.hist(ages, bins=bins, color=COLORS[0], edgecolor=BG, linewidth=0.5, alpha=0.9)
    median_age = ages.median()
    ax.axvline(median_age, color=ACCENT, linewidth=1.8, linestyle="--",
               label=f"Median: {median_age:.1f}d")
    ax.set_xlabel("Age (days)", fontsize=11)
    ax.set_ylabel("Issues", fontsize=11)
    ax.set_title("Open Issue Age Distribution", fontsize=13, fontweight="bold", pad=12)
    ax.legend(facecolor=BG, labelcolor=TEXT_PRI, fontsize=9, framealpha=0.8)
    plt.tight_layout()
    return fig


def chart_pr_merge_time(merged_prs):
    """Histogram of PR merge times, capped at 99th percentile."""
    merge_t = (merged_prs["merged_at"] - merged_prs["created_at"]).dt.total_seconds() / 86400
    cap     = np.percentile(merge_t, 99)
    clipped = merge_t[merge_t <= cap]
    fig, ax = plt.subplots(figsize=(7, 4))
    apply_dark(ax)
    ax.hist(clipped, bins=25, color=COLORS[1], edgecolor=BG, linewidth=0.5, alpha=0.9)
    med = merge_t.median()
    ax.axvline(med, color=ACCENT, linewidth=1.8, linestyle="--", label=f"Median: {med:.2f}d")
    ax.set_xlabel("Merge Time (days)", fontsize=11)
    ax.set_ylabel("PRs", fontsize=11)
    ax.set_title("PR Merge Time Distribution", fontsize=13, fontweight="bold", pad=12)
    ax.legend(facecolor=BG, labelcolor=TEXT_PRI, fontsize=9, framealpha=0.8)
    ax.text(0.97, 0.93, f"99p cap: {cap:.1f}d", transform=ax.transAxes,
            ha="right", va="top", color=TEXT_SEC, fontsize=9)
    plt.tight_layout()
    return fig


def chart_labels(top_labels):
    """Horizontal bar chart of top issue labels."""
    if not top_labels:
        return None
    pairs = sorted(top_labels.items(), key=lambda x: x[1], reverse=True)[:10]
    lbls, cnts = zip(*pairs)
    fig, ax = plt.subplots(figsize=(7, 4))
    apply_dark(ax)
    bars = ax.barh(lbls, cnts,
                   color=[COLORS[i % len(COLORS)] for i in range(len(lbls))],
                   edgecolor=BG, linewidth=0.4, height=0.65)
    for b, v in zip(bars, cnts):
        ax.text(b.get_width() + max(cnts) * 0.01,
                b.get_y() + b.get_height() / 2,
                str(v), va="center", ha="left", color=TEXT_PRI, fontsize=9, fontweight="bold")
    ax.set_xlabel("Issue Count", fontsize=11)
    ax.set_title("Issues by Label", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlim(0, max(cnts) * 1.18)
    ax.invert_yaxis()
    ax.tick_params(axis="y", labelsize=9)
    plt.tight_layout()
    return fig


def chart_contributors(top_contributors):
    """Stacked bar chart of top-10 contributor activity (PRs + Issues)."""
    if not top_contributors:
        return None
    names    = list(top_contributors.keys())
    pr_cnts  = [top_contributors[n]["prs"]    for n in names]
    iss_cnts = [top_contributors[n]["issues"] for n in names]
    totals   = [top_contributors[n]["total"]  for n in names]
    idx      = np.argsort(totals)[::-1]
    names    = [names[i]    for i in idx]
    pr_cnts  = [pr_cnts[i]  for i in idx]
    iss_cnts = [iss_cnts[i] for i in idx]
    totals   = [totals[i]   for i in idx]
    x = np.arange(len(names))
    fig, ax = plt.subplots(figsize=(9, 4))
    apply_dark(ax)
    ax.bar(x, pr_cnts,  width=0.55, color=COLORS[0], label="PRs",    edgecolor=BG, linewidth=0.4)
    ax.bar(x, iss_cnts, width=0.55, bottom=pr_cnts, color=COLORS[2], label="Issues", edgecolor=BG, linewidth=0.4)
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=35, ha="right", fontsize=9)
    ax.set_ylabel("Contributions", fontsize=11)
    ax.set_title("Top 10 Contributor Activity", fontsize=13, fontweight="bold", pad=12)
    ax.legend(facecolor=BG, labelcolor=TEXT_PRI, fontsize=9, framealpha=0.8)
    for i, (p, iss) in enumerate(zip(pr_cnts, iss_cnts)):
        ax.text(i, p + iss + max(totals) * 0.01, str(p + iss),
                ha="center", va="bottom", color=TEXT_PRI, fontsize=8, fontweight="bold")
    plt.tight_layout()
    return fig


# ── AI Recommendations ────────────────────────────────────────────────────────
def build_ai_summary(data: dict, repo: str) -> str:
    """
    Generates a structured maintainer recommendations report.
    Tries the OpenAI-compatible Zerve GenAI endpoint first;
    falls back to a rich heuristic summary if unavailable.
    """
    # Attempt Zerve GenAI endpoint (OpenAI-compatible)
    zerve_endpoint = "https://api.zerve.ai/v1"
    context_lines = [
        f"Repository: {repo}",
        f"Open issues: {data['open_issue_count']}",
        f"Stale issues (>{STALE_DAYS}d without close): {data['stale_count']}",
        f"Average issue close time: {data['avg_close']} days",
        f"Average PR merge time: {data['avg_merge']} days",
        f"Open unmerged PRs: {data['open_pr_count']}",
        f"Total items analysed: {data['total_fetched']}",
        f"Top labels: {', '.join([f'{k}({v})' for k,v in list(data['top_labels'].items())[:5]])}",
        f"Top contributors: {', '.join(list(data['top_contributors'].keys())[:5])}",
    ]
    if not data['prs_longest'].empty:
        oldest_pr = data['prs_longest'].iloc[0]
        context_lines.append(f"Oldest open PR: #{int(oldest_pr['id'])} waiting {int(oldest_pr['age_days'])} days")

    prompt = (
        "You are a GitHub repository maintainer advisor. "
        "Based on the following repository analytics, provide a concise, structured report with:\n"
        "1. Top 3 bottlenecks for the team\n"
        "2. Highest-priority cleanup actions (with specific numbers)\n"
        "3. 5 actionable recommendations\n"
        "4. Positive signals to celebrate\n\n"
        "Use markdown with clear headers and bullet points. Be specific, data-driven, and direct.\n\n"
        "Analytics:\n" + "\n".join(context_lines)
    )

    ai_response = None
    try:
        resp = requests.post(
            f"{zerve_endpoint}/chat/completions",
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 800,
                "temperature": 0.4,
            },
            timeout=10,
        )
        if resp.status_code == 200:
            ai_response = resp.json()["choices"][0]["message"]["content"]
    except Exception:
        pass  # Fall through to heuristic summary

    if ai_response:
        return ai_response

    # ── Heuristic fallback ────────────────────────────────────────────────────
    top5_prs    = data["prs_longest"].head(5)
    top5_labels = list(data["top_labels"].items())[:5]
    stale_pct   = round(data["stale_count"] / data["open_issue_count"] * 100, 1) if data["open_issue_count"] else 0
    health_score = 100
    health_issues = []

    if stale_pct > 40:
        health_score -= 25
        health_issues.append(f"High stale rate ({stale_pct}%)")
    if data["avg_close"] > 14:
        health_score -= 20
        health_issues.append(f"Slow issue resolution ({data['avg_close']}d avg)")
    if data["avg_merge"] > 7:
        health_score -= 15
        health_issues.append(f"Slow PR merges ({data['avg_merge']}d avg)")
    if data["open_pr_count"] > 50:
        health_score -= 15
        health_issues.append(f"Large PR backlog ({data['open_pr_count']} open)")

    health_emoji = "🟢" if health_score >= 80 else ("🟡" if health_score >= 60 else "🔴")

    lines = []
    lines.append(f"### {health_emoji} Repository Health Score: {max(0, health_score)}/100\n")
    if health_issues:
        lines.append("**Areas of concern:** " + " · ".join(health_issues) + "\n")

    lines.append("## 🔴 Top Bottlenecks\n")
    lines.append(f"1. **Stale Issue Backlog** — {data['stale_count']} issues ({stale_pct}% of open) have been "
                 f"open for >{STALE_DAYS} days with no closure. This signals triage debt accumulating.")
    lines.append(f"2. **Open PR Queue** — {data['open_pr_count']} PRs are waiting to be reviewed and merged. "
                 f"Review throughput is a likely bottleneck.")
    if data["avg_close"] > 7:
        lines.append(f"3. **Slow Issue Resolution** — avg close time of {data['avg_close']}d exceeds the "
                     f"7-day healthy threshold, indicating labelling or assignment gaps.")
    elif data["avg_merge"] > 5:
        lines.append(f"3. **PR Review Latency** — avg merge time of {data['avg_merge']}d suggests reviewers "
                     f"are stretched. Consider a dedicated review rotation.")

    lines.append("\n## 🧹 Highest-Priority Actions\n")
    lines.append(f"1. **Triage {data['stale_count']} stale issues** — label, assign, or close each one. "
                 f"Even a partial triage sprint of 1 hour can clear the backlog significantly.")
    if not top5_prs.empty:
        oldest = top5_prs.iloc[0]
        lines.append(f"2. **Review PR #{int(oldest['id'])}** — it has waited **{int(oldest['age_days'])} days** "
                     f"and has {int(oldest['comments'])} comments. Start with the oldest-waiting PRs.")
    if top5_labels:
        top_lbl, top_cnt = top5_labels[0]
        lines.append(f"3. **Address '{top_lbl}' label** — {top_cnt} issues share this label. "
                     f"A focused effort here could dramatically reduce open issue count.")

    lines.append("\n## ✅ Actionable Recommendations\n")
    lines.append(f"1. **Weekly Triage Session** — 30-min slot to label + assign new issues prevents backlog growth.")
    lines.append(f"2. **PR Review Rotation** — assign 2 reviewers per week to clear the oldest "
                 f"{min(5, data['open_pr_count'])} PRs in the queue.")
    lines.append(f"3. **Close-Time SLA** — target <{max(3, int(data['avg_close']))}d issue close time "
                 f"(currently {data['avg_close']}d) as a sprint OKR.")
    lines.append(f"4. **Contributor Onboarding** — top contributors are highly active; ensure they "
                 f"have write access and a clear contribution guide to retain momentum.")
    lines.append(f"5. **Label Cleanup Sprint** — audit top labels ('{top5_labels[0][0] if top5_labels else 'N/A'}', etc.) "
                 f"for consistency. Standardised labels enable faster routing.")

    lines.append("\n## 🟢 Positive Signals\n")
    if data["avg_merge"] <= 3:
        lines.append(f"✅ **Lightning-fast PR merges** — avg {data['avg_merge']}d is world-class. "
                     f"The team is highly responsive to contributions.")
    if data["avg_merge"] <= 7:
        lines.append(f"✅ **Healthy PR velocity** — avg merge time of {data['avg_merge']}d is well within a healthy range.")
    lines.append(f"✅ **Strong community engagement** — {data['total_fetched']} issues + PRs analysed, "
                 f"with {len(data['top_contributors'])} distinct contributors actively participating.")
    if len(data["top_contributors"]) >= 5:
        lines.append(f"✅ **Diverse contributor base** — {len(data['top_contributors'])} top contributors "
                     f"reduce bus-factor risk and ensure project resilience.")

    return "\n".join(lines)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🐙 GitHub Maintainer")
    st.markdown("---")
    repo_input = st.text_input(
        "Repository (owner/repo)",
        value=DEFAULT_REPO,
        placeholder="e.g. facebook/react",
        help="Enter any public GitHub repository in owner/repo format",
    )
    refresh_btn = st.button("🔄 Fetch / Refresh", use_container_width=True)
    st.markdown("---")
    st.markdown(
        f"<span style='color:{TEXT_SEC}; font-size:12px;'>📦 Fetches up to "
        f"{MAX_PAGES * PER_PAGE} recent items</span>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<span style='color:{TEXT_SEC}; font-size:12px;'>⏳ Stale threshold: "
        f"{STALE_DAYS} days</span>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<span style='color:{TEXT_SEC}; font-size:12px;'>🔒 Cache TTL: 5 minutes</span>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<span style='color:{TEXT_SEC}; font-size:12px;'>🔑 No auth token needed for public repos</span>",
        unsafe_allow_html=True,
    )

# ── Clear cache on refresh ────────────────────────────────────────────────────
if refresh_btn:
    st.cache_data.clear()

# ── Header ────────────────────────────────────────────────────────────────────
repo = (repo_input or DEFAULT_REPO).strip().strip("/")

st.markdown(
    "<h1 style='margin-bottom:4px;'>🐙 GitHub Developer Analytics</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    f"<p style='color:{TEXT_SEC}; margin-bottom:24px; font-size:15px;'>"
    f"Analysing <b style='color:{ACCENT};'>{repo}</b> · "
    f"<a href='https://github.com/{repo}' target='_blank' "
    f"style='color:{COLORS[0]}; text-decoration:none;'>View on GitHub ↗</a></p>",
    unsafe_allow_html=True,
)

# ── Load data ─────────────────────────────────────────────────────────────────
with st.spinner(f"⬇  Fetching data from GitHub for **{repo}**…"):
    data = load_repo_data(repo)

# ── KPI Row (5 metrics) ───────────────────────────────────────────────────────
st.markdown("<div class='section-header'>📊 Key Metrics</div>", unsafe_allow_html=True)

k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    st.metric(
        label="🐛 Open Issues",
        value=data["open_issue_count"],
    )
with k2:
    stale_pct_label = (
        f"{round(data['stale_count'] / data['open_issue_count'] * 100, 1)}% of open"
        if data["open_issue_count"] else None
    )
    st.metric(
        label="⏳ Stale Issues (>30d)",
        value=data["stale_count"],
        delta=stale_pct_label,
        delta_color="inverse",
    )
with k3:
    st.metric(
        label="⏱ Avg Issue Close",
        value=f"{data['avg_close']}d",
        delta="days avg" if data["avg_close"] else None,
        delta_color="off",
    )
with k4:
    st.metric(
        label="🔀 Avg PR Merge",
        value=f"{data['avg_merge']}d",
        delta="days avg" if data["avg_merge"] else None,
        delta_color="off",
    )
with k5:
    st.metric(
        label="🔁 Open PRs",
        value=data["open_pr_count"],
        delta=f"awaiting review" if data["open_pr_count"] else None,
        delta_color="off",
    )

# ── Analytics Charts (2 × 2 grid) ────────────────────────────────────────────
st.markdown("<div class='section-header'>📈 Analytics Charts</div>", unsafe_allow_html=True)

col_a, col_b = st.columns(2)

with col_a:
    if len(data["open_issues_df"]) > 0:
        fig_age = chart_issue_age(data["open_issues_df"], data["now"])
        st.pyplot(fig_age, use_container_width=True)
        plt.close(fig_age)
    else:
        st.info("No open issues to display.")

with col_b:
    if len(data["merged_prs"]) > 0:
        fig_merge = chart_pr_merge_time(data["merged_prs"])
        st.pyplot(fig_merge, use_container_width=True)
        plt.close(fig_merge)
    else:
        st.info("No merged PRs to display.")

col_c, col_d = st.columns(2)

with col_c:
    if data["top_labels"]:
        fig_labels = chart_labels(data["top_labels"])
        if fig_labels:
            st.pyplot(fig_labels, use_container_width=True)
            plt.close(fig_labels)
    else:
        st.info("No labels found.")

with col_d:
    if data["top_contributors"]:
        fig_contribs = chart_contributors(data["top_contributors"])
        if fig_contribs:
            st.pyplot(fig_contribs, use_container_width=True)
            plt.close(fig_contribs)
    else:
        st.info("No contributor data available.")

# ── PRs Waiting Longest — sortable dataframe ──────────────────────────────────
st.markdown(
    "<div class='section-header'>⏳ Pull Requests Waiting Longest</div>",
    unsafe_allow_html=True,
)

prs_table = data["prs_longest"].copy()

if len(prs_table) == 0:
    st.info("No open PRs found.")
else:
    # Build display DataFrame with a clickable GitHub URL column
    prs_table["github_url"] = prs_table["id"].apply(
        lambda pr_id: f"https://github.com/{repo}/pull/{int(pr_id)}"
    )
    prs_table["assignees_str"] = prs_table["assignees"].apply(
        lambda a: ", ".join(a) if a else "Unassigned"
    )
    prs_display = prs_table[["id", "title", "age_days", "comments", "assignees_str", "github_url"]].copy()
    prs_display.columns = ["PR #", "Title", "Days Open", "💬 Comments", "Assignees", "GitHub Link"]

    st.dataframe(
        prs_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "PR #": st.column_config.NumberColumn("PR #", width="small"),
            "Title": st.column_config.TextColumn("Title", width="large"),
            "Days Open": st.column_config.NumberColumn(
                "Days Open", width="small", help="Days since the PR was opened"
            ),
            "💬 Comments": st.column_config.NumberColumn("💬 Comments", width="small"),
            "Assignees": st.column_config.TextColumn("Assignees", width="medium"),
            "GitHub Link": st.column_config.LinkColumn(
                "GitHub Link", display_text="Open ↗", width="small"
            ),
        },
    )

# ── AI Maintainer Recommendations ─────────────────────────────────────────────
st.markdown(
    "<div class='section-header'>🤖 AI Maintainer Recommendations</div>",
    unsafe_allow_html=True,
)

with st.spinner("🧠 Generating recommendations…"):
    ai_summary = build_ai_summary(data, repo)

st.markdown(
    f"<div class='rec-section'>{ai_summary}</div>",
    unsafe_allow_html=True,
)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    st.markdown(
        f"<span style='color:{TEXT_SEC}; font-size:12px;'>📦 Total items fetched: "
        f"<b style='color:{TEXT_PRI};'>{data['total_fetched']}</b></span>",
        unsafe_allow_html=True,
    )
with col_f2:
    st.markdown(
        f"<span style='color:{TEXT_SEC}; font-size:12px;'>🕐 Last updated: "
        f"<b style='color:{TEXT_PRI};'>{data['now'].strftime('%Y-%m-%d %H:%M UTC')}</b></span>",
        unsafe_allow_html=True,
    )
with col_f3:
    st.markdown(
        f"<span style='color:{TEXT_SEC}; font-size:12px;'>⚡ Powered by "
        f"<b style='color:{ACCENT};'>Zerve</b></span>",
        unsafe_allow_html=True,
    )
