def add_allow_duplicate():
    """Add allow_duplicate=True to all duplicate outputs"""
    import os
    import re
    
    app_path = r"c:\Users\Ngum\Documents\My projects\trade\mt5-smart-flow-scalper\src\dashboard\app.py"
    
    # Backup the original file
    backup_path = app_path + ".backup_allow_dup"
    os.system(f"copy {app_path} {backup_path}")
    
    with open(app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all Output() calls and add allow_duplicate=True
    output_pattern = r"Output\('([^']+)', '([^']+)'\)"
    
    # Track which outputs have been used
    used_outputs = set()
    
    def replacement_func(match):
        component_id = match.group(1)
        property_id = match.group(2)
        output_key = f"{component_id}.{property_id}"
        
        if output_key in used_outputs:
            # This is a duplicate - add allow_duplicate=True
            return f"Output('{component_id}', '{property_id}', allow_duplicate=True)"
        else:
            # First time seeing this output - record it
            used_outputs.add(output_key)
            return match.group(0)
    
    # Apply the replacement
    modified_content = re.sub(output_pattern, replacement_func, content)
    
    # Write back modified content
    with open(app_path, 'w', encoding='utf-8') as f:
        f.write(modified_content)
    
    print(f"Added allow_duplicate=True to duplicate outputs in {app_path}")
    print(f"Original file backed up to {backup_path}")

if __name__ == "__main__":
    add_allow_duplicate()