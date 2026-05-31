#pragma once
#include <cstdint>

// Minimal forward declarations for CVUtils.dll C API
// Link against CVUtils.lib (import library)

namespace cv { class Mat; }

enum class Directional
{
    H,
    V,
    Auto
};

extern "C" {
    __declspec(dllimport) bool OcrLoadRuntime();
    __declspec(dllimport) void* OcrInit(
        const wchar_t* szDetModel,
        const wchar_t* szRecModel,
        const wchar_t* szKeyPath,
        int nThreads,
        bool gpu,
        uint64_t luid,
        const char* device_type,
        void (*cb2)(const char*)
    );
    __declspec(dllimport) void OcrDetect(
        void* pOcrObj,
        const cv::Mat* mat,
        Directional mode,
        void (*cb)(float, float, float, float, float, float, float, float, const char*),
        void (*cb2)(const char*)
    );
    __declspec(dllimport) void OcrDestroy(void* pOcrObj);
}
