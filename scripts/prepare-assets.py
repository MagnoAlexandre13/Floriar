"""Copy generated originals into the project as optimized WebP assets."""
from pathlib import Path
from PIL import Image

source = Path('C:/Users/DTIC/.codex/generated_images/01a1ac42-1d3b-7642-b9bd-daa9091b2f68')
target = Path(__file__).resolve().parent.parent / 'dist' / 'assets'
images = {
    'hero': 'exec-f98ba1ab-2ce3-4945-8ea6-c93e20ddce85.png',
    'studio': 'exec-f471743e-8c64-49e9-8a5e-29db90c9605f.png',
    'sunday-morning': 'exec-6af3ec8e-d1ac-4271-ab70-723fa92c4fa3.png',
    'garden-party': 'exec-9c07e50b-7ed2-48e1-8ce7-0a37761b229d.png',
    'softly-spoken': 'exec-2d84c048-b143-4785-a979-ca608c02699d.png',
    'wild-at-heart': 'exec-2c8a539c-de58-4446-bf72-44b2c0b2e961.png',
    'sunday-morning-detail': 'exec-ba2b5157-d52a-45b9-bfe1-5e9f098076d4.png',
    'garden-party-detail': 'exec-f09ddd28-9b84-40de-86d0-35f1c87ddecf.png',
    'softly-spoken-detail': 'exec-19606da5-bee9-45db-8e28-e0151bb2e3d2.png',
    'wild-at-heart-detail': 'exec-a5ee454d-d09a-4fcc-a3fc-e6f82d3a97c6.png',
}
for name, file in images.items():
    image = Image.open(source / file).convert('RGB')
    image.save(target / f'{name}.webp', 'WEBP', quality=85, method=6)
    if name in ['sunday-morning', 'garden-party', 'softly-spoken', 'wild-at-heart']:
        image.thumbnail((480, 600), Image.Resampling.LANCZOS)
        image.save(target / f'{name}-small.webp', 'WEBP', quality=83, method=6)
    print(f'{name}: {(target / (name + ".webp")).stat().st_size // 1024} KB')
