using Whisper;

namespace WhisperNetCLI;

class Program
{
    static int Main(string[] args)
    {
        // 设置控制台输出编码为 UTF-8，避免中文乱码
        Console.OutputEncoding = System.Text.Encoding.UTF8;

        // 手动解析参数
        string? videoPath = null;
        string output = "subtitle.srt";
        string model = "ggml-medium.bin";
        string? language = null;
        string format = "srt";
        string? gpu = null;
        
        for (int i = 0; i < args.Length; i++)
        {
            switch (args[i])
            {
                case "--video_path":
                    if (i + 1 < args.Length) videoPath = args[++i];
                    break;
                case "--output":
                    if (i + 1 < args.Length) output = args[++i];
                    break;
                case "--model":
                    if (i + 1 < args.Length) model = args[++i];
                    break;
                case "--language":
                    if (i + 1 < args.Length) language = args[++i];
                    break;
                case "--format":
                    if (i + 1 < args.Length) format = args[++i];
                    break;
                case "--gpu":
                    if (i + 1 < args.Length) gpu = args[++i];
                    break;
                case "--help":
                case "-h":
                    PrintHelp();
                    return 0;
            }
        }
        
        if (string.IsNullOrEmpty(videoPath))
        {
            Console.Error.WriteLine("错误: 必须指定 --video_path 参数");
            PrintHelp();
            return 1;
        }
        
        TranscribeAsync(videoPath, output, model, language, format, gpu);
        return 0;
    }
    
    static void PrintHelp()
    {
        Console.WriteLine("Whisper语音识别CLI工具");
        Console.WriteLine();
        Console.WriteLine("用法: WhisperNetCLI [选项]");
        Console.WriteLine();
        Console.WriteLine("选项:");
        Console.WriteLine("  --video_path <路径>   视频或音频文件路径 (必需)");
        Console.WriteLine("  --output <路径>       输出文件路径 (默认: subtitle.srt)");
        Console.WriteLine("  --model <路径>        模型文件路径 (默认: ggml-medium.bin)");
        Console.WriteLine("  --language <代码>     语言代码 (如: zh, ja, en)");
        Console.WriteLine("  --format <格式>       输出格式: srt, txt, json (默认: srt)");
        Console.WriteLine("  --gpu <名称>          GPU适配器名称");
        Console.WriteLine("  -h, --help            显示帮助信息");
    }
    
    static void TranscribeAsync(string videoPath, string output, string model, string? language, string format, string? gpu)
    {
        try
        {
            // 验证输入文件
            if (!File.Exists(videoPath))
            {
                Console.Error.WriteLine($"错误: 文件不存在: {videoPath}");
                Environment.Exit(1);
            }
            
            // 验证模型文件
            if (!File.Exists(model))
            {
                Console.Error.WriteLine($"错误: 模型文件不存在: {model}");
                Environment.Exit(1);
            }
            
            // 设置日志
            Library.setLogSink(eLogLevel.Info, eLoggerFlags.UseStandardError | eLoggerFlags.SkipFormatMessage);
            
            Console.WriteLine($"加载模型: {model}");
            if (!string.IsNullOrEmpty(gpu))
            {
                Console.WriteLine($"使用GPU: {gpu}");
            }
            else
            {
                Console.WriteLine("使用CPU模式");
            }
            
            // 加载模型（如果不指定 GPU，则使用 CPU）
            using iModel whisperModel = Library.loadModel(model, adapter: gpu);
            
            // 检查模型是否支持多语言
            bool isMultilingual = whisperModel.isMultilingual();
            Console.WriteLine($"模型多语言支持: {isMultilingual}");
            
            // 设置语言
            eLanguage? lang = null;
            if (!string.IsNullOrEmpty(language))
            {
                if (!isMultilingual)
                {
                    Console.Error.WriteLine($"警告: 模型不支持多语言，将使用英语");
                    lang = eLanguage.English;
                }
                else
                {
                    lang = Library.languageFromCode(language);
                    if (lang == null)
                    {
                        Console.Error.WriteLine($"错误: 不支持的语言代码: {language}");
                        Environment.Exit(1);
                    }
                    Console.WriteLine($"设置语言: {language} ({lang})");
                }
            }
            else
            {
                Console.WriteLine("语言: 自动检测");
            }
            
            // 创建上下文
            using Context context = whisperModel.createContext();
            
            // 打印默认语言
            Console.WriteLine($"默认语言: {context.parameters.language} (0x{(uint)context.parameters.language:X})");
            
            // 设置参数（参考 WhisperDesktop 官方示例）
            if (lang.HasValue)
            {
                context.parameters.language = lang.Value;
                Console.WriteLine($"设置语言为: {lang.Value} (0x{(uint)lang.Value:X})");
            }
            
            // 禁用翻译功能
            context.parameters.setFlag(eFullParamsFlags.Translate, false);
            // 设置 NoContext
            context.parameters.setFlag(eFullParamsFlags.NoContext, true);
            
            // 打印参数调试信息
            Console.WriteLine($"最终参数语言: {context.parameters.language} (0x{(uint)context.parameters.language:X})");
            Console.WriteLine($"参数标志: {context.parameters.flags}");
            Console.WriteLine($"Translate标志: {(context.parameters.flags & eFullParamsFlags.Translate) != 0}");
            
            // 初始化Media Foundation
            iMediaFoundation mf = Library.initMediaFoundation();
            
            Console.WriteLine($"开始转录: {videoPath}");
            
            // 创建转录回调
            var transcribe = new TranscribeCallback();
            
            // 打开音频文件
            iAudioReader reader = mf.openAudioFile(videoPath, false);
            
            // 执行转录（带进度回调）
            context.runFull(reader, (double progress) => {
                int percent = (int)(progress * 100);
                Console.WriteLine($"PROGRESS:{percent}");
                Console.Out.Flush();
            }, transcribe);
            
            // 输出结果
            Console.WriteLine($"转录完成");
            
            // 保存输出
            SaveOutput(context, output, format);
            
            // 打印性能统计
            context.timingsPrint();
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"错误: {ex.Message}");
            Console.Error.WriteLine(ex.StackTrace);
            Environment.Exit(1);
        }
    }
    
    static void SaveOutput(Context context, string outputPath, string format)
    {
        var results = context.results(eResultFlags.Timestamps);
        var segments = results.segments;
        
        switch (format.ToLower())
        {
            case "srt":
                SaveSrt(segments, outputPath);
                break;
            case "txt":
                SaveTxt(segments, outputPath);
                break;
            case "json":
                SaveJson(segments, outputPath);
                break;
            default:
                Console.Error.WriteLine($"错误: 不支持的输出格式: {format}");
                Environment.Exit(1);
                break;
        }
        
        Console.WriteLine($"输出已保存到: {outputPath}");
    }
    
    static void SaveSrt(ReadOnlySpan<Whisper.sSegment> segments, string outputPath)
    {
        using var writer = new StreamWriter(outputPath);
        
        for (int i = 0; i < segments.Length; i++)
        {
            var seg = segments[i];
            writer.WriteLine(i + 1);
            writer.WriteLine($"{FormatTime(seg.time.begin)} --> {FormatTime(seg.time.end)}");
            writer.WriteLine(seg.text);
            writer.WriteLine();
        }
    }
    
    static void SaveTxt(ReadOnlySpan<Whisper.sSegment> segments, string outputPath)
    {
        using var writer = new StreamWriter(outputPath);
        
        foreach (var seg in segments)
        {
            writer.WriteLine(seg.text);
        }
    }
    
    static void SaveJson(ReadOnlySpan<Whisper.sSegment> segments, string outputPath)
    {
        var jsonSegments = new List<object>();
        foreach(var seg in segments)
        {
            jsonSegments.Add(new
            {
                start = seg.time.begin.TotalSeconds,
                end = seg.time.end.TotalSeconds,
                text = seg.text
            });
        }
        
        var json = System.Text.Json.JsonSerializer.Serialize(jsonSegments, new System.Text.Json.JsonSerializerOptions
        {
            WriteIndented = true
        });
        
        File.WriteAllText(outputPath, json);
    }
    
    static string FormatTime(TimeSpan time)
    {
        uint msec = (uint)time.Milliseconds;
        uint hr = (uint)time.Hours + (uint)time.Days * 24;
        uint min = (uint)time.Minutes;
        uint sec = (uint)time.Seconds;
        
        return $"{hr:D2}:{min:D2}:{sec:D2},{msec:D3}";
    }
}

class TranscribeCallback : Callbacks
{
}
