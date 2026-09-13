#!/usr/bin/env python3
"""Prepare a machine-local Studio graph using the bundled deterministic input."""
from pathlib import Path
import argparse
import json
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--absolute', action='store_true', help='Compatibility option; absolute paths are always used')
parser.add_argument('--transport', choices=('websocket', 'http_poll'),
                    help='Override the saved Studio plot transport')
args = parser.parse_args()
data = ROOT / 'assets/demo-data/two-tone.f32'
source = ROOT / 'examples/studio/reference.gr4s'
if not data.is_file():
    raise SystemExit(f'Missing bundled input: {data}')

doc = json.loads(source.read_text())
file_node = next(
    (item for item in doc['graph']['nodes']
     if item['blockType'] == 'gr::blocks::fileio::BasicFileSource<float32>'),
    None,
)
if file_node is None:
    raise SystemExit(f'No float32 BasicFileSource in {source}')
file_node['parameters']['file_name']['value'] = str(data)

if args.transport:
    endpoint_scheme = 'ws' if args.transport == 'websocket' else 'http'
    for item in doc['graph']['nodes']:
        parameters = item.get('parameters', {})
        if not item['blockType'].startswith('gr::studio::') or 'transport' not in parameters:
            continue
        parameters['transport']['value'] = args.transport
        endpoint = parameters.get('endpoint')
        if endpoint:
            parts = urlsplit(str(endpoint['value']))
            endpoint['value'] = urlunsplit(
                (endpoint_scheme, parts.netloc, parts.path, parts.query, parts.fragment)
            )

dest = ROOT / '.work/reference.gr4s'
dest.parent.mkdir(parents=True,exist_ok=True)
dest.write_text(json.dumps(doc,indent=2)+'\n')
print(dest)
