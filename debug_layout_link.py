import os

file_path = r"c:\Users\humoyun\OneDrive\Desktop\Ninerscoin-main\frontend\pages\admin\dashboard.html"

with open(file_path, "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if "layout.css" in line:
            print(f"Line {i+1}: {repr(line)}")
