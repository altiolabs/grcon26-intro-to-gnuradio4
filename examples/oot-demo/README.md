# Minimal GNU Radio 4 OOT block

This standalone CMake project builds one discoverable block:
`gr::intro::Gain<float32>`. Its only setting is the linear `gain`, initially 2.

From the workshop root, first activate the GNU Radio 4 SDK, then build and
install the module into the workshop-local `.work` directory:

```bash
cmake -S examples/oot-demo -B .work/oot-demo/build \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_LIBDIR=lib \
  -DCMAKE_INSTALL_PREFIX="$PWD/.work/oot-demo/install"
cmake --build .work/oot-demo/build --parallel 2
cmake --install .work/oot-demo/build
```

Launch Studio with that local plugin directory included:

```bash
GNURADIO4_PLUGIN_DIRECTORIES="$PWD/.work/oot-demo/install/lib/gnuradio-4/plugins:${GNURADIO4_PLUGIN_DIRECTORIES:-}" gr4-studio
```

Search the Studio block catalog for `intro` or `Gain`. The catalog ID is
`gr::intro::Gain<float32>`, with float input/output ports and an editable
`gain` parameter. Studio's control-plane process discovers plugins only at
startup, so restart it after rebuilding the module.

Use the SDK/compiler setup in the [workshop README](../../README.md).
`plugin.cpp` supplies the runtime plugin entry points and registers the generated
factories with the plugin instance. The local plugin may be a `.so` on Linux or
a `.dylib` on macOS. The `intro-plugin-check` executable is used by the
[maintainer checks](../../tests/README.md) to verify loading and construction
without linking the OOT directly.
