#include <gnuradio-4.0/Plugin.hpp>
#include <gnuradio-4.0/GrIntroBlocks.hpp>

GR_PLUGIN("GNU Radio 4 Intro", "GNU Radio", "MIT", "4.0.0")

namespace {
const auto registered = gr::blocklib::initGrIntroBlocks(grPluginInstance());
}
