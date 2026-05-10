#!/usr/bin/env python3
"""
LEO Satellite Communication Link Analysis
==========================================
Single-entry script: auto-find AFSIM -> compile -> run -> parse -> plot -> view in Mystic.
Supports 6-sat constellation project and single-sat leo_comm project.

Usage:
    cd leo_comm/
    python ../scripts/analyze_leo_comm.py                         # auto: find AFSIM + compile + plot + Mystic
    python ../scripts/analyze_leo_comm.py --main leo_comm.txt     # specify main file
    python ../scripts/analyze_leo_comm.py --plot-only             # re-plot from existing output
    python ../scripts/analyze_leo_comm.py --no-mystic             # skip opening Mystic
    python ../scripts/analyze_leo_comm.py --compile-only          # only compile, no plots
"""

import os, sys, re, subprocess, argparse, glob, platform, time
from collections import defaultdict

# ── Matplotlib ───────────────────────────────────────────────────────────────
HAVE_MPL = False
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    HAVE_MPL = True
except ImportError:
    pass


# ═══════════════════════════════════════════════════════════════════════════════
# 1. FULL-DISK AFSIM SCANNER
# ═══════════════════════════════════════════════════════════════════════════════

def scan_for_afsim():
    """
    Full-disk search for mission.exe and mystic.exe.
    Uses cmd.exe dir /s which is 10-50x faster than PowerShell Get-ChildItem.
    Returns (afsim_home, mission_path, mystic_path) or (None, None, None).
    """
    print("\n" + "=" * 60)
    print("SCANNING SYSTEM FOR AFSIM...")
    print("=" * 60)

    # --- Fast path: check environment variable ---
    afsim_home = os.environ.get('AFSIM_HOME', '')
    if afsim_home:
        mission = os.path.join(afsim_home, 'bin', 'mission.exe')
        mystic = os.path.join(afsim_home, 'bin', 'mystic.exe')
        if os.path.isfile(mission):
            print(f"  Found via AFSIM_HOME: {afsim_home}")
            return afsim_home, mission, mystic if os.path.isfile(mystic) else None

    # --- Fast path: check common install locations ---
    common_dirs = [
        r'C:\AFSIM2.9\afsim-2.9.0',
        r'C:\AFSIM\afsim-2.9.0',
        r'C:\AFSIM2.9',
        r'C:\AFSIM',
        r'C:\Program Files\AFSIM',
        r'C:\Program Files (x86)\AFSIM',
        os.path.expanduser(r'~\AFSIM'),
        os.path.expanduser(r'~\afsim-2.9.0'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'AFSIM'),
        os.path.join(os.environ.get('PROGRAMFILES', ''), 'AFSIM'),
    ]
    # Deduplicate
    seen = set()
    for d in common_dirs:
        if d and d not in seen:
            seen.add(d)
            mission = os.path.join(d, 'bin', 'mission.exe')
            if os.path.isfile(mission):
                mystic = os.path.join(d, 'bin', 'mystic.exe')
                print(f"  Found in common location: {d}")
                return d, mission, mystic if os.path.isfile(mystic) else None

    # --- Full disk scan: use cmd dir /s for speed ---
    drives = []
    for letter in 'CDEFGHIJKLMNOPQRSTUVWXYZ':
        drive = f'{letter}:'
        if os.path.exists(drive):
            drives.append(drive)

    print(f"  Scanning {len(drives)} drive(s): {', '.join(drives)}")
    print(f"  Searching for mission.exe... (this may take a moment)")

    for drive in drives:
        try:
            # Use CMD dir /s which is much faster than PowerShell for recursive search
            result = subprocess.run(
                ['cmd', '/c', f'dir /s /b {drive}\\mission.exe 2>nul'],
                capture_output=True, text=True, timeout=30
            )
            if result.stdout.strip():
                paths = [p.strip() for p in result.stdout.splitlines() if p.strip()]
                for p in paths:
                    if os.path.isfile(p) and 'mission.exe' in p.lower():
                        # Extract home: parent of bin/
                        parent = os.path.dirname(os.path.dirname(p))
                        mystic_path = os.path.join(os.path.dirname(p), 'mystic.exe')
                        print(f"  Found at: {p}")
                        print(f"  AFSIM_HOME: {parent}")
                        return parent, p, mystic_path if os.path.isfile(mystic_path) else None
        except subprocess.TimeoutExpired:
            print(f"  (Scan timeout on {drive}, skipping...)")
            continue
        except Exception:
            continue

    print("  AFSIM not found on any drive.")
    print("  Install AFSIM or use --plot-only to view existing results.")
    return None, None, None


# ═══════════════════════════════════════════════════════════════════════════════
# 2. COMPILE & RUN
# ═══════════════════════════════════════════════════════════════════════════════

def compile_and_run(mission_exe, main_file, work_dir, output_dir='output'):
    """Run mission.exe -es to compile and execute the simulation."""
    if not os.path.isfile(main_file):
        print(f"\nERROR: Main file not found: {main_file}")
        return False

    os.makedirs(os.path.join(work_dir, 'output'), exist_ok=True)

    print(f"\n{'=' * 60}")
    print(f"COMPILING: {mission_exe}")
    print(f"  Input:  {main_file}")
    print(f"  Work:   {work_dir}")
    print(f"{'=' * 60}")

    try:
        result = subprocess.run(
            [mission_exe, '-es', main_file],
            capture_output=True, text=True,
            cwd=work_dir,
            timeout=300  # 5 min max
        )
    except subprocess.TimeoutExpired:
        print("ERROR: mission.exe timed out after 5 minutes")
        return False
    except FileNotFoundError:
        print(f"ERROR: Cannot execute {mission_exe}")
        return False

    # Save log: derive filename from main file (not hardcoded)
    main_basename = os.path.splitext(os.path.basename(main_file))[0]
    log_path = os.path.join(work_dir, output_dir, main_basename + '.log')
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    with open(log_path, 'w', encoding='utf-8') as f:
        f.write(result.stdout)
        if result.stderr:
            f.write("\n--- STDERR ---\n")
            f.write(result.stderr)

    # Print output (limited)
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write(result.stdout)
        if result.stderr:
            f.write("\n--- STDERR ---\n")
            f.write(result.stderr)

    # Print output (limited)
    out_lines = result.stdout.splitlines()
    print(f"\n  Return code: {result.returncode}")
    print(f"  Output lines: {len(out_lines)}")

    # Show key lines: errors + summary + first/last data
    error_lines = [l for l in out_lines if 'error' in l.lower() or 'Error' in l or 'ERROR' in l]
    if error_lines:
        print(f"\n  ERRORS ({len(error_lines)}):")
        for l in error_lines[:10]:
            print(f"    {l}")
        if len(error_lines) > 10:
            print(f"    ... and {len(error_lines)-10} more")

    # Show last 10 lines (usually has simulation summary)
    print(f"\n  Last output:")
    for l in out_lines[-10:]:
        print(f"    {l}")

    if result.stderr:
        stderr_lines = [l for l in result.stderr.splitlines() if l.strip()]
        if stderr_lines:
            print(f"\n  STDERR ({len(stderr_lines)} lines):")
            for l in stderr_lines[:10]:
                print(f"    {l}")

    if result.returncode != 0:
        print(f"\n  [FAIL] COMPILATION FAILED (code {result.returncode})")
        print(f"     Check {log_path} for details.")
        return False

    print(f"\n  [OK] COMPILATION SUCCESSFUL")
    print(f"     Log saved: {log_path}")

    # List output files
    out_dir_full = os.path.join(work_dir, output_dir)
    for f in sorted(glob.glob(os.path.join(out_dir_full, '*'))):
        size = os.path.getsize(f)
        print(f"     {os.path.basename(f):30s} {size:>8d} bytes")

    return True


# ═══════════════════════════════════════════════════════════════════════════════
# 3. PARSE OUTPUT
# ═══════════════════════════════════════════════════════════════════════════════

def detect_encoding(path):
    """Detect UTF-16 vs UTF-8 by sniffing BOM."""
    with open(path, 'rb') as f:
        head = f.read(2)
    return 'utf-16' if head == b'\xff\xfe' else 'utf-8'


def parse_links(source_path):
    """
    Parse link_budget output lines. Works for .evt, .log, .csv.
    Line format: "TIME RNG=xxx GRND=xxx DELAY=xxxms LINK=UP" or
                 "TIME SATn_RNG=xxx GRND=xxx ELEV=yy DELAY=zzzms LINK=UP GS=name"
    """
    if not os.path.isfile(source_path):
        return [], [], [], [], []

    encoding = detect_encoding(source_path)

    times, ranges, grounds, delays, link_states = [], [], [], [], []

    # Primary pattern: RNG=xxx GRND=xxx DELAY=xxxms LINK=xx
    # Supports scientific notation like 4.14136e+06
    pat1 = re.compile(r'(\d+(?:\.\d+)?)\s+.*RNG=([\de.+\-]+)\s+GRND=([\de.+\-]+)\s+'
                      r'(?:ELEV=[\de.+\-]+\s+)?DELAY=([\de.+\-]+)ms\s+LINK=(\w+)')

    with open(source_path, 'r', encoding=encoding, errors='replace') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            m = pat1.search(line)
            if m:
                times.append(float(m.group(1)))
                ranges.append(float(m.group(2)))
                grounds.append(float(m.group(3)))
                delays.append(float(m.group(4)))
                link_states.append(m.group(5))

    return times, ranges, grounds, delays, link_states


def parse_constellation_log(log_path):
    """
    Parse constellation simulation log.
    Extracts satellite link data, handover events, ISL data.
    """
    if not os.path.isfile(log_path):
        return None

    encoding = detect_encoding(log_path)

    data = {
        'time': [],
        'sat_links': defaultdict(list),
        'handovers': [],
        'isl_data': [],
        'serving': [],
    }

    # SAT link pattern: "t SATn_RNG=xxx GRND=xxx ELEV=yy DELAY=zzzms LINK=UP GS=name"
    link_pat = re.compile(
        r'(\d+(?:\.\d+)?)\s+SAT(\d+)_RNG=([\d.]+)\s+GRND=([\d.]+)\s+'
        r'ELEV=([\d.]+)\s+DELAY=([\d.]+)ms\s+LINK=(\w+)\s+GS=(\S+)'
    )
    # Handover pattern
    handover_pat = re.compile(
        r'(\d+(?:\.\d+)?)\s+HANDOVER\s+FROM=(\S+)\s+TO=(\S+)\s+ELEV=([\d.]+)'
    )
    # Serving satellite
    serving_pat = re.compile(r'(\d+(?:\.\d+)?)\s+SERVING_SAT=(\S+)\s+ELEV=([\d.]+)')
    # ISL pattern
    isl_pat = re.compile(
        r'(\d+(?:\.\d+)?)\s+RNG_ISL_(PREV|NEXT)=([\d.]+)\s+DELAY_ISL_\w+=([\d.]+)ms'
    )

    with open(log_path, 'r', encoding=encoding, errors='replace') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            m = link_pat.search(line)
            if m:
                t = float(m.group(1))
                sat = f"Sat_{m.group(2)}"
                entry = {
                    't': t, 'rng': float(m.group(3)), 'ground': float(m.group(4)),
                    'elev': float(m.group(5)), 'delay': float(m.group(6)),
                    'link': m.group(7), 'gs': m.group(8)
                }
                data['sat_links'][sat].append(entry)
                if t not in data['time']:
                    data['time'].append(t)
                continue

            m = handover_pat.search(line)
            if m:
                data['handovers'].append({
                    't': float(m.group(1)),
                    'from': m.group(2), 'to': m.group(3),
                    'elev': float(m.group(4))
                })
                continue

            m = serving_pat.search(line)
            if m:
                data['serving'].append({
                    't': float(m.group(1)),
                    'sat': m.group(2), 'elev': float(m.group(3))
                })
                continue

            m = isl_pat.search(line)
            if m:
                data['isl_data'].append({
                    't': float(m.group(1)),
                    'dir': m.group(2),
                    'rng': float(m.group(3)),
                    'delay': float(m.group(4))
                })
                continue

    return data


# ═══════════════════════════════════════════════════════════════════════════════
# 4. DERIVED CALCULATIONS
# ═══════════════════════════════════════════════════════════════════════════════

def compute_elevation(ranges, grounds, sat_alt=550000.0):
    """Elevation angle (deg) from slant range and ground range."""
    return [90.0 if g < 100 else 57.2958 * np.arctan2(sat_alt, max(g, 1))
            for r, g in zip(ranges, grounds)]


def compute_fsl(ranges_m, freq_hz=28e9):
    """Free Space Loss in dB."""
    c = 299792458.0
    wl = c / freq_hz
    return [20 * np.log10(4 * np.pi * r / wl) for r in ranges_m]


def compute_rx_power(fsl_db, tx_pwr_dbm=44.77, tx_gain=25, rx_gain=32, losses=2.0):
    """Pr = Pt + Gt + Gr - FSL - losses (dBm)."""
    return [tx_pwr_dbm + tx_gain + rx_gain - f - losses for f in fsl_db]


# ═══════════════════════════════════════════════════════════════════════════════
# 5. PLOTTING
# ═══════════════════════════════════════════════════════════════════════════════

def plot_leo_comm(times, ranges, grounds, delays, link_states, output_dir, basename='analysis'):
    """Standard LEO comm analysis: 6-panel plot + CSV."""
    if not HAVE_MPL or len(times) < 2:
        print("Skipping plots: matplotlib not available or insufficient data")
        return

    times = np.array(times)
    ranges_km = np.array(ranges) / 1000.0
    grounds_km = np.array(grounds) / 1000.0
    delays_ms = np.array(delays)
    elevs = np.array(compute_elevation(ranges, grounds))
    fsl = np.array(compute_fsl(ranges))
    rx_pwr = np.array(compute_rx_power(fsl))
    link_up = np.array([s == 'UP' for s in link_states])
    link_down = ~link_up

    # 3×2 subplots
    fig, axes = plt.subplots(3, 2, figsize=(14, 10))
    fig.suptitle('LEO Satellite Communication Link Analysis', fontsize=14)

    plots = [
        (axes[0, 0], times, ranges_km, 'b-',
         'Slant Range (km)', 'Slant Range (RNG)',
         link_up, link_down),
        (axes[0, 1], times, grounds_km, 'g-',
         'Ground Range (km)', 'Ground Track Distance (GRND)',
         link_up, link_down),
    ]

    for ax, x, y, style, ylabel, title, lup, ldown in plots:
        ax.plot(x, y, style, linewidth=1.5, alpha=0.7)
        if lup.any():
            ax.scatter(x[lup], y[lup], c='green', s=12, label='Link UP', zorder=5)
        if ldown.any():
            ax.scatter(x[ldown], y[ldown], c='red', s=12, label='Link DOWN', zorder=5)
        ax.set_xlabel('Time (s)')
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

    # Elevation
    ax = axes[1, 0]
    ax.plot(times, elevs, 'r-', linewidth=1.5)
    ax.axhline(y=5, color='gray', linestyle='--', alpha=0.7, label='Min elev (5°)')
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Elevation (deg)')
    ax.set_title('Elevation Angle (computed)')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # Propagation Delay
    ax = axes[1, 1]
    ax.plot(times, delays_ms, 'm-', linewidth=1.5, alpha=0.7)
    if link_up.any():
        ax.scatter(times[link_up], delays_ms[link_up], c='green', s=12, zorder=5)
    if link_down.any():
        ax.scatter(times[link_down], delays_ms[link_down], c='red', s=12, zorder=5)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Delay (ms)')
    ax.set_title('Propagation Delay (DELAY)')
    ax.grid(True, alpha=0.3)

    # FSL
    ax = axes[2, 0]
    ax.plot(times, fsl, 'orange', linewidth=1.5)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('FSL (dB)')
    ax.set_title('Free Space Path Loss @ 28GHz')
    ax.grid(True, alpha=0.3)

    # RX Power
    ax = axes[2, 1]
    ax.plot(times, rx_pwr, 'purple', linewidth=1.5)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('RX Power (dBm)')
    ax.set_title(f'Estimated RX Power (TX: 30W, Gains: {25+32}dBi)')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plot_path = os.path.join(output_dir, f'{basename}.png')
    fig.savefig(plot_path, dpi=150)
    plt.close(fig)
    print(f"  Plot saved: {plot_path}")

    # CSV
    csv_path = os.path.join(output_dir, f'{basename}.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        f.write('Time_s,SlantRange_m,SlantRange_km,GroundRange_m,GroundRange_km,'
                'Elevation_deg,Delay_ms,FSL_dB,RX_Power_dBm,LinkStatus\n')
        for i in range(len(times)):
            f.write(f'{times[i]:.1f},{ranges[i]:.0f},{ranges_km[i]:.1f},'
                    f'{grounds[i]:.0f},{grounds_km[i]:.1f},'
                    f'{elevs[i]:.1f},{delays_ms[i]:.3f},{fsl[i]:.2f},{rx_pwr[i]:.2f},'
                    f'{link_states[i]}\n')
    print(f"  CSV saved: {csv_path}")

    # Summary
    up_count = sum(1 for s in link_states if s == 'UP')
    down_count = len(link_states) - up_count
    print(f"\n  LINK SUMMARY: {up_count}/{len(link_states)} UP ({100*up_count//max(len(link_states),1)}%)")
    print(f"                {down_count}/{len(link_states)} DOWN")
    print(f"  Min delay: {min(delays):.3f} ms")
    print(f"  Max delay: {max(delays):.3f} ms")

    print(f"\n  Output files in {output_dir}/")


def plot_constellation(data, output_dir):
    """Plots for constellation simulation (handover, ISL, elevation)."""
    if not HAVE_MPL or not data or not data['time']:
        print("Skipping constellation plots")
        return

    times = sorted(data['time'])
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']

    # Plot 1: Elevation for all satellite links
    fig1, ax1 = plt.subplots(figsize=(12, 5))
    fig1.suptitle('Constellation: Satellite Elevation Angles', fontsize=13)
    sat_list = sorted(data['sat_links'].keys())
    for i, sat in enumerate(sat_list):
        pts = sorted(data['sat_links'][sat], key=lambda x: x['t'])
        st = np.array([p['t'] for p in pts])
        se = np.array([p['elev'] for p in pts])
        ax1.plot(st, se, color=colors[i % 6], linewidth=0.8, alpha=0.7, label=sat)
    ax1.axhline(y=6, color='gray', linestyle='--', alpha=0.5, label='Min elev 6°')
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Elevation (deg)')
    ax1.legend(fontsize=7, ncol=3)
    ax1.grid(True, alpha=0.3)
    fig1.tight_layout()
    fig1.savefig(os.path.join(output_dir, 'constellation_elevation.png'), dpi=150)
    plt.close(fig1)
    print(f"  Elevation plot: constellation_elevation.png")

    # Plot 2: Handover timeline
    if data['handovers']:
        fig2, ax2 = plt.subplots(figsize=(12, 3))
        sat_names = [f'Sat_{i+1}' for i in range(6)]
        y_map = {s: i+1 for i, s in enumerate(sat_names)}
        y_map['none'] = 0

        serving_times = [s['t'] for s in data['serving']]
        serving_sats = [y_map.get(s['sat'], 0) for s in data['serving']]

        if serving_times:
            ax2.step(serving_times, serving_sats, 'b-', linewidth=2, where='post')

        for ho in data['handovers']:
            y_ho = y_map.get(ho['to'], 0)
            ax2.scatter(ho['t'], y_ho, s=80, c='red', zorder=5)
            ax2.axvline(x=ho['t'], color='red', linestyle='--', alpha=0.5)
            ax2.annotate(f'{ho["from"]}->{ho["to"]}', (ho['t'], y_ho),
                        xytext=(3, 8), textcoords='offset points', fontsize=7, rotation=45)

        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('Serving Satellite')
        ax2.set_yticks(list(range(7)))
        ax2.set_yticklabels(['none'] + sat_names)
        ax2.set_title('Mobile Terminal Handover Timeline')
        ax2.grid(True, alpha=0.3, axis='x')
        fig2.tight_layout()
        fig2.savefig(os.path.join(output_dir, 'constellation_handover.png'), dpi=150)
        plt.close(fig2)
        print(f"  Handover plot: constellation_handover.png")

        print(f"\n  HANDOVER EVENTS ({len(data['handovers'])}):")
        for ho in data['handovers']:
            print(f"    t={ho['t']:4.0f}s: {ho['from']:>8s} -> {ho['to']:<8s} (elev={ho['elev']:.1f}°)")

    # Plot 3: ISL ranges
    if data['isl_data']:
        fig3, ax3 = plt.subplots(figsize=(12, 4))
        isl_times = np.array([d['t'] for d in data['isl_data']])
        isl_rng = np.array([d['rng'] for d in data['isl_data']])
        ax3.plot(isl_times, isl_rng / 1000, 'b.', markersize=2, alpha=0.3)
        ax3.set_xlabel('Time (s)')
        ax3.set_ylabel('ISL Range (km)')
        ax3.set_title('Inter-Satellite Link Ranges (60GHz V-band)')
        ax3.grid(True, alpha=0.3)
        fig3.tight_layout()
        fig3.savefig(os.path.join(output_dir, 'constellation_isl.png'), dpi=150)
        plt.close(fig3)
        print(f"  ISL plot: constellation_isl.png")


# ═══════════════════════════════════════════════════════════════════════════════
# 6. MYSTIC VIEWER
# ═══════════════════════════════════════════════════════════════════════════════

def open_mystic(mystic_exe, work_dir):
    """Find and open .aer file in Mystic."""
    if not mystic_exe or not os.path.isfile(mystic_exe):
        print("  Mystic not available")
        return

    aer_files = glob.glob(os.path.join(work_dir, 'output', '*.aer'))
    if not aer_files:
        print("  No .aer file found")
        return

    aer_path = aer_files[0]
    print(f"\n  Opening Mystic: {aer_path}")
    try:
        if platform.system() == 'Windows':
            os.startfile(aer_path)
        else:
            subprocess.Popen([mystic_exe, aer_path])
    except Exception as e:
        print(f"  Failed to open Mystic: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# 7. ARGUMENTS & MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def parse_args():
    p = argparse.ArgumentParser(
        description='LEO Comm Analysis: auto-find AFSIM -> compile -> run -> plot -> Mystic',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python analyze_leo_comm.py                              # auto everything
  python analyze_leo_comm.py --main leo_comm.txt          # use this main file
  python analyze_leo_comm.py --main leo_constellation.txt  # 6-sat constellation
  python analyze_leo_comm.py --plot-only                   # re-plot existing data
  python analyze_leo_comm.py --afsim-home "C:\\AFSIM2.9"   # set path manually
  python analyze_leo_comm.py --no-mystic                   # skip 3D viewer
  python analyze_leo_comm.py --compile-only                # compile only, no plot
        """
    )
    p.add_argument('--main', default=None,
                   help='Main .txt file (auto-detected from project dir if omitted)')
    p.add_argument('--evt', default=None, help='Path to .evt file (auto-detected if omitted)')
    p.add_argument('--log', default=None, help='Path to simulation .log file (auto-detected if omitted)')
    p.add_argument('--output', default='output', help='Output directory (relative to project dir)')
    p.add_argument('--afsim-home', default=None, help='AFSIM_HOME override')
    p.add_argument('--plot-only', action='store_true', help='Skip compile, only plot existing data')
    p.add_argument('--compile-only', action='store_true', help='Only compile, no plot')
    p.add_argument('--no-mystic', action='store_true', help='Skip opening Mystic')
    return p.parse_args()


def detect_main_file(work_dir):
    """Scan a directory for the main AFSIM .txt input file."""
    # Look for a .txt file that has 'define_path_variable' or 'end_time' or 'include_once'
    # (these are telltale signs of a main config, not a platform/processor include)
    if not os.path.isdir(work_dir):
        return None
    for f in sorted(glob.glob(os.path.join(work_dir, '*.txt'))):
        try:
            with open(f, 'r', encoding='utf-8', errors='replace') as fh:
                content = fh.read(2000)
            if 'define_path_variable' in content or 'end_time' in content.lower():
                return f
        except Exception:
            continue
    # Fallback: any .txt that isn't obviously an include file
    for f in sorted(glob.glob(os.path.join(work_dir, '*.txt'))):
        base = os.path.basename(f).lower()
        if base not in ('setup.txt', 'event_output.txt'):
            return f
    return None


def detect_output_file(work_dir, ext):
    """Scan output/ directory for a file with the given extension."""
    out_dir = os.path.join(work_dir, 'output')
    if not os.path.isdir(out_dir):
        return None
    matches = sorted(glob.glob(os.path.join(out_dir, '*' + ext)))
    # Prefer non-'.' prefixed files (e.g. leo_comm.log over .log)
    named = [m for m in matches if not os.path.basename(m).startswith('.')]
    if named:
        return named[0]
    if matches:
        return matches[0]
    return None


def main():
    args = parse_args()
    start_time = time.time()

    print("=" * 60)
    print("LEO COMMUNICATION LINK ANALYSIS")
    print("=" * 60)
    print("  No hardcoded paths -- all files auto-detected from project directory.")

    # Determine working directory
    work_dir = os.getcwd()

    # Auto-detect main file
    main_file = None
    if args.main:
        main_file = args.main
        if not os.path.isabs(main_file):
            main_file = os.path.join(work_dir, main_file)
    else:
        main_file = detect_main_file(work_dir)

    if main_file:
        work_dir = os.path.dirname(main_file) if os.path.isfile(main_file) else work_dir
        print(f"  Project:   {work_dir}")
        print(f"  Main file: {main_file}")
    else:
        print(f"  Project:   {work_dir}")

    # ── Step 1: Find AFSIM and compile ──
    if not args.plot_only:
        if not main_file:
            print("ERROR: No main .txt file found in current directory.")
            print("  cd to a project directory (contains e.g. leo_comm.txt or leo_constellation.txt)")
            print("  Or specify: --main path/to/your_project.txt")
            sys.exit(1)

        afsim_home = args.afsim_home or os.environ.get('AFSIM_HOME', '')
        mission_exe = None
        mystic_exe = None

        if afsim_home:
            mission_exe = os.path.join(afsim_home, 'bin', 'mission.exe')
            mystic_exe = os.path.join(afsim_home, 'bin', 'mystic.exe')
            if not os.path.isfile(mission_exe):
                print(f"WARNING: mission.exe not found in AFSIM_HOME ({afsim_home})")
                afsim_home, mission_exe, mystic_exe = None, None, None

        if not mission_exe or not os.path.isfile(mission_exe):
            afsim_home, mission_exe, mystic_exe = scan_for_afsim()

        if not mission_exe or not os.path.isfile(mission_exe):
            print("\nERROR: AFSIM not found. Install AFSIM or use --plot-only to re-plot existing data.")
            sys.exit(1)

        os.environ['AFSIM_HOME'] = afsim_home
        print(f"\n  AFSIM_HOME: {afsim_home}")
        print(f"  mission:    {mission_exe}")

        # Compile
        if not compile_and_run(mission_exe, main_file, work_dir, args.output):
            print("\nCompilation failed. Fix errors above and retry.")
            sys.exit(1)
    else:
        mystic_exe = None
        if not main_file:
            # In plot-only mode, auto-detect from current dir even without main file
            work_dir = os.getcwd()

    # ── Step 2: Parse and plot ──
    if not args.compile_only:
        print(f"\n{'=' * 60}")
        print("PARSING OUTPUT")
        print(f"{'=' * 60}")

        output_dir = os.path.join(work_dir, args.output)

        # Auto-detect log and evt files (not hardcoded to leo_comm)
        log_path = args.log or detect_output_file(work_dir, '.log')
        evt_path = args.evt or detect_output_file(work_dir, '.evt')

        # Check if this is constellation output (has HANDOVER/SERVING_SAT)
        is_constellation = False
        if os.path.isfile(log_path):
            enc = detect_encoding(log_path)
            with open(log_path, 'r', encoding=enc, errors='replace') as f:
                sample = f.read(5000)
                if 'HANDOVER' in sample or 'SERVING_SAT' in sample or 'ISL_PREV' in sample:
                    is_constellation = True

        if is_constellation:
            # Constellation analysis
            data = parse_constellation_log(log_path)
            if data and data['time']:
                print(f"  Detected: Constellation simulation (6-sat + gateways + terminal)")
                print(f"  Data points: {len(data['time'])}")
                print(f"  Satellites: {len(data['sat_links'])}")
                print(f"  Handovers: {len(data['handovers'])}")
                plot_constellation(data, output_dir)
            else:
                print("  No constellation data found in log.")
        else:
            # Standard LEO comm analysis
            times, ranges, grounds, delays, link_states = parse_links(evt_path)
            if not times:
                times, ranges, grounds, delays, link_states = parse_links(log_path)

            if times:
                print(f"  Parsed {len(times)} data points")
                print(f"  Time range: {times[0]:.0f}s - {times[-1]:.0f}s")
                print(f"  Range: {ranges[-1]/1000:.0f}km - {ranges[0]/1000:.0f}km")
                base = os.path.splitext(os.path.basename(main_file))[0] if main_file else 'analysis'
                plot_leo_comm(times, ranges, grounds, delays, link_states, output_dir, base)
            else:
                print("  No link data found in output files.")

        # ── Step 3: Open Mystic ──
        if not args.no_mystic and not args.plot_only:
            print(f"\n{'=' * 60}")
            print("MYSTIC 3D VIEWER")
            print(f"{'=' * 60}")
            open_mystic(mystic_exe, work_dir)

    elapsed = time.time() - start_time
    print(f"\nTotal time: {elapsed:.1f}s")
    print("Done.")


if __name__ == '__main__':
    main()
