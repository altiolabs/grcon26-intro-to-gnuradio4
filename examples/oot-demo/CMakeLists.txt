cmake_minimum_required(VERSION 3.27)
project(gr4IntroOot LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

include(GNUInstallDirs)
find_package(gnuradio4 CONFIG REQUIRED)
find_package(GnuRadioBlockLib CONFIG REQUIRED)

set(gain_header include/gnuradio-4.0/intro/Gain.hpp)

gr_add_block_library(
  GrIntroBlocks
  MAKE_SHARED_LIBRARY
  HEADERS ${gain_header})

# Registration generation supplies factories; the plugin entry points make
# this shared library loadable by Studio's control plane.
target_sources(GrIntroBlocksShared PRIVATE plugin.cpp)
target_link_libraries(GrIntroBlocksShared PRIVATE gnuradio4::gnuradio-plugin)

install(DIRECTORY include/gnuradio-4.0/intro
  DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/gnuradio-4.0)

# This executable deliberately does not link the OOT: it checks dynamic loading.
add_executable(intro-plugin-check plugin-check.cpp)
target_link_libraries(intro-plugin-check PRIVATE gnuradio4::gnuradio-core gnuradio4::gnuradio-blocklib-core)
