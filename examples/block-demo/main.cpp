#include <gnuradio-4.0/Block.hpp>
#include <gnuradio-4.0/BlockRegistry.hpp>
#include <gnuradio-4.0/Graph.hpp>
#include <gnuradio-4.0/Scheduler.hpp>
#include <gnuradio-4.0/testing/NullSources.hpp>
#include <gnuradio-4.0/testing/TagMonitors.hpp>
#include <algorithm>
#include <array>
#include <iostream>

namespace gr::blocks::tutorial {
struct Gain : gr::Block<Gain> {
    using gr::Block<Gain>::Block;
    using Description = gr::Doc<"Multiply each input sample by two.">;

    gr::PortIn<float> in;
    gr::PortOut<float> out;
    float factor = 2.0f;
    GR_MAKE_REFLECTABLE(Gain, in, out);

    [[nodiscard]] constexpr float processOne(float input) const noexcept {
        return input * factor;
    }
};
} // namespace gr::blocks::tutorial
GR_REGISTER_BLOCK(gr::blocks::tutorial::Gain)

template<typename Result>
void checked(Result&& result) {
    if (!result) throw gr::exception(result.error().message);
}

int main() try {
    constexpr std::array input{1.0f, -2.0f, 3.5f};
    constexpr std::array expected{2.0f, -4.0f, 7.0f};
    constexpr std::array graphExpected{2.0f, 4.0f, 6.0f};

    std::cout << "Direct processOne():\n";
    gr::blocks::tutorial::Gain gain;
    for (std::size_t index = 0; index < input.size(); ++index) {
        const float output = gain.processOne(input[index]);
        if (output != expected[index]) return 1;
        std::cout << input[index] << " -> " << output << '\n';
    }

    using namespace gr::blocks::testing;
    gr::Graph graph;
    auto& source = graph.emplaceBlock<CountingSource<float>>(
        {{"n_samples_max", gr::Size_t{graphExpected.size()}}});
    auto& graphGain = graph.emplaceBlock<gr::blocks::tutorial::Gain>();
    auto& sink = graph.emplaceBlock<TagSink<float, ProcessFunction::USE_PROCESS_ONE>>(
        {{"n_samples_expected", gr::Size_t{graphExpected.size()}}});
    checked(graph.connect<"out", "in">(source, graphGain));
    checked(graph.connect<"out", "in">(graphGain, sink));

    gr::scheduler::Simple scheduler;
    checked(scheduler.exchange(std::move(graph)));
    checked(scheduler.runAndWait());
    if (!std::ranges::equal(sink._samples, graphExpected)) return 1;

    std::cout << "Flowgraph (CountingSource -> Gain -> TagSink):\n";
    for (std::size_t index = 0; index < sink._samples.size(); ++index) {
        std::cout << index + 1 << " -> " << sink._samples[index] << '\n';
    }
} catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
}
