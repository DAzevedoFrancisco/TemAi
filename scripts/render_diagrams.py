"""Extrai diagramas Mermaid do markdown e gera imagens PNG com Playwright."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'docs' / 'modelagem' / 'diagramas-sistema-mob.md'
OUTPUT_DIR = ROOT / 'docs' / 'modelagem' / 'imagens'
MMD_DIR = OUTPUT_DIR / 'mmd'

SLUGS = [
    '01-classes',
    '02-der',
    '03-casos-de-uso',
    '04-atividade-cadastro',
    '04-atividade-autenticacao',
    '04-atividade-estabelecimento',
    '04-atividade-produto',
    '04-atividade-pesquisa',
    '04-atividade-favorito',
    '04-atividade-avaliacao',
    '05-sequencia-cadastro',
    '05-sequencia-autenticacao',
    '05-sequencia-estabelecimento',
    '05-sequencia-produto',
    '05-sequencia-localizacao',
    '05-sequencia-favorito',
    '05-sequencia-admin',
]

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="pt">
<head>
  <meta charset="UTF-8">
  <style>
    body {{
      margin: 0;
      padding: 24px;
      background: #ffffff;
      font-family: Arial, sans-serif;
    }}
    #diagram {{
      display: inline-block;
    }}
  </style>
</head>
<body>
  <div id="diagram" class="mermaid">
{diagram}
  </div>
  <script type="module">
    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
    mermaid.initialize({{
      startOnLoad: true,
      theme: 'default',
      securityLevel: 'loose',
      fontFamily: 'Arial, sans-serif',
    }});
    await mermaid.run({{ querySelector: '.mermaid' }});
    window.__MERMAID_READY__ = true;
  </script>
</body>
</html>
"""


def extract_mermaid_blocks(content: str) -> list[str]:
    return re.findall(r'```mermaid\s*\n(.*?)```', content, flags=re.DOTALL)


def render_png(page, mermaid_source: str, png_path: Path) -> None:
    html = HTML_TEMPLATE.format(diagram=mermaid_source.strip())
    page.set_content(html, wait_until='networkidle')
    page.wait_for_function('window.__MERMAID_READY__ === true', timeout=120000)
    page.wait_for_timeout(500)
    diagram = page.locator('#diagram svg').first
    diagram.wait_for(state='visible', timeout=120000)
    diagram.screenshot(path=str(png_path), omit_background=False)


def main() -> int:
    if not SOURCE.exists():
        print(f'Ficheiro não encontrado: {SOURCE}', file=sys.stderr)
        return 1

    content = SOURCE.read_text(encoding='utf-8')
    blocks = extract_mermaid_blocks(content)

    if len(blocks) != len(SLUGS):
        print(
            f'Aviso: {len(blocks)} diagramas encontrados, {len(SLUGS)} slugs definidos.',
            file=sys.stderr,
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    MMD_DIR.mkdir(parents=True, exist_ok=True)

    generated: list[Path] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 2200, 'height': 1600}, device_scale_factor=2)

        for index, block in enumerate(blocks):
            slug = SLUGS[index] if index < len(SLUGS) else f'diagrama-{index + 1:02d}'
            mmd_path = MMD_DIR / f'{slug}.mmd'
            png_path = OUTPUT_DIR / f'{slug}.png'
            mmd_path.write_text(block.strip() + '\n', encoding='utf-8')

            print(f'A gerar {png_path.name}...')
            try:
                render_png(page, block, png_path)
            except Exception as exc:  # noqa: BLE001
                print(f'Erro ao gerar {png_path.name}: {exc}', file=sys.stderr)
                browser.close()
                return 1

            generated.append(png_path)

        browser.close()

    print(f'\n{len(generated)} imagens geradas em {OUTPUT_DIR}')
    for path in generated:
        print(f' - {path.relative_to(ROOT)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
