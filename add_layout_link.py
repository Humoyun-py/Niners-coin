import os

root_dir = r"c:\Users\humoyun\OneDrive\Desktop\Ninerscoin-main\frontend\pages"
layout_link = '    <link rel="stylesheet" href="/styles/layout.css">\n'

width_main_css = '<link rel="stylesheet" href="/styles/main.css">'

count_updated = 0
count_skipped = 0

for dirpath, dirnames, filenames in os.walk(root_dir):
    for filename in filenames:
        if filename.endswith(".html"):
            file_path = os.path.join(dirpath, filename)
            
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                if "layout.css" in content:
                    print(f"Skipped (already exists): {filename}")
                    count_skipped += 1
                    continue
                
                if width_main_css in content:
                    new_content = content.replace(width_main_css, width_main_css + "\n" + layout_link)
                    
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    
                    print(f"Updated: {filename}")
                    count_updated += 1
                else:
                    print(f"Warning: main.css link not found in {filename}")
                    
            except Exception as e:
                print(f"Error processing {filename}: {e}")

print(f"\nTotal updated: {count_updated}")
print(f"Total skipped: {count_skipped}")
