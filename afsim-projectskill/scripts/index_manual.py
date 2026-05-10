#!/usr/bin/env python3
"""
AFSIM Reference Manual Index Generator v2
==========================================
Extracts command lists for all major AFSIM types.

Usage:
    python index_manual.py [path_to_manual.txt]

Output in ../references/:
    - wsf_radar_sensor.txt
    - wsf_air_mover.txt
    - ... (one per major type)
    - sensor_types.txt
    - processor_types.txt
"""

import os, sys, re

BULLET = '\u25aa'  # ▪ (black small square)

def find_manual():
    if len(sys.argv) > 1:
        return sys.argv[1]
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Preferred: offline copy inside skill
    for rel in ['../references/reference_manual.txt', '../../references/reference_manual.txt']:
        p = os.path.normpath(os.path.join(script_dir, rel))
        if os.path.isfile(p):
            return p
    # Fallback: legacy workspace location
    for rel in ['../pdf_out/reference_manual.txt', '../../pdf_out/reference_manual.txt']:
        p = os.path.normpath(os.path.join(script_dir, rel))
        if os.path.isfile(p):
            return p
    print("ERROR: Cannot find reference_manual.txt. Pass path as argument.")
    sys.exit(1)

def load(path):
    for enc in ['utf-8', 'utf-8-sig', 'gbk', 'latin-1']:
        try:
            with open(path, 'r', encoding=enc, errors='replace') as f:
                return f.read()
        except:
            continue
    return None

def extract_commands_from_section(txt, section_start, max_len=8000):
    """Extract bullet commands from a section of text starting at section_start."""
    section = txt[section_start:section_start + max_len]
    commands = []
    for line in section.split('\n'):
        stripped = line.strip()
        if not stripped:
            continue
        # Bullet commands start with ▪
        if stripped.startswith(BULLET):
            cmd = stripped[1:].strip()
            # Filter out TOC page references and section headings
            if any(x in cmd for x in ['第', '页', '共', '▪', '...', 'WSF_', 'sensor']):
                if not cmd.startswith('WSF_'):
                    continue
            if len(cmd) > 3 and not cmd.startswith(('0', '1', '2', '3', '4', '5', '6', '7', '8', '9')):
                commands.append(cmd)
        # Also catch '▪' embedded in lines (encoding issues)
        elif BULLET in stripped:
            parts = stripped.split(BULLET)
            for part in parts:
                part = part.strip()
                if part and len(part) > 3 and '<' in part:
                    commands.append(part)
    return commands

def find_main_section(txt, keyword, min_bullets=15):
    """Find the MAIN definition section (not TOC) for a keyword by looking for dense bullet clusters."""
    best_idx = -1
    best_bullets = 0
    idx = -1
    while True:
        idx = txt.find(keyword, idx + 1)
        if idx < 0:
            break
        ctx = txt[idx:idx + 5000]
        bullets = ctx.count(BULLET)
        if bullets > best_bullets:
            best_bullets = bullets
            best_idx = idx
    return best_idx if best_bullets >= min_bullets else -1

def main():
    path = find_manual()
    print(f"Loading: {path}")
    txt = load(path)
    if not txt:
        print("Failed to load.")
        sys.exit(1)
    print(f"Size: {len(txt)} chars, {txt.count(BULLET)} bullets found")

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'references')
    os.makedirs(out_dir, exist_ok=True)

    targets = [
        ("WSF_RADAR_SENSOR", "wsf_radar_sensor.txt"),
        ("WSF_AIR_MOVER", "wsf_air_mover.txt"),
        ("WSF_GROUND_MOVER", "wsf_ground_mover.txt"),
        ("WSF_GUIDED_MOVER", "wsf_guided_mover.txt"),
        ("WSF_GUIDANCE_COMPUTER", "wsf_guidance_computer.txt"),
        ("WSF_BALLISTIC_MISSILE_LAUNCH_COMPUTER", "wsf_launch_computer.txt"),
        ("WSF_EXPLICIT_WEAPON", "wsf_explicit_weapon.txt"),
        ("WSF_STRAIGHT_LINE_MOVER", "wsf_straight_line_mover.txt"),
        ("WSF_SCRIPT_PROCESSOR", "wsf_script_processor.txt"),
        ("WSF_GRADUATED_LETHALITY", "weapon_effects.txt"),
    ]

    for keyword, filename in targets:
        print(f"\n{keyword} ...", end=' ')
        idx = find_main_section(txt, keyword)
        if idx < 0:
            print("SKIP (no main section found)")
            continue
        cmds = extract_commands_from_section(txt, idx)
        outpath = os.path.join(out_dir, filename)
        with open(outpath, 'w', encoding='utf-8') as f:
            f.write(f"# {keyword} — Command Reference\n")
            f.write(f"# Extracted from AFSIM 2.9.0 Reference Manual\n")
            f.write(f"# Commands found: {len(cmds)}\n\n")
            for c in cmds:
                f.write(f"  {c}\n")
        print(f"→ {len(cmds)} commands → {outpath}")

    # Sensor types
    types = sorted(set(re.findall(r'WSF_\w+_SENSOR', txt)))
    with open(os.path.join(out_dir, 'sensor_types.txt'), 'w', encoding='utf-8') as f:
        f.write(f"# AFSIM Sensor Types ({len(types)})\n\n")
        for t in types:
            f.write(f"- {t}\n")
    print(f"\nSensor types: {len(types)}")

    # Processor types
    types = sorted(set(re.findall(r'WSF_\w+_PROCESSOR', txt)))
    with open(os.path.join(out_dir, 'processor_types.txt'), 'w', encoding='utf-8') as f:
        f.write(f"# AFSIM Processor Types ({len(types)})\n\n")
        for t in types:
            f.write(f"- {t}\n")
    print(f"Processor types: {len(types)}")

    # Mover types
    types = sorted(set(re.findall(r'WSF_\w+_MOVER', txt)))
    with open(os.path.join(out_dir, 'mover_types.txt'), 'w', encoding='utf-8') as f:
        f.write(f"# AFSIM Mover Types ({len(types)})\n\n")
        for t in types:
            f.write(f"- {t}\n")
    print(f"Mover types: {len(types)}")

    # Weapon types
    types = sorted(set(re.findall(r'WSF_\w+_WEAPON', txt)))
    with open(os.path.join(out_dir, 'weapon_types.txt'), 'w', encoding='utf-8') as f:
        f.write(f"# AFSIM Weapon Types ({len(types)})\n\n")
        for t in types:
            f.write(f"- {t}\n")
    print(f"Weapon types: {len(types)}")

    print(f"\nDone → {out_dir}")

if __name__ == '__main__':
    main()
