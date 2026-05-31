cmake_minimum_required(VERSION 3.20)
project(luna-ocr-cli LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# ---------------------------------------------------------------------------
# OpenCV (reuse Luna's pre-built package)
# ---------------------------------------------------------------------------
set(OPENCV_ROOT "D:/CODE/LunaTranslator/src/NativeImpl/build/x64_win10/_deps/opencv-src/windows-x64")
set(OpenCV_INCLUDE_DIRS "${OPENCV_ROOT}/include")
set(OpenCV_LIB_DIR      "${OPENCV_ROOT}/x64/vc16/staticlib")

file(GLOB OpenCV_LIBS "${OpenCV_LIB_DIR}/*.lib")

# ---------------------------------------------------------------------------
# CVUtils.dll import library
# ---------------------------------------------------------------------------
set(CVUTILS_LIB_DIR "D:/CODE/LunaTranslator/src/NativeImpl/builds/_x64_win10")
set(CVUTILS_LIB     "${CVUTILS_LIB_DIR}/CVUtils.lib")

# ---------------------------------------------------------------------------
# Executable
# ---------------------------------------------------------------------------
add_executable(paddleocr main.cpp)

target_include_directories(paddleocr PRIVATE
    ${OpenCV_INCLUDE_DIRS}
    ${CMAKE_CURRENT_SOURCE_DIR}
)

target_link_libraries(paddleocr PRIVATE
    ${OpenCV_LIBS}
    ${CVUTILS_LIB}
)

# On Windows, link system libs required by OpenCV static libs
target_link_libraries(paddleocr PRIVATE
    ws2_32
    user32
    gdi32
    winmm
    imm32
    ole32
    oleaut32
    comdlg32
    advapi32
    shell32
)
