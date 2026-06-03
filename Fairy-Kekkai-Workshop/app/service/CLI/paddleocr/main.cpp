#ifdef _WIN32
#include <windows.h>
#endif
#include "cvutils_api.h"
#include <algorithm>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <opencv2/opencv.hpp>
#include <sstream>
#include <string>
#include <vector>

namespace fs = std::filesystem;

// ---------------------------------------------------------------------------
// Error callback
// ---------------------------------------------------------------------------
static std::string g_last_error;
static void error_cb(const char *msg) {
  g_last_error = msg ? msg : "";
  std::cerr << "[CVUtils Error] " << msg << std::endl;
}

// ---------------------------------------------------------------------------
// Simple arg parser: key-value pairs after the command name
// ---------------------------------------------------------------------------
static std::map<std::string, std::string> parse_args(int argc, char *argv[],
                                                     std::string &out_cmd) {
  std::map<std::string, std::string> args;
  if (argc < 2)
    return args;
  out_cmd = argv[1];
  for (int i = 2; i < argc; ++i) {
    std::string key = argv[i];
    if (key.rfind("--", 0) == 0 && i + 1 < argc) {
      args[key] = argv[i + 1];
      ++i;
    }
  }
  return args;
}

// ---------------------------------------------------------------------------
// Load image -> cv::Mat (RGB, matching Luna Python binding)
// ---------------------------------------------------------------------------
static cv::Mat load_image_rgb(const fs::path &path) {
  cv::Mat bgr = cv::imread(path.string(), cv::IMREAD_COLOR);
  if (bgr.empty())
    return {};
  cv::Mat rgb;
  cv::cvtColor(bgr, rgb, cv::COLOR_BGR2RGB);
  return rgb;
}

// ---------------------------------------------------------------------------
// Run OCR on one image, collect results
// ---------------------------------------------------------------------------
struct OcrResult {
  std::array<cv::Point2f, 4> box;
  std::string text;
};

static std::vector<OcrResult> run_ocr_on_image(void *ocr, const cv::Mat &rgb) {
  std::vector<OcrResult> results;
  auto cb = [](float x1, float y1, float x2, float y2, float x3, float y3,
               float x4, float y4, const char *text) {
    auto *vec = static_cast<std::vector<OcrResult> *>(
        static_cast<void *>(const_cast<char *>(text))); // hack to pass userdata
  };
  // Use a thread_local or global to receive callbacks since CVUtils API doesn't
  // pass userdata
  static std::vector<OcrResult> *g_results = nullptr;
  g_results = &results;

  auto callback = [](float x1, float y1, float x2, float y2, float x3, float y3,
                     float x4, float y4, const char *text) {
    OcrResult r;
    r.box = {cv::Point2f(x1, y1), cv::Point2f(x2, y2), cv::Point2f(x3, y3),
             cv::Point2f(x4, y4)};
    r.text = text ? text : "";
    g_results->push_back(r);
  };

  OcrDetect(ocr, &rgb, Directional::H, callback, error_cb);
  return results;
}

// ---------------------------------------------------------------------------
// Format polygon for JSON output
// ---------------------------------------------------------------------------
static std::string format_poly_json(const std::array<cv::Point2f, 4> &box) {
  std::ostringstream oss;
  oss << "[[" << box[0].x << "," << box[0].y << "],[" << box[1].x << ","
      << box[1].y << "],[" << box[2].x << "," << box[2].y << "],[" << box[3].x
      << "," << box[3].y << "]]";
  return oss.str();
}

// ---------------------------------------------------------------------------
// Progress file writer
// ---------------------------------------------------------------------------
static void write_progress(const std::string &file_path, int current, int total) {
  if (file_path.empty())
    return;
  std::ofstream ofs(file_path, std::ios::trunc);
  if (ofs.is_open()) {
    ofs << current << "/" << total;
  }
}

// ---------------------------------------------------------------------------
// Command: text_detection
//   paddleocr.exe text_detection
//      --input <dir>
//      --model_dir <dir>
//      --model_name <name>
//      --save_path <dir>
//      [--device cpu|gpu]
//      [--progress_file <path>]
// ---------------------------------------------------------------------------
static int cmd_text_detection(const std::map<std::string, std::string> &args) {
  fs::path input_dir = args.count("--input") ? args.at("--input") : "";
  fs::path model_dir = args.count("--model_dir") ? args.at("--model_dir") : "";
  fs::path save_path = args.count("--save_path") ? args.at("--save_path") : "";
  std::string device = args.count("--device") ? args.at("--device") : "cpu";
  std::string progress_file = args.count("--progress_file") ? args.at("--progress_file") : "";
  bool use_gpu = (device == "gpu");
  // Map CLI device flag to ONNX Runtime provider name
  std::string provider = use_gpu ? "DML" : "CPU";

  if (input_dir.empty() || model_dir.empty() || save_path.empty()) {
    std::cerr << "Usage: text_detection --input <dir> --model_dir <dir> "
                 "--model_name <name> --save_path <dir> [--device cpu|gpu]"
              << std::endl;
    return 1;
  }

  fs::path det_onnx = model_dir / "det.onnx";
  fs::path rec_onnx = model_dir / "rec.onnx";
  fs::path dict_txt = model_dir / "dict.txt";

  if (!fs::exists(det_onnx) || !fs::exists(rec_onnx) || !fs::exists(dict_txt)) {
    std::cerr << "Model files not found in " << model_dir << std::endl;
    return 1;
  }

  if (!OcrLoadRuntime()) {
    std::cerr << "Failed to load ONNX Runtime" << std::endl;
    return 1;
  }

  g_last_error.clear();
  void *ocr = OcrInit(det_onnx.wstring().c_str(), rec_onnx.wstring().c_str(),
                      dict_txt.wstring().c_str(), 4, use_gpu, 0, provider.c_str(), error_cb);
  if (!ocr) {
    std::cerr << "OcrInit failed: " << g_last_error << std::endl;
    return 1;
  }

  fs::create_directories(save_path);

  std::vector<fs::path> images;
  for (const auto &entry : fs::directory_iterator(input_dir)) {
    if (entry.is_regular_file()) {
      std::string ext = entry.path().extension().string();
      std::transform(ext.begin(), ext.end(), ext.begin(), ::tolower);
      if (ext == ".jpg" || ext == ".jpeg" || ext == ".png" || ext == ".bmp")
        images.push_back(entry.path());
    }
  }
  std::sort(images.begin(), images.end());

  int processed = 0;
  for (const auto &img_path : images) {
    cv::Mat rgb = load_image_rgb(img_path);
    if (rgb.empty())
      continue;

    auto results = run_ocr_on_image(ocr, rgb);

    std::ostringstream json;
    std::string path_str = img_path.string();
    std::replace(path_str.begin(), path_str.end(), '\\', '/');
    json << "{\"input_path\":\"" << path_str << "\",";
    json << "\"dt_polys\":[";
    for (size_t i = 0; i < results.size(); ++i) {
      if (i)
        json << ",";
      json << format_poly_json(results[i].box);
    }
    json << "],\"dt_scores\":[";
    for (size_t i = 0; i < results.size(); ++i) {
      if (i)
        json << ",";
      json << "1.0"; // Luna does not expose per-box confidence
    }
    json << "]}";

    fs::path out_file = save_path / (img_path.stem().string() + "_det.json");
    std::ofstream ofs(out_file, std::ios::out);
    ofs << json.str();

    ++processed;
    std::cout << "ppocr INFO: Processed item " << processed << "/"
              << images.size() << std::endl;
    write_progress(progress_file, processed, (int)images.size());
  }

  OcrDestroy(ocr);
  return 0;
}

// ---------------------------------------------------------------------------
// Command: ocr
//   paddleocr.exe ocr
//      --input <dir>
//      --device cpu|gpu
//      --use_textline_orientation true|false
//      --lang <lang>
//      --text_detection_model_dir <dir>
//      --text_recognition_model_dir <dir>
//      [--textline_orientation_model_dir <dir>]
//      [--output <file>]
//      [--progress_file <path>]
// ---------------------------------------------------------------------------
static int cmd_ocr(const std::map<std::string, std::string> &args) {
  fs::path input_dir = args.count("--input") ? args.at("--input") : "";
  fs::path det_dir = args.count("--text_detection_model_dir")
                         ? args.at("--text_detection_model_dir")
                         : "";
  fs::path rec_dir = args.count("--text_recognition_model_dir")
                         ? args.at("--text_recognition_model_dir")
                         : "";

  if (input_dir.empty() || det_dir.empty() || rec_dir.empty()) {
    std::cerr
        << "Usage: ocr --input <dir> --device <cpu|gpu> --lang <lang> "
           "--text_detection_model_dir <dir> --text_recognition_model_dir <dir>"
        << std::endl;
    return 1;
  }

  fs::path det_onnx = det_dir / "det.onnx";
  fs::path rec_onnx = rec_dir / "rec.onnx";
  fs::path dict_txt = rec_dir / "dict.txt";

  if (!fs::exists(det_onnx) || !fs::exists(rec_onnx) || !fs::exists(dict_txt)) {
    std::cerr << "Model files not found" << std::endl;
    return 1;
  }

  bool use_gpu = false;
  if (args.count("--device"))
    use_gpu = (args.at("--device") == "gpu");

  std::string provider = use_gpu ? "DML" : "CPU";
  std::string progress_file = args.count("--progress_file") ? args.at("--progress_file") : "";

  if (!OcrLoadRuntime()) {
    std::cerr << "Failed to load ONNX Runtime" << std::endl;
    return 1;
  }

  g_last_error.clear();
  void *ocr =
      OcrInit(det_onnx.wstring().c_str(), rec_onnx.wstring().c_str(),
              dict_txt.wstring().c_str(), 4, use_gpu, 0, provider.c_str(), error_cb);
  if (!ocr) {
    std::cerr << "OcrInit failed: " << g_last_error << std::endl;
    return 1;
  }

  std::vector<fs::path> images;
  for (const auto &entry : fs::directory_iterator(input_dir)) {
    if (entry.is_regular_file()) {
      std::string ext = entry.path().extension().string();
      std::transform(ext.begin(), ext.end(), ext.begin(), ::tolower);
      if (ext == ".jpg" || ext == ".jpeg" || ext == ".png" || ext == ".bmp")
        images.push_back(entry.path());
    }
  }
  std::sort(images.begin(), images.end());

  std::string output_file;
  auto it = args.find("--output");
  if (it != args.end())
    output_file = it->second;
  std::ofstream out_json;
  if (!output_file.empty()) {
    out_json.open(output_file);
    if (!out_json.is_open()) {
      std::cerr << "Failed to open output file: " << output_file << std::endl;
      return 1;
    }
  }

  int processed = 0;
  for (const auto &img_path : images) {
    cv::Mat rgb = load_image_rgb(img_path);
    if (rgb.empty())
      continue;

    auto results = run_ocr_on_image(ocr, rgb);

    if (out_json.is_open()) {
      out_json << "{\"image\":\"" << img_path.filename().string()
               << "\",\"results\":[";
      for (size_t i = 0; i < results.size(); ++i) {
        if (i)
          out_json << ",";
        out_json << "{\"box\":" << format_poly_json(results[i].box)
                 << ",\"text\":\"" << results[i].text << "\",\"score\":100.0}";
      }
      out_json << "]}" << std::endl;
    } else {
      printf("ppocr INFO: **********%s**********\n",
             img_path.filename().string().c_str());
      fflush(stdout);

      printf("ppocr INFO: [");
      for (size_t i = 0; i < results.size(); ++i) {
        if (i)
          printf(",");
        printf("[%s,(\"%s\",100.0)]", format_poly_json(results[i].box).c_str(),
               results[i].text.c_str());
      }
      printf("]\n");
      fflush(stdout);
    }

    ++processed;
    std::cout << "ppocr INFO: Processed item " << processed << "/"
              << images.size() << std::endl;
    write_progress(progress_file, processed, (int)images.size());
  }

  if (out_json.is_open())
    out_json.close();

  OcrDestroy(ocr);
  return 0;
}

// ---------------------------------------------------------------------------
// Entry point
// ---------------------------------------------------------------------------
int main(int argc, char *argv[]) {
#ifdef _WIN32
  SetConsoleOutputCP(CP_UTF8);
#endif
  setvbuf(stdout, nullptr, _IONBF, 0);
  std::string cmd;
  auto args = parse_args(argc, argv, cmd);

  if (cmd == "text_detection")
    return cmd_text_detection(args);
  if (cmd == "ocr")
    return cmd_ocr(args);

  std::cerr << "Unknown command: " << cmd << std::endl;
  std::cerr << "Supported commands: text_detection, ocr" << std::endl;
  return 1;
}
