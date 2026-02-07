import os

root_dir = r"c:\Users\humoyun\OneDrive\Desktop\Ninerscoin-main\frontend\pages"

# The problematic string patterns introduced by PowerShell
bad_pattern_1 = 'main.css">`r`n    <link rel="stylesheet" href="/styles/layout.css">'
bad_pattern_2 = 'main.css">`n    <link rel="stylesheet" href="/styles/layout.css">'
# Also check for simple concatenation without newline
bad_pattern_3 = 'main.css"><link rel="stylesheet" href="/styles/layout.css">'

# The correct replacement
correct_replacement = 'main.css">\n    <link rel="stylesheet" href="/styles/layout.css">'

count_fixed = 0

for dirpath, dirnames, filenames in os.walk(root_dir):
    for filename in filenames:
        if filename.endswith(".html"):
            file_path = os.path.join(dirpath, filename)
            
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                new_content = content
                was_fixed = False
                
                if bad_pattern_1 in new_content:
                    new_content = new_content.replace(bad_pattern_1, correct_replacement)
                    was_fixed = True
                    
                if bad_pattern_2 in new_content:
                    new_content = new_content.replace(bad_pattern_2, correct_replacement)
                    was_fixed = True
                    
                if bad_pattern_3 in new_content:
                    new_content = new_content.replace(bad_pattern_3, correct_replacement)
                    was_fixed = True
                
                # Also check generically for `r`n literals anywhere else just in case
                if "`r`n" in new_content:
                     new_content = new_content.replace("`r`n", "\n")
                     was_fixed = True
                
                if was_fixed:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    print(f"Fixed formatting in: {filename}")
                    count_fixed += 1
                    
            except Exception as e:
                print(f"Error processing {filename}: {e}")

print(f"\nTotal files fixed: {count_fixed}")
