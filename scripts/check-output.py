#!/usr/bin/env python3
"""Validate float32 output and write a local SVG using only the standard library."""
import argparse
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]


def read_samples(path):
    data = path.read_bytes()
    if len(data) != 8192 * 4:
        raise ValueError(f'{path}: expected 8192 float32 samples, got {len(data)} bytes')
    values = struct.unpack('<8192f', data)
    if not all(math.isfinite(value) for value in values):
        raise ValueError(f'{path}: non-finite samples')
    return values


def amplitude(values, hz):
    values = values[1024:]  # Discard startup transient; retain whole periods.
    real = sum(value * math.cos(2 * math.pi * hz * n / 8192)
               for n, value in enumerate(values))
    imag = sum(value * math.sin(2 * math.pi * hz * n / 8192)
               for n, value in enumerate(values))
    return 2 * math.hypot(real, imag) / len(values)


def write_plot(source, output, path):
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="500" viewBox="0 0 1000 500">',
           '<rect width="1000" height="500" fill="#fafcfd"/>',
           '<g font-family="sans-serif" font-size="18" fill="#123f58">']
    for values, title, center, color in (
            (source, 'Input: 128 Hz + 2048 Hz', 145, '#006b8f'),
            (output, 'Output: low-pass at 512 Hz', 355, '#ef7825')):
        svg.append(f'<text x="70" y="{center - 95}">{title}</text>')
        svg.append(f'<path d="M70 {center - 80} V{center + 80} H970" fill="none" stroke="#80909a"/>')
        svg.append(f'<path d="M70 {center} H970" stroke="#ccd6dc"/>')
        for value in (-1, 0, 1):
            svg.append(f'<text x="30" y="{center - value * 75 + 6}">{value}</text>')
        points = ' '.join(f'{70 + n * 900 / 255:.2f},{center - value * 75:.2f}'
                          for n, value in enumerate(values[-256:]))
        svg.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2"/>')
    for ms in (0, 10, 20, 30):
        svg.append(f'<text x="{70 + ms * 8192 / 1000 * 900 / 255:.2f}" y="460">{ms}</text>')
    svg.extend(['<text x="460" y="490">Time (ms)</text>', '</g></svg>'])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(svg) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--plot', type=Path, default=ROOT / '.work/measured-result.svg')
    args = parser.parse_args()
    source = read_samples(ROOT / 'assets/demo-data/two-tone.f32')
    output = read_samples(args.output)
    low, high = (amplitude(output, hz) / amplitude(source, hz) for hz in (128, 2048))
    if not 0.97 < low < 1.03 or not high < 0.032:
        raise ValueError(f'Unexpected filter gains: 128 Hz={low:.6f}, 2048 Hz={high:.6f}')
    print(f'PASS: 8192 samples; gain at 128 Hz={low:.6f}; at 2048 Hz={high:.6f}')
    write_plot(source, output, args.plot)
    print(f'Wrote {args.plot}')


if __name__ == '__main__':
    main()
