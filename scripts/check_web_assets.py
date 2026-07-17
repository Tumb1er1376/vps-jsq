#!/usr/bin/env python3
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"


class AssetParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.assets = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        href = values.get("href") or ""
        src = values.get("src") or ""
        if tag == "link" and href.startswith("/assets/"):
            self.assets.append(href)
        if tag == "script" and src.startswith("/assets/"):
            self.assets.append(src)


html = (WEB / "index.html").read_text(encoding="utf-8")
parser = AssetParser()
parser.feed(html)
assert parser.assets, "no external assets referenced"
for asset in parser.assets:
    path = WEB / asset.lstrip("/")
    assert path.is_file(), f"missing asset: {asset}"

required_ids = ("calculate_btn", "payment_cycle", "copy_btn", "share_url")
for element_id in required_ids:
    assert f'id="{element_id}"' in html, f"missing required element: {element_id}"

print(f"validated {len(parser.assets)} assets and {len(required_ids)} required elements")
