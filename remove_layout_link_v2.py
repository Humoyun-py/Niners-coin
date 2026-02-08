import os
import re

root_dir = r"c:\Users\humoyun\OneDrive\Desktop\Ninerscoin-main\frontend\pages"
# Regex to match the link tag with any surrounding whitespace
pattern = r'\s*<link rel="stylesheet" href="/styles/layout\.css">\s*'

count_updated = 0

for dirpath, dirnames, filenames in os.walk(root_dir):
    for filename in filenames:
        if filename.endswith(".html"):
            file_path = os.path.join(dirpath, filename)
            
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Check if the file contains the pattern
                if re.search(pattern, content):
                    new_content = re.sub(pattern, "\n", content) # Replace with a single newline to maintain some structure if needed, or empty string if it leaves a blank line.
                    
                    # If we replaced with newline, we might have introduced extra blank lines. 
                    # But for now, let's just remove the specific tag.
                    # Actually, better to just remove the specific line if it was added on a new line.
                    
                    # Let's try a simpler string replace first if regex is too aggressive, 
                    # but regex is better for whitespace.
                    # The previous script might have failed because of how I constructed 'target_line'.
                    
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    print(f"Updated: {filename}")
                    count_updated += 1
                else:
                    # Debug: check if it's there but slightly different
                    if "layout.css" in content:
                        print(f"Found 'layout.css' in {filename} but regex didn't match. Manual check needed.")
                    
            except Exception as e:
                print(f"Error processing {filename}: {e}")

print(f"\nTotal files updated: {count_updated}")
