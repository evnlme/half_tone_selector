from pathlib import Path
from zipfile import ZipFile

script_path = Path(__file__).resolve().parent

name = 'half_tone_selector'
local_paths = [
    f'{name}.desktop',
    f'{name}/',
    f'{name}/__init__.py',
    f'{name}/lib.py',
    f'{name}/Manual.html',
]

with ZipFile(script_path / f'{name}.zip', 'w') as f:
    for path in local_paths:
        f.write(filename=script_path / path, arcname=path)
