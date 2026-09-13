#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
if [[ -z "${GR4_PREFIX:-}" ]]; then
  echo 'Activate the prebuilt GR4 SDK and select its compiler first (see README).' >&2
  exit 1
fi
mkdir -p .work
if [[ $# -gt 1 || ( $# -eq 1 && "$1" != '--studio' ) ]]; then
  echo 'Usage: bash tests/validate-demos.sh [--studio]' >&2
  exit 2
fi
cmake -S examples -B .work/build -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH="$GR4_PREFIX"
cmake --build .work/build --parallel "${WORKSHOP_BUILD_JOBS:-2}"
ctest --test-dir .work/build --output-on-failure
cmake -S examples/oot-demo -B .work/oot-demo/build \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_PREFIX_PATH="$GR4_PREFIX" \
  -DCMAKE_INSTALL_LIBDIR=lib \
  -DCMAKE_INSTALL_PREFIX="$PWD/.work/oot-demo/install"
cmake --build .work/oot-demo/build --parallel "${WORKSHOP_BUILD_JOBS:-2}"
cmake --install .work/oot-demo/build
GNURADIO4_PLUGIN_DIRECTORIES="$PWD/.work/oot-demo/install/lib/gnuradio-4/plugins" \
  .work/oot-demo/build/intro-plugin-check
python3 - <<'PY'
import subprocess
for output in ('.work/filtered.f32', '.work/filtered-repeat.f32'):
    subprocess.run(['.work/build/reference', 'assets/demo-data/two-tone.f32', output],
                   check=True, timeout=30)
PY
cmp .work/filtered.f32 .work/filtered-repeat.f32
python3 scripts/check-output.py .work/filtered.f32
if [[ "${1:-}" == '--studio' ]]; then
  python3 tests/check-studio.py "${STUDIO_URL:-http://127.0.0.1:18080}"
fi
