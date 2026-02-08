import os

root_dir = r"c:\Users\humoyun\OneDrive\Desktop\Ninerscoin-main\frontend\pages"
target_line = '<link rel="stylesheet" href="/styles/layout.css">'

count_updated = 0

for dirpath, dirnames, filenames in os.walk(root_dir):
    for filename in filenames:
        if filename.endswith(".html"):
            file_path = os.path.join(dirpath, filename)
            
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                
                new_lines = [line for line in lines if target_line not in line]
                
                if len(lines) != len(new_lines):
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.writelines(new_lines)
                    print(f"Updated: {filename}")
                    count_updated += 1
                    
            except Exception as e:
                print(f"Error processing {filename}: {e}")

print(f"\nTotal files updated: {count_updated}")
