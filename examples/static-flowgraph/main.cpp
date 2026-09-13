#include <gnuradio-4.0/Graph.hpp>
#include <gnuradio-4.0/Scheduler.hpp>
#include <gnuradio-4.0/fileio/BasicFileIo.hpp>
#include <gnuradio-4.0/filter/time_domain_filter.hpp>
#include <iostream>

// Fail visibly on connection, scheduler-exchange, or run errors.
template<typename Result>
void checked(Result&& result) {
    if (!result) throw gr::exception(result.error().message);
}

int main(int argc, char** argv) try {
    if (argc != 3) {
        std::cerr << "usage: " << argv[0] << " input.f32 output.f32\n";
        return 2;
    }
    const std::string input = argv[1], output = argv[2];
    using namespace gr::blocks;
    gr::Graph graph;
    auto& source = graph.emplaceBlock<fileio::BasicFileSource<float>>(
        {{"file_name", input}});
    auto& lowpass = graph.emplaceBlock<filter::BasicFilter<float>>(
        {{"sample_rate", 8192.0f}, {"f_low", 512.0f}});
    auto& sink = graph.emplaceBlock<fileio::BasicFileSink<float>>(
        {{"file_name", output}});
    checked(graph.connect<"out", "in">(source, lowpass));
    checked(graph.connect<"out", "in">(lowpass, sink));
    gr::scheduler::Simple scheduler;
    checked(scheduler.exchange(std::move(graph)));
    checked(scheduler.runAndWait());
    std::cout << "Completed: " << input << " -> " << output << '\n';
} catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
}
