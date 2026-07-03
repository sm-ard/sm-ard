import re

DEVOPS_PULSE_README = "https://raw.githubusercontent.com/sm-ard/devops-pulse/main/README.md"
PULSE_REPO_URL = "https://github.com/sm-ard/devops-pulse"
START = "<!--PULSE:START-->"
END = "<!--PULSE:END-->"


def extract_pulse(devops_readme: str) -> tuple[str, int]:
    """Return (latest_date, cve_count) parsed from the devops-pulse README."""
    m = re.search(r"## Latest — (\d{4}-\d{2}-\d{2})", devops_readme)
    if not m:
        raise ValueError("no '## Latest — <date>' section found")
    date = m.group(1)
    sec = re.search(r"## Security \(CVEs\)(.*?)(?=\n## |\Z)", devops_readme, re.S)
    body = sec.group(1) if sec else ""
    if "No notable CVEs today." in body:
        count = 0
    else:
        count = len(re.findall(r"^- \*\*\[CVE", body, re.M))
    return date, count


def build_line(date: str, cve_count: int) -> str:
    if cve_count == 0:
        sev = "no new high/critical CVEs"
    elif cve_count == 1:
        sev = "1 new high/critical CVE"
    else:
        sev = f"{cve_count} new high/critical CVEs"
    return (f"- **[devops-pulse]({PULSE_REPO_URL})** — automated daily DevOps "
            f"digest (CVEs · releases · news) · latest {date}: {sev} · live")


def update_readme(readme: str, line: str) -> str:
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if not pattern.search(readme):
        raise ValueError("PULSE markers not found in README")
    return pattern.sub(f"{START}\n{line}\n{END}", readme)
