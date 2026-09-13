#pragma once

#include <gnuradio-4.0/Block.hpp>
#include <gnuradio-4.0/BlockRegistry.hpp>

namespace gr::intro {

template<typename T>
struct Gain : gr::Block<Gain<T>> {
    using gr::Block<Gain<T>>::Block;
    using Description = gr::Doc<"Multiply every input sample by gain.">;

    gr::PortIn<T>  in;
    gr::PortOut<T> out;
    gr::Annotated<T, "gain", gr::Doc<"Linear gain">, gr::Visible> gain{T{2}};

    GR_MAKE_REFLECTABLE(Gain, in, out, gain);

    [[nodiscard]] constexpr T processOne(T input) const noexcept {
        return input * gain.value;
    }
};

} // namespace gr::intro

GR_REGISTER_BLOCK(gr::intro::Gain, [T], [float])
