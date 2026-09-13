# Intro to GNU Radio 4 — GRCon26

Hands-on examples for Josh Morman's introductory GNU Radio 4 workshop:
run a graph in Studio, build its C++ equivalent, and create a loadable block.

This repository is self-contained. Use an installed GNU Radio 4 development
SDK with Studio, the standard blocks, and the SDK's compatible C++23 compiler.
The development environment needs CMake 3.27+, a build tool (Make or Ninja),
and Python 3. Python helpers use only the standard library. There are no
additional Python/Node packages, GR3 installation, source checkouts, or sibling
repositories to install.

## Start here

Activate your installed SDK using its supplied activation script, then run the
commands below from this repository root. Activation must expose
`GR4_PREFIX`, `gr4-studio`, and the SDK's library/plugin paths.

```bash
source /path/to/your/sdk/activate.sh
mkdir -p .work
gr4-studio
```

The activation script's location depends on how your SDK was packaged.
Open `examples/studio/reference.gr4s` in Studio and set its input file path as
described below. Save your working graph under `.work/`, which also holds build
outputs and results.

For the C++ exercises, use the compiler and standard library your SDK was built
with. If activation does not select it, set `CXX` before the first build:

```bash
export CXX=/path/to/sdk-compatible/clang++
```

This especially applies on macos e.g. using Homebrew LLVM 23.1.0. On that setup,
`CXX=/opt/homebrew/opt/llvm/bin/clang++`; the system Apple Clang is a different
toolchain.

## 1. Explore a graph in Studio

Source: [reference.gr4s](examples/studio/reference.gr4s).

The input file contains 8192 little-endian float32 samples: a 128 Hz tone plus
a 2048 Hz tone at 8192 samples/second. Studio adds a little uniform noise, then
applies a low-pass filter with a 512 Hz cutoff.

```text
File ──┐
       ├─ Add ─┬─ Lowpass ─┬─ Output time plot
Noise ─┘      │           └─ Output spectrum
              ├─ Input time plot
              └─ Input spectrum
```

From a terminal at the repository root, print the absolute input path:

```bash
printf '%s\n' "$PWD/assets/demo-data/two-tone.f32"
```

1. Open `examples/studio/reference.gr4s`. Use **Fit view** if necessary.
2. Double-click the **File** source and set `file_name` to the absolute path
   printed above. Keep `repeat=true`. Studio's backend may have a different
   working directory, so the bundled relative path may not resolve.
3. Use **Save As** to save your working copy as `.work/reference.gr4s` inside
   this repository, preserving the bundled example.
4. Click **Run**, complete any save prompt, and open **In-app** to see the
   four plots.
5. Move **Low-pass cutoff (Hz)** from 512 to 3072. The high-frequency component
   should return in the output. Restore the cutoff to 512.
6. Return to **Graph** and inspect the filter's ports, sample type, and settings.
7. Stop the graph when finished.

Optional convenience: `python3 scripts/prepare-demo.py` creates
`.work/reference.gr4s` with the absolute input path already set. The manual
workflow above does not require this helper.

A Run submits a snapshot of the graph. Canvas edits take effect after stopping
and running again; the cutoff slider changes the running session directly.
The repeating file source is unpaced and can use a CPU core. Sample rate
describes the signal, not wall-clock pacing; repeating waveforms can look
stationary.

To reconstruct the graph, use these catalog types:

| Instance | Catalog type | Settings |
| --- | --- | --- |
| File | `gr::blocks::fileio::BasicFileSource<float32>` | Absolute input path, `repeat=true` |
| Noise | `gr::blocks::basic::SignalGenerator<float32>` | `signal_type=UniformNoise`, `amplitude=0.1`, `sample_rate=8192` |
| Add | `gr::blocks::math::Add<float32>` | `n_inputs=2` |
| Lowpass | `gr::blocks::filter::BasicFilter<float32>` | `sample_rate=8192`, `f_low=512` |
| Time plots | `gr::studio::StudioSeriesSink<float32>` | `window_size=1024`, `update_ms=100` |
| Spectra | `gr::studio::StudioPowerSpectrumSink<float32>` | `fft_size=1024`, `sample_rate=8192` |

Use the bundled graph as the connection/layout reference. Time-series sinks
use input port `in#0`; spectrum sinks use `in`. Keep `websocket` transport.
Studio manages the stream endpoints. The Cutoff panel binds to `Lowpass.f_low`
with range 256–3072 and step 256.

## 2. Run the equivalent C++ graph

Source: [main.cpp](examples/static-flowgraph/main.cpp).

```bash
cmake -S examples -B .work/build -DCMAKE_BUILD_TYPE=Release
cmake --build .work/build --parallel 2
.work/build/reference assets/demo-data/two-tone.f32 .work/filtered.f32
python3 scripts/check-output.py .work/filtered.f32
```

Expect 8192 finite output samples, approximately unity gain at 128 Hz, and
more than 30 dB suppression at 2048 Hz. Open `.work/measured-result.svg` in a
browser to compare input and output. The finite C++ graph omits Studio's noise
so the numeric check is repeatable.

CMake finds the installed SDK through the activation environment. The configure
command selects the sources and build directory; the build command compiles
them. CMake uses its default build tool, or you can select Ninja with `-G Ninja`
on the first configure.

Read the source to identify block creation, connections, and scheduler execution.
Try a different filter cutoff and observe the output; the supplied checker
specifically tests the original 512 Hz configuration.

This executable uses the installed SDK and its libraries. It runs without Studio
but is not a fully static binary.

## 3. Declare a block

Source: [main.cpp](examples/block-demo/main.cpp).

```bash
cmake -S examples -B .work/build -DCMAKE_BUILD_TYPE=Release
cmake --build .work/build --target gain-teaser --parallel 2
.work/build/gain-teaser
```

This example declares input/output ports and a `processOne()` operation that
multiplies by two. It checks direct calls, then runs the block in a
`CountingSource → Gain → TagSink` graph. Expect the scheduled output
`2, 4, 6` for input `1, 2, 3`.

The factor is fixed in this example. The next exercise exposes it as an
editable setting and packages the block for runtime discovery.

## 4. Build and load an out-of-tree block

Source and details: [examples/oot-demo](examples/oot-demo/README.md).

```bash
cmake -S examples/oot-demo -B .work/oot-demo/build \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_LIBDIR=lib \
  -DCMAKE_INSTALL_PREFIX="$PWD/.work/oot-demo/install"
cmake --build .work/oot-demo/build --parallel 2
cmake --install .work/oot-demo/build
GNURADIO4_PLUGIN_DIRECTORIES="$PWD/.work/oot-demo/install/lib/gnuradio-4/plugins:${GNURADIO4_PLUGIN_DIRECTORIES:-}" gr4-studio
```

Search the Studio catalog for `intro` or `Gain`. The block
`gr::intro::Gain<float32>` exposes an editable `gain`, initially 2.
Try inserting it between Add and Lowpass in the reference graph, then change
gain and run again to see the output scale.

The install prefix keeps the module under `.work/oot-demo/install`. The
`GNURADIO4_PLUGIN_DIRECTORIES` setting adds that module to the SDK's plugin
search path for this launch. Restart Studio after rebuilding so its backend
discovers the updated plugin.

Automated checks for workshop maintenance are documented in [tests/](tests/README.md).

## Repository layout

- `examples/studio/`: portable Studio graph.
- `examples/static-flowgraph/`: file → filter → file C++ graph.
- `examples/block-demo/`: block declaration and scheduled execution.
- `examples/oot-demo/`: standalone SDK-consuming plugin project.
- `assets/demo-data/`: bundled input shared by Studio and C++.
- `scripts/`: check/plot C++ output and optionally prepare a local Studio graph.
- `tests/`: automated build and runtime checks for maintainers.
- `.work/`: ignored generated graphs, builds, plugin installs, and results.
