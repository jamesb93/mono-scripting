import gzip
from pathlib import Path
import os
import xml.etree.ElementTree as ET

def process_adv_preset(preset_path: Path, amxd_path: Path):
    with gzip.open(preset_path, 'rb') as f:
        xml_content = f.read()
        
    root = ET.fromstring(xml_content)
    rel_path = os.path.relpath(amxd_path, preset_path.parent)

    for patch_slot in root.findall(".//PatchSlot"):
        for fileref in patch_slot.findall(".//FileRef"):
            for rel_path_type in fileref.findall(".//RelativePathType"):
                rel_path_type.set("Value", "1")
            for path_elem in fileref.findall(".//Path"):
                path_elem.set("Value", "")
            for rel_path_elem in fileref.findall(".//RelativePath"):
                rel_path_elem.set("Value", rel_path)

    xml_output = '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding='unicode')

    with gzip.open(preset_path.with_name(preset_path.stem + "_modified.adv"), 'wb') as f:
        f.write(xml_output.encode('utf-8'))