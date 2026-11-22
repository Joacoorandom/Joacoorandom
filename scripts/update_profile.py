"""Refresh only public repository metadata; leave the hand-written profile intact."""

import html
import json
import os
from pathlib import Path
import re
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
START = "<!-- PUBLIC_REPOS:START -->"
END = "<!-- PUBLIC_REPOS:END -->"


def public_repos(owner, fetch):
    result = []
    for page in range(1, 101):
        batch = fetch(f"/users/{quote(owner, safe='')}/repos?type=owner&per_page=100&page={page}")
        if not isinstance(batch, list):
            raise ValueError("Expected a repository list")
        for repo in batch:
            if (repo.get("private") is False
                    and repo.get("visibility", "public") == "public"
                    and repo.get("owner", {}).get("login", "").casefold() == owner.casefold()
                    and repo["name"].casefold() != owner.casefold()):
                result.append(repo)
        if len(batch) < 100:
            return sorted(result, key=lambda r: (bool(r.get("fork")), r["name"].casefold()))
    raise ValueError("Repository pagination did not finish")


def text(value):
    return html.escape(" ".join(str(value or "").split()), quote=True)


def catalog(repos, config):
    owner = config["owner"]
    lines = ['<img src="./assets/modules.svg" width="100%" alt="Repositorios públicos: proyectos propios y forks; el repositorio del perfil no se cuenta." />', ""]
    for forks, title in [(False, "Proyectos propios"), (True, "Forks para explorar")]:
        group = [r for r in repos if bool(r.get("fork")) == forks]
        lines.extend([f"### {title}", "", "<table>", "<tr><th>Proyecto</th><th>Qué hay detrás</th><th>Lenguaje</th></tr>"])
        for repo in group:
            name = repo["name"]
            url = f"https://github.com/{quote(owner, safe='')}/{quote(name, safe='')}"
            description = config.get("descriptions", {}).get(name, repo.get("description") or "Explora el código y la documentación.")
            archived = " · archivado" if repo.get("archived") else ""
            lines.append(f'<tr><td><a href="{url}"><strong>{text(name)}</strong></a>{archived}</td><td>{text(description)}</td><td>{text(repo.get("language") or "—")}</td></tr>')
        if not group:
            lines.append('<tr><td colspan="3">Sin repositorios públicos en esta sección.</td></tr>')
        lines.extend(["</table>", ""])
    lines.append("<sub>Catálogo actualizado automáticamente cada 6 horas con datos públicos de GitHub.</sub>")
    return "\n".join(lines)


def modules(repos, config):
    theme = config["theme"]
    for color in theme.values():
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
            raise ValueError("Theme colors must be six-digit hex values")
    cards = config["modules"]
    if len(cards) != 3:
        raise ValueError("The strip has three configurable modules")
    counts = {"total": len(repos), "forks": sum(bool(r.get("fork")) for r in repos)}
    counts["originals"] = counts["total"] - counts["forks"]
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="166" viewBox="0 0 1200 166" role="img"><title>Repositorios públicos de {text(config["owner"])}</title>']
    for i, card in enumerate(cards):
        bg = theme["highlight"] if i == 0 else theme["background"]
        x = i * 408
        svg.append(f'<g transform="translate({x} 0)"><rect width="384" height="166" rx="20" fill="{bg}"/><g fill="{theme["ink"]}" font-family="DejaVu Sans,Arial,sans-serif"><text x="25" y="35" font-size="12" letter-spacing="1.5">{text(card["label"])}</text><text x="25" y="101" font-size="54" font-weight="700">{counts[card["metric"]]:02d}</text><text x="25" y="139" font-size="14">{text(card["caption"])}</text></g><rect x="335" y="28" width="16" height="16" rx="4" fill="{theme["accent"]}"/></g>')
    return "\n".join(svg + ["</svg>\n"])


def replace_catalog(readme, generated):
    if readme.count(START) != 1 or readme.count(END) != 1:
        raise ValueError("README must contain exactly one pair of catalog markers")
    before, rest = readme.split(START)
    _, after = rest.split(END)
    return before + START + "\n\n" + generated + "\n\n" + END + after


def api(path):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "Joacoorandom-public-profile", "X-GitHub-Api-Version": "2022-11-28"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urlopen(Request("https://api.github.com" + path, headers=headers), timeout=30) as response:
        return json.load(response)


def main():
    config = json.loads((ROOT / "profile.json").read_text())
    repos = public_repos(config["owner"], api)
    readme_path = ROOT / "README.md"
    readme = replace_catalog(readme_path.read_text(), catalog(repos, config))
    svg = modules(repos, config)
    for path, content in [(readme_path, readme), (ROOT / "assets/modules.svg", svg)]:
        if not path.exists() or path.read_text() != content:
            path.write_text(content, encoding="utf-8")
            print(f"Updated {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
