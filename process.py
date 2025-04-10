import gzip
from pathlib import Path
import os
import xml.etree.ElementTree as ET
import argparse
import shutil
import re

def rearrange_specific_names(root):
    """
    Find and rearrange specific Names elements in the XML tree.
    This function directly manipulates the Names elements for specific parameters.
    
    Args:
        root: The XML root element
        
    Returns:
        bool: True if any changes were made, False otherwise
    """
    changes_made = False
    
    # Find all MxDEnumParameter elements
    for param in root.findall(".//MxDEnumParameter"):
        # Check the parameter name
        name_elem = param.find("./Name")
        if name_elem is None:
            continue
            
        name = name_elem.get("Value")
        
        # Handle "Env Trigger" parameter
        if name == "Env Trigger":
            # Find the Names element within this parameter
            names_elem = param.find("./Names")
            if names_elem is not None:
                print("Found Env Trigger Names element")
                
                # Create new order
                name_values = ["LFO", "Legato", "Retrig"]
                
                # Clear and rebuild Names element
                names_elem.clear()  # Remove all children
                
                # Create new order
                for i, value in enumerate(name_values):
                    new_name = ET.SubElement(names_elem, "Name")
                    new_name.set("Id", str(i))
                    inner_name = ET.SubElement(new_name, "Name")
                    inner_name.set("Value", value)
                
                print("Rearranged Env Trigger Names element")
                changes_made = True
        
        # Handle "Sub Oct" parameter (the -1, -2, -2 PWM values)
        elif name == "Sub Oct":
            # Find the Names element within this parameter
            names_elem = param.find("./Names")
            if names_elem is not None:
                print("Found Sub Oct Names element")
                
                # Create new order
                name_values = ["-2 PWM", "-2", "-1"]
                
                # Clear and rebuild Names element
                names_elem.clear()  # Remove all children
                
                # Create new order
                for i, value in enumerate(name_values):
                    new_name = ET.SubElement(names_elem, "Name")
                    new_name.set("Id", str(i))
                    inner_name = ET.SubElement(new_name, "Name")
                    inner_name.set("Value", value)
                
                print("Rearranged Sub Oct Names element")
                changes_made = True
    
    return changes_made

def process_adv_preset(preset_path: Path, amxd_path: Path, force_gzip=None, backup=True, rearrange_names=False):
    """
    Process an Ableton preset file to update paths and optionally rearrange Names elements.
    
    Args:
        preset_path: Path to the preset file
        amxd_path: Path to the target .amxd file
        force_gzip: If provided, forces output to be gzipped (True) or not (False).
                   If None, preserves the original format.
        backup: If True, creates a backup of the original file before modifying it
        rearrange_names: If True, rearranges the Names elements for specific parameters
    """
    print(f"Processing {preset_path}")
    try:
        # Make backup if requested
        if backup:
            backup_path = preset_path.with_name(preset_path.stem + "_backup" + preset_path.suffix)
            shutil.copy2(preset_path, backup_path)
            print(f"Created backup at {backup_path}")
        
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
        
        changes_made = False
        
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
                    changes_made = True
                
                path_elem = fileref.find("./Path")
                if path_elem is not None:
                    path_elem.set("Value", "")
                    print(f"Updated Path in MxPatchRef")
                    changes_made = True
                
                rel_path_elem = fileref.find("./RelativePath")
                if rel_path_elem is not None:
                    rel_path_elem.set("Value", rel_path)
                    print(f"Updated RelativePath in MxPatchRef to: {rel_path}")
                    changes_made = True
        
        # Generic approach for other PatchSlot structures
        if not patch_refs_found:
            for patch_slot in root.findall(".//PatchSlot"):
                for fileref in patch_slot.findall(".//FileRef"):
                    patch_refs_found = True
                    for rel_path_type in fileref.findall(".//RelativePathType"):
                        rel_path_type.set("Value", "1")
                        print(f"Updated RelativePathType")
                        changes_made = True
                    
                    for path_elem in fileref.findall(".//Path"):
                        path_elem.set("Value", "")
                        print(f"Updated Path")
                        changes_made = True
                    
                    for rel_path_elem in fileref.findall(".//RelativePath"):
                        rel_path_elem.set("Value", rel_path)
                        print(f"Updated RelativePath to: {rel_path}")
                        changes_made = True
        
        # Process Names elements if requested
        if rearrange_names:
            names_changes = rearrange_specific_names(root)
            if names_changes:
                changes_made = True
        
        if not changes_made:
            print(f"Warning: No changes were made to {preset_path}")
            if backup:
                # Remove backup if no changes were made
                os.remove(backup_path)
                print(f"Removed backup as no changes were made")
            return False
        
        xml_output = '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding='unicode')
        
        # Determine if output should be gzipped
        output_gzipped = is_gzipped
        if force_gzip is not None:
            output_gzipped = force_gzip
        
        # Save directly to the original file
        if output_gzipped:
            with gzip.open(preset_path, 'wb') as f:
                f.write(xml_output.encode('utf-8'))
        else:
            with open(preset_path, 'w', encoding='utf-8') as f:
                f.write(xml_output)
                
        print(f"Successfully updated {preset_path}" + 
              f" ({'gzipped' if output_gzipped else 'not gzipped'})")
        return True
    except Exception as e:
        print(f"Error processing {preset_path}: {str(e)}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process Ableton preset files to update paths.')
    parser.add_argument('--preset-folder', type=str, default="./Mono One/Presets",
                        help='Path to the presets folder')
    parser.add_argument('--amxd-path', type=str, default="./Mono One/Mono One.amxd",
                        help='Path to the target .amxd file')
    parser.add_argument('--force-gzip', type=str, choices=['yes', 'no'], 
                        help='Force output to be gzipped (yes) or not gzipped (no)')
    parser.add_argument('--no-backup', action='store_true',
                        help='Do not create backup files')
    parser.add_argument('--rearrange-names', action='store_true',
                        help='Rearrange Names elements for specific parameters')
    parser.add_argument('--debug', action='store_true',
                        help='Process only one file and quit (for debugging)')
    
    args = parser.parse_args()
    
    preset_folder = Path(args.preset_folder)
    amxd_path = Path(args.amxd_path)
    
    # Convert force_gzip argument to boolean or None
    force_gzip = None
    if args.force_gzip == 'yes':
        force_gzip = True
    elif args.force_gzip == 'no':
        force_gzip = False
    
    # Track success/failure
    total_files = 0
    successful_files = 0
    
    # Process both .adv and .adg files
    for extension in ["*.adv", "*.adg"]:
        for preset in preset_folder.rglob(extension):
            total_files += 1
            if process_adv_preset(preset, 
                                  amxd_path=amxd_path, 
                                  force_gzip=force_gzip, 
                                  backup=not args.no_backup,
                                  rearrange_names=args.rearrange_names):
                successful_files += 1
                if args.debug:
                    print("Debug mode: Processed one file, exiting")
                    quit()
    
    print(f"Processing complete: {successful_files}/{total_files} files successfully processed")