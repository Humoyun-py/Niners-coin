import os
import re

root_dir = r"c:\Users\humoyun\OneDrive\Desktop\Ninerscoin-main\frontend\pages"
# Regex matches the link tag, allowing for any indentation at start of line, and newline at end
pattern = r'(?m)^\s*<link rel="stylesheet" href="/styles/layout\.css">\s*$'

count_updated = 0

for dirpath, dirnames, filenames in os.walk(root_dir):
    for filename in filenames:
        if filename.endswith(".html"):
            file_path = os.path.join(dirpath, filename)
            
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Check if matches
                if re.search(pattern, content):
                    # Replace with empty string (removes the whole line)
                    new_content = re.sub(pattern, "", content)
                    
                    # Also cleanup potential double newlines if left behind, though not strictly necessary
                    # new_content = re.sub(r'\n\s*\n', '\n', new_content)

                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    print(f"Updated: {filename}")
                    count_updated += 1
                
            except Exception as e:
                print(f"Error processing {filename}: {e}")

print(f"\nTotal files updated: {count_updated}")
