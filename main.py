import xml.etree.ElementTree as ET
from pathlib import Path
import gzip
import os

presets_repo_path = Path("./Mono One")
amxd_path = presets_repo_path / "Mono One.amxd"
presets = presets_repo_path / "Presets"
test_preset = presets / "elphnt" / "Bass" / "Choker.adv"

def process_adv_preset(preset_path: str):
    with gzip.open(preset_path, 'rb') as f:
        xml_content = f.read()
        
    root = ET.fromstring(xml_content)

    rel_path = os.path.relpath(amxd_path, test_preset.parent)

    for patch_slot in root.findall(".//PatchSlot"):
        for fileref in patch_slot.findall(".//FileRef"):
            for rel_path_type in fileref.findall(".//RelativePathType"):
                rel_path_type.set("Value", "1")  # Relative path mode
            for path_elem in fileref.findall(".//Path"):
                path_elem.set("Value", "")
            for rel_path_elem in fileref.findall(".//RelativePath"):
                rel_path_elem.set("Value", rel_path)

    xml_output = '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding='unicode')

    modified_preset = test_preset.with_name(test_preset.stem + "_modified.adv")
    with gzip.open(modified_preset, 'wb') as f:
        f.write(xml_output.encode('utf-8'))