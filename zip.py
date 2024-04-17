from pathlib import Path
from zipfile import ZipFile

script_path = Path(__file__).resolve().parent

name = 'half_tone_selector'
local_paths = [
    f'{name}.desktop',
    f'{name}/',
]

def recursiveWrite(f: ZipFile, path: Path):
    if path.name in ['__pycache__']:
        return

    name = path.relative_to(script_path)
    print(path, '-->', name)
    f.write(filename=path, arcname=name)
    if path.is_dir():
        for p in path.iterdir():
            recursiveWrite(f, p)

with ZipFile(script_path / f'{name}.zip', 'w') as f:
    for path in local_paths:
        recursiveWrite(f, script_path / path)
