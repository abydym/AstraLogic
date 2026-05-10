#!/usr/bin/env python3
"""
EVT Full Data Extractor
========================
Reads ANY AFSIM .evt file, extracts ALL key:value or key=value pairs,
dumps to a complete CSV, and plots every numeric column.

Supports:
  - KEY=VALUE format   (e.g., RNG=826091 LINK=UP)
  - KEY: VALUE format  (e.g., Type: LEO_SAT, LLA: 27:00:00.00n 110:00:00.00e)
  - HH:MM:SS.S time format (converts to seconds)
  - Multi-line continuation with trailing backslash
  - DMS latitude/longitude parsing

Usage:
    python parse_evt_full.py output/leo_comm.evt
    python parse_evt_full.py output/leo_comm.evt -o leo_full.csv
    python parse_evt_full.py output/leo_comm.evt --no-plot
"""

import os, sys, re, argparse
from collections import defaultdict

# Optional deps
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    HAVE_MPL = True
except ImportError:
    HAVE_MPL = False


# ── Time conversion ──────────────────────────────────────────────────────────

def time_to_seconds(timestr):
    """Convert HH:MM:SS.S or HH:MM:SS to total seconds. Also handles bare float."""
    if not timestr:
        return None
    timestr = timestr.strip()
    try:
        return float(timestr)
    except ValueError:
        pass
    try:
        parts = timestr.split(':')
        if len(parts) == 3:
            return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
        elif len(parts) == 2:
            return float(parts[0]) * 60 + float(parts[1])
    except (ValueError, IndexError):
        pass
    return None


# ── Known AFSIM event keys (order of greed matters) ─────────────────────────

KNOWN_KEYS = [
    'Type',
    'Side',
    'Comm',
    'Heading',
    'Pitch',
    'Roll',
    'Speed',
    'Acceleration',
    'Ps',
    'LLA',
    'RNG',
    'GRND',
    'DELAY',
    'LINK',
    'SNR',
    'BER',
    'Freq',
    'Bandwidth',
    'TxPower',
    'RxPower',
    'Gain',
    'Lat',
    'Lon',
    'Alt',
    'Az',
    'El',
    'Range',
    'Signal',
    'Noise',
    'Loss',
]

# Build regex: (\bKEY1|KEY2|...):\s*(.*?)(?=\s+\b(KEY1|KEY2|...):|\s*$)
# Greedy match between known keys
def _build_kv_pattern():
    escaped = [re.escape(k) for k in KNOWN_KEYS]
    alt = '|'.join(escaped)
    # Match: KnownKey: ... until next KnownKey: or end of string
    return re.compile(
        r'\b(' + alt + r'):\s*'              # key + colon
        r'(.*?)(?=\s+\b(?:' + alt + r'):|\s*$)',  # value (non-greedy to next key)
        re.DOTALL
    )

KV_COLON_RE = _build_kv_pattern()
KV_EQ_RE = re.compile(r'(\w+)=([^\s]+)')

# Event type pattern (bare uppercase tokens like PLATFORM_ADDED)
EVENT_RE = re.compile(r'^[A-Z][A-Z_]+(?:\s+[A-Z][A-Z_]+)*')
TIME_RE = re.compile(r'^(\d[\d:.]*)\s+')


# ── DMS parsing ─────────────────────────────────────────────────────────────

def parse_dms(dms_str):
    """Parse latitude/longitude in DMS format like '27:00:00.00n' to decimal degrees."""
    if not dms_str:
        return None
    m = re.match(r'(\d+):(\d+):([\d.]+)\s*([nswe])', dms_str.strip(), re.IGNORECASE)
    if m:
        deg = float(m.group(1))
        minute = float(m.group(2))
        sec = float(m.group(3))
        hemi = m.group(4).lower()
        dec = deg + minute / 60.0 + sec / 3600.0
        if hemi in ('s', 'w'):
            dec = -dec
        return dec
    return None


# ── Parsing ──────────────────────────────────────────────────────────────────

def detect_encoding(path):
    """Detect UTF-16 vs UTF-8 encoding by sniffing BOM."""
    with open(path, 'rb') as f:
        head = f.read(4)
    if head[:2] in (b'\xff\xfe', b'\xfe\xff'):
        return 'utf-16'
    return 'utf-8'


def parse_log_file(log_path):
    """
    Parse a .log file for script processor writeln() output.
    Extracts all KEY=VALUE pairs (e.g. RNG=826091 GRND=591101 DELAY=2.75554ms LINK=UP).
    """
    if not os.path.isfile(log_path):
        return [], []

    rows = []
    all_fields = []
    field_set = set()

    kv_re = re.compile(r'(\w+)=([^\s]+)')
    time_re = re.compile(r'^(\d+(?:\.\d+)?)\s+')
    encoding = detect_encoding(log_path)

    with open(log_path, 'r', encoding=encoding, errors='replace') as f:
        for line in f:
            line = line.strip()
            # Skip non-data lines
            if not line or not line[0].isdigit():
                continue
            if 'RNG=' not in line and 'GRND=' not in line:
                continue

            row = {}

            # Extract time
            tm = time_re.match(line)
            if tm:
                row['TIME'] = tm.group(1)
                rest = line[tm.end():].strip()
            else:
                continue

            # Extract all KEY=VALUE
            pairs = kv_re.findall(rest)
            for key, val in pairs:
                row[key] = val

            if row:
                for key in row:
                    if key not in field_set:
                        field_set.add(key)
                        all_fields.append(key)
                rows.append(row)

    if rows:
        if 'TIME' in field_set:
            all_fields.remove('TIME')
            all_fields.insert(0, 'TIME')
        print(f"  Log file parsed: {len(rows)} data points, {len(all_fields)} fields")

    return rows, all_fields


def parse_evt_all(evt_path):
    """
    Parse EVERY line in the .evt file.
    """
    if not os.path.isfile(evt_path):
        print(f"WARNING: File not found: {evt_path}")
        return [], []

    # --- Step 1: join continuation lines ---
    raw_lines = []
    with open(evt_path, 'r', encoding='utf-8', errors='replace') as f:
        buf = ''
        for line in f:
            line = line.rstrip('\n\r')
            if line.endswith('\\'):
                buf += line[:-1] + ' '
            else:
                raw_lines.append(buf + line)
                buf = ''
        if buf:
            raw_lines.append(buf)

    rows = []
    all_fields = []
    field_set = set()
    line_count = 0
    skipped = 0

    for line in raw_lines:
        line = line.strip()
        line_count += 1
        if not line:
            continue

        row = {}

        # Extract time (leading timestamp)
        tm = TIME_RE.match(line)
        t_sec = None
        if tm:
            t_sec = time_to_seconds(tm.group(1))
            rest = line[tm.end():].strip()
        else:
            rest = line

        # Extract event type (first uppercase tokens)
        evt_m = EVENT_RE.match(rest)
        if evt_m:
            row['EVENT'] = evt_m.group(0).strip()
            rest = rest[evt_m.end():].strip()

        # Extract entity name (next token before first KnownKey:)
        # e.g. "Leo_Satellite_1 Type:" → entity is "Leo_Satellite_1"
        entity_m = re.match(r'(\S+)\s+', rest)
        if entity_m:
            row['Entity'] = entity_m.group(1)
            rest = rest[entity_m.end():].strip()

        # Extract KEY=VALUE pairs (e.g. RNG=826091)
        eq_pairs = KV_EQ_RE.findall(rest)
        for key, val in eq_pairs:
            row[key] = val
            if key not in field_set:
                field_set.add(key)
                all_fields.append(key)

        # Extract KEY: VALUE pairs (e.g. Type: LEO_SAT)
        col_pairs = KV_COLON_RE.findall(rest)
        for key, val in col_pairs:
            val = val.strip()
            if key not in row:
                row[key] = val
            if key not in field_set:
                field_set.add(key)
                all_fields.append(key)

        # Special parsing: extract lat/lon from LLA field
        if 'LLA' in row:
            lla_val = row['LLA']
            # Format: "27:00:00.00n 110:00:00.00e 550000 m"
            parts = lla_val.split()
            if len(parts) >= 2:
                lat_dec = parse_dms(parts[0])
                lon_dec = parse_dms(parts[1])
                if lat_dec is not None:
                    row['LAT'] = str(lat_dec)
                if lon_dec is not None:
                    row['LON'] = str(lon_dec)
            if len(parts) >= 3:
                # Altitude: "550000 m" or "550000"
                alt_val = parts[2].strip()
                try:
                    row['ALT'] = str(float(alt_val))
                except ValueError:
                    pass

        if t_sec is not None:
            row['TIME'] = str(t_sec)

        if not row and t_sec is None:
            skipped += 1
            continue

        # Register any fields that were missed in first pass
        for key in row:
            if key not in field_set:
                field_set.add(key)
                all_fields.append(key)

        rows.append(row)

    # Sort fields consistently
    priority = ['TIME', 'EVENT', 'Entity', 'LAT', 'LON', 'ALT']
    ordered = [f for f in priority if f in field_set]
    ordered += [f for f in all_fields if f not in priority]
    all_fields[:] = ordered

    print(f"  Lines read: {line_count}")
    print(f"  Events extracted: {len(rows)}")
    print(f"  Lines skipped: {skipped}")
    print(f"  Fields found: {len(all_fields)}")
    print(f"  Fields: {', '.join(all_fields)}")

    return rows, all_fields


# ── Value helpers ────────────────────────────────────────────────────────────

def try_float(val):
    """Try to convert a value string to float, handling units and DMS."""
    if not val:
        return None
    val = val.strip()
    # Remove common trailing units
    val_clean = re.sub(
        r'\s*(ms|km|m|dB|dBm|dBi|deg|rad|knots|kHz|MHz|GHz|Hz|W|mW|us|ns|s)\s*$',
        '', val, flags=re.IGNORECASE
    ).strip()
    # Remove brackets and vector stuff: "7202.222 m/s * [ 0.604 0.797 0.000 ]"
    val_clean = re.sub(r'\s*\*\s*\[.*?\]', '', val_clean).strip()
    # Try DMS
    dms = parse_dms(val_clean)
    if dms is not None:
        return dms
    # Try plain float
    try:
        return float(val_clean)
    except ValueError:
        pass
    # Try with leading parts (e.g. "ka_downlink" → no)
    return None


def write_csv(rows, fields, csv_path):
    """Write ALL data to CSV."""
    os.makedirs(os.path.dirname(csv_path) or '.', exist_ok=True)
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        f.write(','.join(fields) + '\n')
        for row in rows:
            vals = []
            for field in fields:
                v = row.get(field, '')
                tv = try_float(v)
                if tv is not None:
                    vals.append(f'{tv:.6g}')
                else:
                    ev = v.replace('"', '""')
                    if ',' in v or '"' in v:
                        vals.append(f'"{ev}"')
                    else:
                        vals.append(v)
            f.write(','.join(vals) + '\n')
    print(f"\n  CSV saved: {csv_path}")
    print(f"  Rows: {len(rows)}, Columns: {len(fields)}")


# ── Plotting ─────────────────────────────────────────────────────────────────

def get_numeric_columns(rows, fields):
    counts = defaultdict(int)
    numeric_counts = defaultdict(int)
    for row in rows:
        for fld in fields:
            v = row.get(fld, '')
            if v:
                counts[fld] += 1
                if try_float(v) is not None:
                    numeric_counts[fld] += 1
    return [f for f in fields
            if counts.get(f, 0) >= 2
            and numeric_counts.get(f, 0) / max(counts.get(f, 0), 1) >= 0.5], counts


def plot_all(rows, fields, csv_path):
    if not HAVE_MPL:
        print("Skipping plots: matplotlib/numpy not available")
        return
    if len(rows) < 2:
        print("Skipping plots: <2 data points")
        return

    numeric_cols, _ = get_numeric_columns(rows, fields)
    has_time = 'TIME' in numeric_cols
    if has_time:
        numeric_cols.remove('TIME')
    if not numeric_cols:
        print("No numeric columns to plot")
        return

    data = {col: [] for col in fields}
    x_vals = []
    for row in rows:
        tv = try_float(row.get('TIME', ''))
        x_vals.append(tv if tv is not None else len(x_vals))
        for col in fields:
            v = row.get(col, '')
            tv2 = try_float(v)
            data[col].append(tv2 if tv2 is not None else float('nan'))

    x_arr = np.array(x_vals)
    n_plots = len(numeric_cols)
    n_cols = min(3, n_plots)
    n_rows = max(1, (n_plots + n_cols - 1) // n_cols)

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(6 * n_cols, 4 * n_rows), squeeze=False)
    base_name = os.path.basename(csv_path).replace('.csv', '')
    fig.suptitle(f'EVT Full Data: {base_name}', fontsize=14)

    for i, col in enumerate(numeric_cols):
        ax = axes[i // n_cols][i % n_cols]
        y = np.array(data[col])
        mask = np.isfinite(y)
        if mask.sum() > 1:
            ax.plot(x_arr[mask], y[mask], linewidth=1.5, marker='o', markersize=4)
        ax.set_xlabel('Time (s)' if has_time else 'Event Index')
        ax.set_ylabel(col)
        ax.set_title(col)
        ax.grid(True, alpha=0.3)

    for i in range(n_plots, n_rows * n_cols):
        axes[i // n_cols][i % n_cols].set_visible(False)

    plt.tight_layout()
    plot_path = csv_path.replace('.csv', '_plots.png')
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    print(f"  Plots saved: {plot_path}")
    plt.close(fig)
    print(f"  Plotted {len(numeric_cols)} columns: {', '.join(numeric_cols)}")

    return plot_path


def print_summary(rows, fields):
    print(f"\n{'=' * 60}")
    print("EVT DATA SUMMARY")
    print(f"{'=' * 60}")
    print(f"  Total events: {len(rows)}")
    print(f"  Total fields: {len(fields)}")

    if 'EVENT' in fields:
        from collections import Counter
        tc = Counter(r.get('EVENT', '') for r in rows)
        print(f"\n  By EVENT type:")
        for t, c in tc.most_common():
            print(f"    {t}: {c}")

    print(f"\n  Fields:")
    for fld in fields:
        vals = set()
        num = 0
        for r in rows:
            v = r.get(fld, '')
            if v:
                vals.add(v)
                if try_float(v) is not None:
                    num += 1
        kind = 'numeric' if num >= len(rows) * 0.4 else 'text'
        print(f"    {fld}: {len(vals)} unique values ({kind})")


# ── Main ─────────────────────────────────────────────────────────────────────

def merge_rows(rows_a, fields_a, rows_b, fields_b):
    """Merge two row sets, union their fields."""
    if not rows_b:
        return rows_a, fields_a
    if not rows_a:
        return rows_b, fields_b

    # Union of fields (preserve order: A first, then new ones from B)
    field_set = set(fields_a)
    merged_fields = list(fields_a)
    for f in fields_b:
        if f not in field_set:
            field_set.add(f)
            merged_fields.append(f)

    # Combine all rows
    all_rows = rows_a + rows_b
    return all_rows, merged_fields


def main():
    parser = argparse.ArgumentParser(
        description='Extract ALL data from any AFSIM .evt + .log file to CSV + plots'
    )
    parser.add_argument('evt_file', help='Path to .evt file')
    parser.add_argument('--log', default=None, help='Path to .log file (mission stdout)')
    parser.add_argument('-o', '--output', default=None, help='Output CSV path')
    parser.add_argument('--no-plot', action='store_true', help='Skip plotting')
    parser.add_argument('--skip-summary', action='store_true', help='Skip console summary')

    args = parser.parse_args()

    # Auto-detect .log path if not specified
    if not args.log:
        base = args.evt_file
        for ext in ['.evt', '.csv', '.aer']:
            base = base.replace(ext, '')
        args.log = base + '.log'

    if not args.output:
        args.output = args.evt_file.replace('.evt', '_full.csv')

    print(f"\n{'=' * 60}")
    print("EVT + LOG FULL EXTRACTOR")
    print(f"{'=' * 60}")
    print(f"  EVT input: {args.evt_file}")
    print(f"  LOG input: {args.log}")
    print(f"  CSV output: {args.output}")

    # Parse both sources
    evt_rows, evt_fields = parse_evt_all(args.evt_file)
    log_rows, log_fields = parse_log_file(args.log)

    # Merge
    rows, fields = merge_rows(evt_rows, evt_fields, log_rows, log_fields)

    if not rows:
        print("ERROR: No data extracted.")
        sys.exit(1)

    write_csv(rows, fields, args.output)

    if not args.skip_summary:
        print_summary(rows, fields)

    if not args.no_plot:
        plot_all(rows, fields, args.output)

    print(f"\nDone.\n")


if __name__ == '__main__':
    main()
