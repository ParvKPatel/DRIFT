import os

REPLACEMENTS = {
    "DRIFT": "DRIFT",
    "Drift": "Drift",
    "drift": "drift",
    "DRIFT": "DRIFT",
    "drift": "drift",
    "drift": "drift"
}

def rename_in_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return False
        
    new_content = content
    for old_str, new_str in REPLACEMENTS.items():
        new_content = new_content.replace(old_str, new_str)
        
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

def main():
    modified_files = 0
    for root, dirs, files in os.walk("/Users/parvpatel/SIH MVP"):
        if "node_modules" in root or ".git" in root or "__pycache__" in root or ".venv" in root or ".next" in root:
            continue
            
        for file in files:
            # Skip images and compiled files
            if file.endswith((".png", ".jpg", ".jpeg", ".webp", ".pyc", ".db", ".sqlite3", ".csv")):
                continue
                
            filepath = os.path.join(root, file)
            if rename_in_file(filepath):
                print(f"Modified: {filepath}")
                modified_files += 1
                
    print(f"Total files modified: {modified_files}")

if __name__ == "__main__":
    main()
