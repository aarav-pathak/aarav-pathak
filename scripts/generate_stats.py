import json
import os
import subprocess
import urllib.request
from collections import defaultdict

def fetch_github_stats(username="aarav-pathak"):
    query = """
    query {
      user(login: "%s") {
        name
        login
        createdAt
        pullRequests { totalCount }
        mergedPRs: pullRequests(states: MERGED) { totalCount }
        openPRs: pullRequests(states: OPEN) { totalCount }
        repositories(ownerAffiliations: OWNER, first: 100) {
          totalCount
          nodes {
            stargazerCount
            forkCount
            isFork
            languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
              edges {
                size
                node { name color }
              }
            }
          }
        }
        contributionsCollection {
          totalCommitContributions
          totalIssueContributions
          totalPullRequestContributions
          totalPullRequestReviewContributions
          contributionCalendar {
            totalContributions
          }
        }
      }
    }
    """ % username

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        try:
            req = urllib.request.Request(
                "https://api.github.com/graphql",
                data=json.dumps({"query": query}).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {token}",
                    "User-Agent": "profile-stats-generator",
                    "Content-Type": "application/json"
                }
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())["data"]["user"]
                return data
        except Exception as e:
            print(f"Error fetching GitHub via urllib with token: {e}")

    try:
        res = subprocess.check_output(["gh", "api", "graphql", "-f", f"query={query}"], text=True)
        return json.loads(res)["data"]["user"]
    except Exception as e:
        print(f"Error fetching GitHub via gh CLI: {e}")
        return None

def fetch_codeforces_stats(handle="orthodoxcoder"):
    rating = 764
    max_rating = 960
    rank = "newbie"
    solved = 177

    try:
        url = f"https://codeforces.com/api/user.info?handles={handle}"
        req = urllib.request.Request(url, headers={"User-Agent": "profile-stats-generator"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            if data.get("status") == "OK" and data.get("result"):
                u = data["result"][0]
                rating = u.get("rating", rating)
                max_rating = u.get("maxRating", max_rating)
                rank = u.get("rank", rank)
    except Exception as e:
        print(f"Error fetching Codeforces info: {e}")

    try:
        url_status = f"https://codeforces.com/api/user.status?handle={handle}"
        req_status = urllib.request.Request(url_status, headers={"User-Agent": "profile-stats-generator"})
        with urllib.request.urlopen(req_status, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            if data.get("status") == "OK" and data.get("result"):
                subs = data["result"]
                unique_solved = set(
                    (s["problem"]["contestId"], s["problem"]["index"])
                    for s in subs
                    if s.get("verdict") == "OK" and "contestId" in s.get("problem", {}) and "index" in s.get("problem", {})
                )
                if len(unique_solved) > 0:
                    solved = len(unique_solved)
    except Exception as e:
        print(f"Error fetching Codeforces status: {e}")

    return {"rating": rating, "maxRating": max_rating, "rank": rank, "solved": solved}

def fetch_leetcode_stats(username="orthodoxcoder"):
    try:
        query = {
            "query": """
            query getUserProfile($username: String!) {
              matchedUser(username: $username) {
                submitStatsGlobal {
                  acSubmissionNum { difficulty count }
                }
              }
            }
            """,
            "variables": {"username": username}
        }
        req = urllib.request.Request(
            "https://leetcode.com/graphql",
            data=json.dumps(query).encode("utf-8"),
            headers={"User-Agent": "profile-stats-generator", "Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            subs = data["data"]["matchedUser"]["submitStatsGlobal"]["acSubmissionNum"]
            counts = {item["difficulty"]: item["count"] for item in subs}
            return {
                "total": counts.get("All", 209),
                "easy": counts.get("Easy", 139),
                "medium": counts.get("Medium", 63),
                "hard": counts.get("Hard", 7)
            }
    except Exception as e:
        print(f"Error fetching LeetCode: {e}")
    return {"total": 209, "easy": 139, "medium": 63, "hard": 7}

def generate_github_svg(data):
    if data:
        repos_count = data["repositories"]["totalCount"]
        repos_nodes = data["repositories"]["nodes"]
        stars_count = sum(r["stargazerCount"] for r in repos_nodes)

        cc = data["contributionsCollection"]
        commits_count = cc["totalCommitContributions"]
        all_prs_count = data["pullRequests"]["totalCount"]
        merged_prs_count = data["mergedPRs"]["totalCount"]
        total_contribs = cc["contributionCalendar"]["totalContributions"]

        lang_sizes = defaultdict(int)
        lang_colors = {}
        for r in repos_nodes:
            for edge in r.get("languages", {}).get("edges", []):
                name = edge["node"]["name"]
                lang_colors[name] = edge["node"].get("color") or "#8b949e"
                lang_sizes[name] += edge["size"]

        total_size = sum(lang_sizes.values()) or 1
        sorted_langs = sorted(lang_sizes.items(), key=lambda x: x[1], reverse=True)[:3]
        top_langs = [
            (lang, (size / total_size) * 100, lang_colors.get(lang, "#8b949e"))
            for lang, size in sorted_langs
        ]
    else:
        repos_count = 60
        stars_count = 29
        commits_count = 216
        all_prs_count = 40
        merged_prs_count = 18
        total_contribs = 314
        top_langs = [
            ("Go", 57.0, "#00ADD8"),
            ("TypeScript", 24.0, "#3178c6"),
            ("JavaScript", 13.0, "#f1e05a")
        ]

    l1_name, l1_pct, l1_col = top_langs[0] if len(top_langs) > 0 else ("Go", 57.0, "#00ADD8")
    l2_name, l2_pct, l2_col = top_langs[1] if len(top_langs) > 1 else ("TypeScript", 24.0, "#3178c6")
    l3_name, l3_pct, l3_col = top_langs[2] if len(top_langs) > 2 else ("JavaScript", 13.0, "#f1e05a")

    bar_total = 118
    b1_w = max(2, int((l1_pct / 100.0) * bar_total))
    b2_w = max(2, int((l2_pct / 100.0) * bar_total))
    b3_w = max(2, bar_total - b1_w - b2_w)

    svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 830 136" width="830" height="136" fill="none">
  <title>Aarav Pathak — GitHub Activity</title>
  <defs>
    <!-- Glassmorphic Gradients -->
    <linearGradient id="glass-base" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#161b22" stop-opacity="0.88"/>
      <stop offset="100%" stop-color="#0d1117" stop-opacity="0.96"/>
    </linearGradient>
    <linearGradient id="glass-edge" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.16"/>
      <stop offset="45%" stop-color="#ffffff" stop-opacity="0.06"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0.02"/>
    </linearGradient>
    <linearGradient id="cell-glass" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#1f242c" stop-opacity="0.75"/>
      <stop offset="100%" stop-color="#12161c" stop-opacity="0.65"/>
    </linearGradient>
    <linearGradient id="cell-edge" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.12"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0.03"/>
    </linearGradient>

    <!-- Subtle Optical Glass Sheen Sweep -->
    <linearGradient id="sheen" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0"/>
      <stop offset="50%" stop-color="#ffffff" stop-opacity="0.22"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
      <animate attributeName="x1" values="-100%;100%" dur="8s" repeatCount="indefinite"/>
      <animate attributeName="x2" values="0%;200%" dur="8s" repeatCount="indefinite"/>
    </linearGradient>
  </defs>

  <style>
    .lbl {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; font-size: 11px; font-weight: 500; fill: #8b949e; letter-spacing: 0.1px; }}
    .num {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; font-size: 24px; font-weight: 600; fill: #f0f6fc; font-variant-numeric: tabular-nums; }}
    .sub {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; font-size: 11px; font-weight: 400; fill: #7d8590; }}
    .lang-item {{ font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace; font-size: 10.5px; font-weight: 400; fill: #c9d1d9; }}
    .lang-pct {{ font-weight: 500; fill: #8b949e; }}
  </style>

  <!-- Glassmorphic Card Frame -->
  <rect x="0.5" y="0.5" width="829" height="135" rx="8" fill="url(#glass-base)" stroke="url(#glass-edge)"/>
  <line x1="8" y1="1" x2="822" y2="1" stroke="url(#sheen)" stroke-width="1.2" stroke-linecap="round"/>

  <!-- Col 1: Contributions -->
  <g transform="translate(16, 16)">
    <rect x="0" y="0" width="148" height="104" rx="6" fill="url(#cell-glass)" stroke="url(#cell-edge)"/>
    <line x1="6" y1="1" x2="142" y2="1" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>
    <text x="14" y="24" class="lbl">Contributions</text>
    <text x="14" y="58" class="num">{total_contribs}</text>
    <text x="14" y="80" class="sub">Year-to-date</text>
  </g>

  <!-- Col 2: Commits -->
  <g transform="translate(178, 16)">
    <rect x="0" y="0" width="148" height="104" rx="6" fill="url(#cell-glass)" stroke="url(#cell-edge)"/>
    <line x1="6" y1="1" x2="142" y2="1" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>
    <text x="14" y="24" class="lbl">Commits</text>
    <text x="14" y="58" class="num">{commits_count}</text>
    <text x="14" y="80" class="sub">Direct code pushes</text>
  </g>

  <!-- Col 3: Pull Requests -->
  <g transform="translate(340, 16)">
    <rect x="0" y="0" width="148" height="104" rx="6" fill="url(#cell-glass)" stroke="url(#cell-edge)"/>
    <line x1="6" y1="1" x2="142" y2="1" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>
    <text x="14" y="24" class="lbl">Pull requests</text>
    <text x="14" y="58" class="num">{all_prs_count}</text>
    <text x="14" y="80" class="sub">{merged_prs_count} merged</text>
  </g>

  <!-- Col 4: Repositories -->
  <g transform="translate(502, 16)">
    <rect x="0" y="0" width="148" height="104" rx="6" fill="url(#cell-glass)" stroke="url(#cell-edge)"/>
    <line x1="6" y1="1" x2="142" y2="1" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>
    <text x="14" y="24" class="lbl">Repositories</text>
    <text x="14" y="58" class="num">{repos_count}</text>
    <text x="14" y="80" class="sub">{stars_count} stars earned</text>
  </g>

  <!-- Col 5: Top Stack -->
  <g transform="translate(664, 16)">
    <rect x="0" y="0" width="150" height="104" rx="6" fill="url(#cell-glass)" stroke="url(#cell-edge)"/>
    <line x1="6" y1="1" x2="144" y2="1" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>
    <text x="14" y="24" class="lbl">Top languages</text>
    <g transform="translate(14, 34)">
      <circle cx="4" cy="6" r="3.5" fill="{l1_col}"/>
      <text x="12" y="9" class="lang-item">{l1_name} <tspan class="lang-pct">{l1_pct:.0f}%</tspan></text>
      
      <circle cx="4" cy="22" r="3.5" fill="{l2_col}"/>
      <text x="12" y="25" class="lang-item">{l2_name} <tspan class="lang-pct">{l2_pct:.0f}%</tspan></text>

      <circle cx="4" cy="38" r="3.5" fill="{l3_col}"/>
      <text x="12" y="41" class="lang-item">{l3_name} <tspan class="lang-pct">{l3_pct:.0f}%</tspan></text>
    </g>

    <!-- Language Proportion Bar -->
    <rect x="14" y="86" width="{b1_w}" height="4" rx="2" fill="{l1_col}"/>
    <rect x="{14 + b1_w}" y="86" width="{b2_w}" height="4" fill="{l2_col}"/>
    <rect x="{14 + b1_w + b2_w}" y="86" width="{b3_w}" height="4" rx="2" fill="{l3_col}"/>
  </g>
</svg>'''

    with open("assets/stats.svg", "w") as f:
        f.write(svg_content)
    print("Updated assets/stats.svg")

def generate_competitive_svg(cf_data, lc_data):
    cf_rating = cf_data["rating"]
    cf_max = cf_data["maxRating"]
    cf_solved = cf_data["solved"]

    lc_total = lc_data["total"]
    lc_easy = lc_data["easy"]
    lc_med = lc_data["medium"]
    lc_hard = lc_data["hard"]

    # Verified CodeChef metrics for alive_frog_99
    cc_rating = 1410
    cc_contests = 23
    cc_solved = 82

    svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 830 112" width="830" height="112" fill="none">
  <title>Aarav Pathak — Competitive Programming Stats</title>
  <defs>
    <!-- Glassmorphic Gradients -->
    <linearGradient id="cp-glass" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#161b22" stop-opacity="0.88"/>
      <stop offset="100%" stop-color="#0d1117" stop-opacity="0.96"/>
    </linearGradient>
    <linearGradient id="cp-edge" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.16"/>
      <stop offset="45%" stop-color="#ffffff" stop-opacity="0.06"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0.02"/>
    </linearGradient>
    <linearGradient id="cp-cell" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#1f242c" stop-opacity="0.75"/>
      <stop offset="100%" stop-color="#12161c" stop-opacity="0.65"/>
    </linearGradient>
    <linearGradient id="cp-cell-edge" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.12"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0.03"/>
    </linearGradient>

    <!-- Subtle Optical Glass Sheen Sweep -->
    <linearGradient id="cp-sheen" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0"/>
      <stop offset="50%" stop-color="#ffffff" stop-opacity="0.22"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
      <animate attributeName="x1" values="-100%;100%" dur="8s" repeatCount="indefinite"/>
      <animate attributeName="x2" values="0%;200%" dur="8s" repeatCount="indefinite"/>
    </linearGradient>
  </defs>

  <style>
    .platform {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; font-size: 11px; font-weight: 500; fill: #8b949e; letter-spacing: 0.1px; }}
    .rating {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; font-size: 26px; font-weight: 600; fill: #f0f6fc; font-variant-numeric: tabular-nums; }}
    .detail {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; font-size: 11.5px; font-weight: 400; fill: #7d8590; }}
    .beacon {{ fill: #3fb950; }}
  </style>

  <!-- Glass Card Frame -->
  <rect x="0.5" y="0.5" width="829" height="111" rx="8" fill="url(#cp-glass)" stroke="url(#cp-edge)"/>
  <line x1="8" y1="1" x2="822" y2="1" stroke="url(#cp-sheen)" stroke-width="1.2" stroke-linecap="round"/>

  <!-- Col 1: Codeforces -->
  <g transform="translate(16, 16)">
    <rect x="0" y="0" width="254" height="80" rx="6" fill="url(#cp-cell)" stroke="url(#cp-cell-edge)"/>
    <line x1="6" y1="1" x2="248" y2="1" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>
    <text x="16" y="24" class="platform">Codeforces · orthodoxcoder</text>
    <text x="16" y="54" class="rating">{cf_rating}</text>
    <text x="16" y="71" class="detail">Peak {cf_max} · {cf_solved} problems solved</text>
  </g>

  <!-- Col 2: LeetCode -->
  <g transform="translate(288, 16)">
    <rect x="0" y="0" width="254" height="80" rx="6" fill="url(#cp-cell)" stroke="url(#cp-cell-edge)"/>
    <line x1="6" y1="1" x2="248" y2="1" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>
    <text x="16" y="24" class="platform">LeetCode · orthodoxcoder</text>
    <text x="16" y="54" class="rating">{lc_total}</text>
    <text x="16" y="71" class="detail">{lc_easy} easy · {lc_med} medium · {lc_hard} hard</text>
  </g>

  <!-- Col 3: CodeChef -->
  <g transform="translate(560, 16)">
    <rect x="0" y="0" width="254" height="80" rx="6" fill="url(#cp-cell)" stroke="url(#cp-cell-edge)"/>
    <line x1="6" y1="1" x2="248" y2="1" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>
    <text x="16" y="24" class="platform">CodeChef · alive_frog_99</text>
    <text x="16" y="54" class="rating">{cc_rating}</text>
    <text x="16" y="71" class="detail">Div 3 (2★) · {cc_contests} contests · {cc_solved} solved</text>
  </g>
</svg>'''

    with open("assets/competitive.svg", "w") as f:
        f.write(svg_content)
    print("Updated assets/competitive.svg")

def main():
    os.makedirs("assets", exist_ok=True)
    gh_data = fetch_github_stats()
    generate_github_svg(gh_data)

    cf_data = fetch_codeforces_stats()
    lc_data = fetch_leetcode_stats()
    generate_competitive_svg(cf_data, lc_data)

if __name__ == "__main__":
    main()
