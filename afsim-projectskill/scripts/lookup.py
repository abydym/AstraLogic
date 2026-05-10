# lookup.py — Search AFSIM 2.9.0 reference manual for syntax
# Usage: python lookup.py <keyword>
# Example: python lookup.py WSF_AIR_MOVER
#
# Portable: finds the manual relative to this script's parent directory

import sys, os

# Fix Windows console encoding for Unicode output
if sys.stdout.encoding and sys.stdout.encoding.upper() != 'UTF-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

def find_manual():
    """Auto-locate reference_manual.txt.
    Search order:
      1. <skill_dir>/references/reference_manual.txt  (offline copy in skill)
      2. <skill_dir>/../pdf_out/reference_manual.txt  (legacy workspace location)
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Preferred: offline copy inside the skill itself
    for rel in ['../references/reference_manual.txt', '../../references/reference_manual.txt']:
        path = os.path.normpath(os.path.join(script_dir, rel))
        if os.path.isfile(path):
            return path
    # Fallback: legacy workspace location
    for rel in ['../pdf_out/reference_manual.txt', '../../pdf_out/reference_manual.txt']:
        path = os.path.normpath(os.path.join(script_dir, rel))
        if os.path.isfile(path):
            return path
    return None

def lookup(keyword, context_before=200, context_after=2000):
    manual_path = find_manual()
    if not manual_path:
        print(f"ERROR: Cannot find reference_manual.txt")
        print("Expected: <skill_dir>/references/reference_manual.txt")
        print(f"Searched from: {os.path.dirname(os.path.abspath(__file__))}")
        return
    
    with open(manual_path, 'r', encoding='utf-8', errors='replace') as f:
        txt = f.read()
    
    idx = 0
    count = 0
    while True:
        idx = txt.find(keyword, idx)
        if idx < 0:
            break
        start = max(0, idx - context_before)
        end = min(len(txt), idx + context_after)
        chunk = txt[start:end]
        if keyword in chunk and len(chunk.strip()) > 50:
            print(f"=== Match {count+1} at position {idx} ===")
            print(chunk)
            print()
            count += 1
            if count >= 3:
                break
        idx += 1
    
    if count == 0:
        print(f"No results found for '{keyword}'")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python lookup.py <keyword>")
        print("Example: python lookup.py WSF_AIR_MOVER")
        sys.exit(1)
    lookup(sys.argv[1])
