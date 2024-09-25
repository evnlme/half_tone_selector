import xml.etree.ElementTree as ET
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List
from zipfile import ZipFile
from .state import HalfToneSet
from .color import convertColorSpace

mimetype = 'application/x-krita-palette'
iccPath = Path(__file__).resolve().parent / 'icc/sRGB-elle-V2-srgbtrc.icc'


def exportPalette(halfTones: List[HalfToneSet], name: str, path: Path) -> None:
    with TemporaryDirectory() as temp:
        _exportPalette(halfTones, name, path, temp)

def _exportPalette(halfTones: List[HalfToneSet], name: str, path: Path, temp: Path) -> None:
    tempPath = Path(temp)
    mimetypePath = tempPath / 'mimetype'
    profilesPath = tempPath / 'profiles.xml'
    colorsetPath = tempPath / 'colorset.xml'

    with mimetypePath.open('w') as f:
        f.write(mimetype)

    profiles = ET.Element('Profiles')
    profileAttrs = {
        'colorModelId': 'RGBA',
        'colorDepthId': 'U8',
        'filename': iccPath.name,
        'name': iccPath.name,
    }
    profile = ET.SubElement(profiles, 'Profile', profileAttrs)
    with profilesPath.open('w') as f:
        f.write(ET.tostring(profiles, encoding='unicode'))

    colorsetAttrs = {
        'name': name,
        'version': '2.0',
        'comment': '',
        'rows': str(len(halfTones)),
        'columns': '12',
    }
    colorset = ET.Element('ColorSet', colorsetAttrs)
    for i, ht in enumerate(halfTones):
        for j, t in enumerate(ht.tones):
            rgb = convertColorSpace(t, 'Oklch', 'sRGB')
            entryAttrs = {
                'id': f'{12*i+j}',
                'name': f'Color {12*i+j}',
                'bitdepth': 'U8',
                'spot': 'false',
            }
            colorsetEntry = ET.SubElement(colorset, 'ColorSetEntry', entryAttrs)
            rgbElemAttrs = {
                'space': iccPath.name,
                'r': str(rgb[0]),
                'g': str(rgb[1]),
                'b': str(rgb[2]),
            }
            rgbElem = ET.SubElement(colorsetEntry, 'RGB', rgbElemAttrs)
            positionAttrs = {'row': str(i), 'column': str(j)}
            position = ET.SubElement(colorsetEntry, 'Position', positionAttrs)
    with colorsetPath.open('w') as f:
        f.write(ET.tostring(colorset, encoding='unicode'))

    with ZipFile(path / f'{name}.kpl', 'w') as f:
        f.write(filename=mimetypePath, arcname=mimetypePath.name)
        f.write(filename=iccPath, arcname=iccPath.name)
        f.write(filename=profilesPath, arcname=profilesPath.name)
        f.write(filename=colorsetPath, arcname=colorsetPath.name)
