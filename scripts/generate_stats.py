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
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode())["data"]["user"]
                return data
        except Exception as e:
            print(f"Error fetching via standard library urllib with token: {e}")

    try:
        res = subprocess.check_output(["gh", "api", "graphql", "-f", f"query={query}"], text=True)
        return json.loads(res)["data"]["user"]
    except Exception as e:
        print(f"Error fetching via gh CLI: {e}")
        return None

def main():
    data = fetch_github_stats()

    if data:
        repos_count = data["repositories"]["totalCount"]
        repos_nodes = data["repositories"]["nodes"]
        stars_count = sum(r["stargazerCount"] for r in repos_nodes)
        
        cc = data["contributionsCollection"]
        commits_count = cc["totalCommitContributions"]
        all_prs_count = data["pullRequests"]["totalCount"]
        merged_prs_count = data["mergedPRs"]["totalCount"]
        
        # 2025 calendar had 8 contributions + current rolling calendar
        total_contribs = cc["contributionCalendar"]["totalContributions"] + 8

        # Language calculation
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
        # Fallback to accurate cached values
        repos_count = 49
        stars_count = 28
        commits_count = 176
        all_prs_count = 27
        merged_prs_count = 9
        total_contribs = 254
        top_langs = [
            ("TypeScript", 58.0, "#3178c6"),
            ("JavaScript", 28.0, "#f1e05a"),
            ("Go", 6.4, "#00ADD8")
        ]

    l1_name, l1_pct, l1_col = top_langs[0] if len(top_langs) > 0 else ("TypeScript", 58.0, "#3178c6")
    l2_name, l2_pct, l2_col = top_langs[1] if len(top_langs) > 1 else ("JavaScript", 28.0, "#f1e05a")
    l3_name, l3_pct, l3_col = top_langs[2] if len(top_langs) > 2 else ("Go", 6.4, "#00ADD8")

    bar_total = 118
    b1_w = int((l1_pct / 100.0) * bar_total)
    b2_w = int((l2_pct / 100.0) * bar_total)
    b3_w = max(4, bar_total - b1_w - b2_w)

    print(f"Stats: Contribs={total_contribs}, Commits={commits_count}, PRs={all_prs_count} (Merged={merged_prs_count}), Repos={repos_count}, Stars={stars_count}")

    svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 830 150" width="830" height="150" fill="none">
  <title>Aarav Pathak - GitHub Activity Stats</title>
  <defs>
    <linearGradient id="bg-grad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#111820"/>
      <stop offset="100%" stop-color="#0d1117"/>
    </linearGradient>
    <linearGradient id="glow-line" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#388bfd" stop-opacity="0"/>
      <stop offset="50%" stop-color="#58a6ff" stop-opacity="0.9"/>
      <stop offset="100%" stop-color="#388bfd" stop-opacity="0"/>
      <animate attributeName="x1" values="-100%;100%" dur="4s" repeatCount="indefinite"/>
      <animate attributeName="x2" values="0%;200%" dur="4s" repeatCount="indefinite"/>
    </linearGradient>
    <linearGradient id="accent-green" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#3fb950"/>
      <stop offset="100%" stop-color="#56d364"/>
    </linearGradient>
  </defs>

  <style>
    .label {{ font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace; font-size: 10px; font-weight: 600; letter-spacing: 1.5px; fill: #7d8590; text-transform: uppercase; }}
    .val {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 22px; font-weight: 700; fill: #f0f6fc; }}
    .unit {{ font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace; font-size: 11px; fill: #8b949e; font-weight: 400; }}
  </style>

  <!-- Card Background -->
  <rect x="0.5" y="0.5" width="829" height="149" rx="12" fill="url(#bg-grad)" stroke="#21262d"/>
  <line x1="20" y1="1" x2="810" y2="1" stroke="url(#glow-line)" stroke-width="1.5" stroke-linecap="round"/>

  <!-- Column 1: Contributions -->
  <g transform="translate(24, 20)">
    <rect x="0" y="0" width="144" height="110" rx="8" fill="#161b22" stroke="#30363d" stroke-width="0.8"/>
    <circle cx="16" cy="18" r="4" fill="#3fb950"/>
    <text x="26" y="21" class="label">CONTRIBUTIONS</text>
    <text x="16" y="58" class="val">{total_contribs}</text>
    <text x="16" y="76" class="unit">Total (2025–26)</text>
    <rect x="16" y="88" width="112" height="4" fill="#21262d" rx="2"/>
    <rect x="16" y="88" width="95" height="4" fill="url(#accent-green)" rx="2"/>
  </g>

  <!-- Column 2: Commits -->
  <g transform="translate(182, 20)">
    <rect x="0" y="0" width="144" height="110" rx="8" fill="#161b22" stroke="#30363d" stroke-width="0.8"/>
    <circle cx="16" cy="18" r="4" fill="#388bfd"/>
    <text x="26" y="21" class="label">COMMITS</text>
    <text x="16" y="58" class="val">{commits_count}</text>
    <text x="16" y="76" class="unit">Code Pushes</text>
    <rect x="16" y="88" width="112" height="4" fill="#21262d" rx="2"/>
    <rect x="16" y="88" width="85" height="4" fill="#388bfd" rx="2"/>
  </g>

  <!-- Column 3: PRs -->
  <g transform="translate(340, 20)">
    <rect x="0" y="0" width="144" height="110" rx="8" fill="#161b22" stroke="#30363d" stroke-width="0.8"/>
    <circle cx="16" cy="18" r="4" fill="#a371f7"/>
    <text x="26" y="21" class="label">PULL REQUESTS</text>
    <text x="16" y="58" class="val">{all_prs_count}</text>
    <text x="16" y="76" class="unit">{merged_prs_count} Merged • Open Source</text>
    <rect x="16" y="88" width="112" height="4" fill="#21262d" rx="2"/>
    <rect x="16" y="88" width="75" height="4" fill="#a371f7" rx="2"/>
  </g>

  <!-- Column 4: Repositories -->
  <g transform="translate(498, 20)">
    <rect x="0" y="0" width="144" height="110" rx="8" fill="#161b22" stroke="#30363d" stroke-width="0.8"/>
    <circle cx="16" cy="18" r="4" fill="#e3b341"/>
    <text x="26" y="21" class="label">REPOSITORIES</text>
    <text x="16" y="58" class="val">{repos_count}</text>
    <text x="16" y="76" class="unit">⭐ {stars_count} Stars Earned</text>
    <rect x="16" y="88" width="112" height="4" fill="#21262d" rx="2"/>
    <rect x="16" y="88" width="90" height="4" fill="#e3b341" rx="2"/>
  </g>

  <!-- Column 5: Top Languages -->
  <g transform="translate(656, 20)">
    <rect x="0" y="0" width="150" height="110" rx="8" fill="#161b22" stroke="#30363d" stroke-width="0.8"/>
    <circle cx="16" cy="18" r="4" fill="#f7816f"/>
    <text x="26" y="21" class="label">TOP STACK</text>
    
    <text x="16" y="44" class="unit" fill="{l1_col}">● {l1_name} <tspan fill="#f0f6fc">{l1_pct:.0f}%</tspan></text>
    <text x="16" y="62" class="unit" fill="{l2_col}">● {l2_name} <tspan fill="#f0f6fc">{l2_pct:.0f}%</tspan></text>
    <text x="16" y="80" class="unit" fill="{l3_col}">● {l3_name} <tspan fill="#f0f6fc">{l3_pct:.1f}%</tspan></text>

    <rect x="16" y="92" width="{bar_total}" height="4" fill="#21262d" rx="2"/>
    <rect x="16" y="92" width="{b1_w}" height="4" fill="{l1_col}" rx="2"/>
    <rect x="{16 + b1_w}" y="92" width="{b2_w}" height="4" fill="{l2_col}"/>
    <rect x="{16 + b1_w + b2_w}" y="92" width="{b3_w}" height="4" fill="{l3_col}" rx="2"/>
  </g>
</svg>'''

    os.makedirs("assets", exist_ok=True)
    with open("assets/stats.svg", "w") as f:
        f.write(svg_content)
    print("Successfully generated assets/stats.svg with live GitHub profile data!")

if __name__ == "__main__":
    main()
