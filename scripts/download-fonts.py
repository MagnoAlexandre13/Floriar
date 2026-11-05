"""Fetch the selected open-source fonts for self-hosted typography."""
from pathlib import Path
import re
import urllib.request

target = Path(__file__).resolve().parent.parent / 'dist' / 'assets'
url = 'https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300..700;1,300..700&family=DM+Sans:wght@100..900&display=swap'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36'}
css = urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30).read().decode()
blocks = re.findall(r'@font-face\s*\{(.*?)\}', css, re.S)
for family, style, name in [('Cormorant Garamond', 'normal', 'cormorant'), ('Cormorant Garamond', 'italic', 'cormorant-italic'), ('DM Sans', 'normal', 'dm-sans')]:
    matches = [block for block in blocks if f"font-family: '{family}'" in block and f'font-style: {style}' in block]
    source = re.search(r'src: url\(([^)]+)\)', matches[-1]).group(1)
    data = urllib.request.urlopen(urllib.request.Request(source, headers=headers), timeout=30).read()
    if data[:4] != b'wOF2':
        raise ValueError('Expected WOFF2 font; received a different format')
    (target / f'{name}.woff2').write_bytes(data)
    print(f'{name}.woff2: {len(data)} bytes')
for font in ['cormorantgaramond', 'dmsans']:
    license_url = f'https://raw.githubusercontent.com/google/fonts/main/ofl/{font}/OFL.txt'
    (target / f'{font}-OFL.txt').write_bytes(urllib.request.urlopen(license_url, timeout=30).read())
