import gzip
from pathlib import Path
import os
import xml.etree.ElementTree as ET

def process_adv_preset(preset_path: Path, amxd_path: Path):
    print(f"Processing {preset_path}")
    try:
        # Check if file is gzipped
        is_gzipped = False
        try:
            with gzip.open(preset_path, 'rb') as f:
                xml_content = f.read()
                is_gzipped = True
        except:
            # If not gzipped, read as regular XML
            with open(preset_path, 'rb') as f:
                xml_content = f.read()
                
        root = ET.fromstring(xml_content)
        rel_path = os.path.relpath(amxd_path, preset_path.parent)
        print(f"Relative path calculated: {rel_path}")
        
        # Find all FileRef elements - look in MxPatchRef specifically for Ableton files
        patch_refs_found = False
        
        # Direct child FileRef in MxPatchRef (handle Ableton format)
        for mx_patch_ref in root.findall(".//MxPatchRef"):
            for fileref in mx_patch_ref.findall("./FileRef"):
                patch_refs_found = True
                rel_path_type = fileref.find("./RelativePathType")
                if rel_path_type is not None:
                    rel_path_type.set("Value", "1")
                    print(f"Updated RelativePathType in MxPatchRef")
                
                path_elem = fileref.find("./Path")
                if path_elem is not None:
                    path_elem.set("Value", "")
                    print(f"Updated Path in MxPatchRef")
                
                rel_path_elem = fileref.find("./RelativePath")
                if rel_path_elem is not None:
                    rel_path_elem.set("Value", rel_path)
                    print(f"Updated RelativePath in MxPatchRef to: {rel_path}")
        
        # Generic approach for other PatchSlot structures
        if not patch_refs_found:
            for patch_slot in root.findall(".//PatchSlot"):
                for fileref in patch_slot.findall(".//FileRef"):
                    patch_refs_found = True
                    for rel_path_type in fileref.findall(".//RelativePathType"):
                        rel_path_type.set("Value", "1")
                        print(f"Updated RelativePathType")
                    
                    for path_elem in fileref.findall(".//Path"):
                        path_elem.set("Value", "")
                        print(f"Updated Path")
                    
                    for rel_path_elem in fileref.findall(".//RelativePath"):
                        rel_path_elem.set("Value", rel_path)
                        print(f"Updated RelativePath to: {rel_path}")
        
        if not patch_refs_found:
            print(f"Warning: No PatchSlot or FileRef found in {preset_path}")
        
        xml_output = '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding='unicode')
        # Create output filename with original extension
        output_path = preset_path.with_name(preset_path.stem + "_modified" + preset_path.suffix)
        
        # Save in same format as original (gzipped or not)
        if is_gzipped:
            with gzip.open(output_path, 'wb') as f:
                f.write(xml_output.encode('utf-8'))
        else:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(xml_output)
                
        print(f"Successfully processed and saved to {output_path}")
        return True
    except Exception as e:
        print(f"Error processing {preset_path}: {str(e)}")
        return False

if __name__ == "__main__":
    preset_folder = Path("./Mono One/Presets")
    amxd_path = Path("./Mono One/Mono One.amxd")
    
    # Track success/failure
    total_files = 0
    successful_files = 0
    
    # Process both .adv and .adg files
    for extension in ["*.adv", "*.adg"]:
        for preset in preset_folder.rglob(extension):
            total_files += 1
            if process_adv_preset(preset, amxd_path=amxd_path):
                successful_files += 1
    
    print(f"Processing complete: {successful_files}/{total_files} files successfully processed")