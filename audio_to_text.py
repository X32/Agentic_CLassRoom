#!/usr/bin/env python3
"""
长音频转文字脚本 - Faster-Whisper
支持 GPU 加速，自动处理长音频
"""

import os
# 禁用 cuDNN（GTX 1080 Ti 兼容性）
os.environ["CT2_USE_CUDNN"] = "0"

import argparse
import sys
from pathlib import Path

def transcribe(audio_path, model_size="large-v3", language="zh", output_format="txt", output_path=None, device="cuda"):
    """
    转写音频文件

    Args:
        audio_path: 音频文件路径
        model_size: 模型大小 (tiny/base/small/medium/large-v3)
        language: 语言代码 (zh/en 等)
        output_format: 输出格式 (txt/srt/json)
        output_path: 输出文件路径（可选）
        device: 设备 (auto/cuda/cpu)

    Returns:
        str: 转写的文字内容（与 audio_text 返回值一致）
    """
    from faster_whisper import WhisperModel
    import torch

    # 自动检测设备
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"

    print(f"Loading model: {model_size} on {device}...")

    # 根据设备选择计算类型
    if device == "cuda":
        model = WhisperModel(model_size, device="cuda", compute_type="int8")
    else:
        model = WhisperModel(model_size, device="cpu", compute_type="int8")

    print(f"Transcribing: {audio_path}")
    print(f"Language: {language}")

    # 转写音频
    segments, info = model.transcribe(
        audio_path,
        language=language,
        beam_size=5,
        vad_filter=True,  # 自动跳过静音
        vad_parameters=dict(min_silence_duration_ms=500)
    )

    print(f"Detected language: {info.language} (probability: {info.language_probability:.2f})")
    print(f"Duration: {info.duration:.2f}s")

    # 收集所有文本
    all_segments = list(segments)
    content = "".join([segment.text for segment in all_segments])

    # 输出结果
    if output_path:
        output_file = Path(output_path)
    else:
        output_file = Path(audio_path).with_suffix(f".{output_format}")

    if output_format == "txt":
        with open(output_file, "w", encoding="utf-8") as f:
            for segment in all_segments:
                f.write(segment.text + "\n")
        print(f"Saved to: {output_file}")

    elif output_format == "srt":
        def format_time(seconds):
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            ms = int((seconds - int(seconds)) * 1000)
            return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

        with open(output_file, "w", encoding="utf-8") as f:
            for i, segment in enumerate(all_segments, 1):
                f.write(f"{i}\n")
                f.write(f"{format_time(segment.start)} --> {format_time(segment.end)}\n")
                f.write(f"{segment.text}\n\n")
        print(f"Saved to: {output_file}")

    elif output_format == "json":
        import json
        result = {
            "language": info.language,
            "duration": info.duration,
            "segments": [
                {
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text
                }
                for seg in all_segments
            ]
        }
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"Saved to: {output_file}")

    # 打印预览
    print("\n--- Preview ---")
    for segment in all_segments[:5]:
        print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
    if len(all_segments) > 5:
        print(f"... ({len(all_segments) - 5} more segments)")

    # 返回纯文本，与 audio_text 返回值一致
    return content

def main():
    parser = argparse.ArgumentParser(description="长音频转文字 (Faster-Whisper)")
    parser.add_argument("audio", help="音频文件路径")
    parser.add_argument("-m", "--model", default="large-v3",
                        choices=["tiny", "base", "small", "medium", "large-v3"],
                        help="模型大小 (默认：large-v3)")
    parser.add_argument("-l", "--language", default="zh", help="语言代码 (默认：zh)")
    parser.add_argument("-f", "--format", default="txt",
                        choices=["txt", "srt", "json"],
                        help="输出格式 (默认：txt)")
    parser.add_argument("-o", "--output", help="输出文件路径")
    parser.add_argument("-d", "--device", default="auto",
                        choices=["auto", "cuda", "cpu"],
                        help="设备选择 (默认：auto)")

    args = parser.parse_args()

    if not Path(args.audio).exists():
        print(f"Error: File not found: {args.audio}")
        sys.exit(1)

    transcribe(args.audio, args.model, args.language, args.format, args.output, args.device)

if __name__ == "__main__":
    main()
