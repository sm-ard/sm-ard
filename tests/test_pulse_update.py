import pytest

import pulse_update as pu


DEVOPS_README_WITH_CVES = """# devops-pulse

blurb here

## Latest — 2026-07-03

## Security (CVEs)

- **[CVE-2026-1](https://nvd/1)** `CRITICAL` — bad bug
- **[CVE-2026-2](https://nvd/2)** `HIGH` — other bug

## Releases

- **Kubernetes** [`v1.33.0`](u)

## News

- [post](u) — _Kubernetes Blog_
"""

DEVOPS_README_NO_CVES = """# devops-pulse

## Latest — 2026-07-04

## Security (CVEs)

No notable CVEs today.

## Releases

No notable releases today.
"""


def test_extract_pulse_counts_cves():
    date, count = pu.extract_pulse(DEVOPS_README_WITH_CVES)
    assert date == "2026-07-03"
    assert count == 2


def test_extract_pulse_zero_when_none():
    date, count = pu.extract_pulse(DEVOPS_README_NO_CVES)
    assert date == "2026-07-04"
    assert count == 0


def test_extract_pulse_missing_date_raises():
    with pytest.raises(ValueError):
        pu.extract_pulse("no latest section here")


def test_extract_pulse_security_last_section():
    md = "## Latest — 2026-07-05\n\n## Security (CVEs)\n\n- **[CVE-2026-9](u)** `HIGH` — x\n"
    date, count = pu.extract_pulse(md)
    assert date == "2026-07-05"
    assert count == 1


def test_build_line_plural():
    line = pu.build_line("2026-07-03", 2)
    assert "latest 2026-07-03: 2 new high/critical CVEs" in line
    assert "devops-pulse" in line
    assert line.startswith("- ")


def test_build_line_singular():
    assert "1 new high/critical CVE" in pu.build_line("2026-07-03", 1)
    assert "1 new high/critical CVEs" not in pu.build_line("2026-07-03", 1)


def test_build_line_zero():
    assert "no new high/critical CVEs" in pu.build_line("2026-07-03", 0)


def test_update_readme_replaces_between_markers():
    readme = "top\n<!--PULSE:START-->\nOLD\n<!--PULSE:END-->\nbottom\n"
    out = pu.update_readme(readme, "- NEW LINE")
    assert "OLD" not in out
    assert "- NEW LINE" in out
    assert out.startswith("top")
    assert out.rstrip().endswith("bottom")
    assert "<!--PULSE:START-->" in out and "<!--PULSE:END-->" in out


def test_update_readme_missing_markers_raises():
    with pytest.raises(ValueError):
        pu.update_readme("no markers here", "- NEW")


def _seed_readme(tmp_path):
    p = tmp_path / "README.md"
    p.write_text("top\n<!--PULSE:START-->\nOLD\n<!--PULSE:END-->\nbottom\n",
                 encoding="utf-8")
    return p


def test_main_writes_updated_line(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _seed_readme(tmp_path)
    pu.main(fetch=lambda url: DEVOPS_README_WITH_CVES)
    out = (tmp_path / "README.md").read_text(encoding="utf-8")
    assert "latest 2026-07-03: 2 new high/critical CVEs" in out
    assert "OLD" not in out


def test_main_skips_on_fetch_error_without_writing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    p = _seed_readme(tmp_path)
    before = p.read_text(encoding="utf-8")

    def boom(url):
        raise RuntimeError("network down")

    pu.main(fetch=boom)  # must not raise
    assert p.read_text(encoding="utf-8") == before  # unchanged
