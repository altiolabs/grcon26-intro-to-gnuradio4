#include <gnuradio-4.0/PluginLoader.hpp>
#include <algorithm>
#include <iostream>

int main() {
    constexpr std::string_view name = "gr::intro::Gain<float32>";
    auto& loader = gr::globalPluginLoader();
    for (const auto& [path, reason] : loader.failedPlugins()) {
        if (path.find("GrIntroBlocksShared") != std::string::npos) {
            std::cerr << "Intro plugin rejected: " << reason << '\n';
            return 1;
        }
    }
    for (const auto& plugin : loader.plugins()) {
        const auto names = plugin->availableBlocks();
        if (std::ranges::find(names, name) != names.end() &&
            plugin->createBlock(name, {}) && loader.instantiate(name, {})) {
            std::cout << "PASS: installed plugin advertises and constructs " << name << '\n';
            return 0;
        }
    }
    std::cerr << "No accepted plugin constructs " << name << '\n';
    return 1;
}
