#!/usr/bin/env python
"""测试 transcribe 函数的完整测试套件"""

import sys
import os
import unittest
import tempfile
from pathlib import Path

sys.path.insert(0, '.')

from module import transcribe


class TestTranscribe(unittest.TestCase):
    """transcribe 函数的测试用例"""

    @classmethod
    def setUpClass(cls):
        """在所有测试之前执行一次"""
        cls.test_dir = tempfile.mkdtemp(prefix="transcribe_test_")
        cls.audio_file = "static/videos/20260420_172156_434147.mp3"
        print(f"\n测试目录：{cls.test_dir}")
        print(f"音频文件：{cls.audio_file}")

    @classmethod
    def tearDownClass(cls):
        """在所有测试之后清理"""
        import shutil
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir)
            print(f"\n已清理测试目录：{cls.test_dir}")

    def _skip_if_no_audio(self):
        """如果音频文件不存在则跳过测试"""
        if not os.path.exists(self.audio_file):
            self.skipTest(f"测试音频文件不存在：{self.audio_file}")

    def test_transcribe_cpu_mode(self):
        """测试 1: CPU 模式转写"""
        self._skip_if_no_audio()

        output_path = os.path.join(self.test_dir, "output_cpu.txt")

        print("\n[测试] CPU 模式转写...")
        transcribe(
            self.audio_file,
            model_size="tiny",
            language="zh",
            output_format="txt",
            output_path=output_path,
            device="cpu"
        )

        self.assertTrue(os.path.exists(output_path))
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertGreater(len(content), 0, "转写结果不应为空")
        print("[成功] CPU 模式测试通过")

    def test_transcribe_cuda_mode(self):
        """测试 2: CUDA 模式转写"""
        self._skip_if_no_audio()

        import torch
        if not torch.cuda.is_available():
            self.skipTest("CUDA 不可用，跳过 GPU 测试")

        output_path = os.path.join(self.test_dir, "output_cuda.txt")

        print("\n[测试] CUDA 模式转写...")
        transcribe(
            self.audio_file,
            model_size="tiny",
            language="zh",
            output_format="txt",
            output_path=output_path,
            device="cuda"
        )

        self.assertTrue(os.path.exists(output_path))
        print("[成功] CUDA 模式测试通过")

    def test_transcribe_auto_device(self):
        """测试 3: 自动设备选择"""
        self._skip_if_no_audio()

        output_path = os.path.join(self.test_dir, "output_auto.txt")

        print("\n[测试] 自动设备选择...")
        transcribe(
            self.audio_file,
            model_size="tiny",
            language="zh",
            output_format="txt",
            output_path=output_path,
            device="auto"
        )

        self.assertTrue(os.path.exists(output_path))
        print("[成功] 自动设备选择测试通过")

    def test_transcribe_srt_output(self):
        """测试 4: SRT 字幕格式输出"""
        self._skip_if_no_audio()

        output_path = os.path.join(self.test_dir, "output.srt")

        print("\n[测试] SRT 格式输出...")
        transcribe(
            self.audio_file,
            model_size="tiny",
            language="zh",
            output_format="srt",
            output_path=output_path,
            device="cpu"
        )

        self.assertTrue(os.path.exists(output_path))

        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("-->", content, "SRT 输出应包含时间戳格式")
        print("[成功] SRT 格式测试通过")

    def test_transcribe_json_output(self):
        """测试 5: JSON 格式输出"""
        self._skip_if_no_audio()

        output_path = os.path.join(self.test_dir, "output.json")

        print("\n[测试] JSON 格式输出...")
        transcribe(
            self.audio_file,
            model_size="tiny",
            language="zh",
            output_format="json",
            output_path=output_path,
            device="cpu"
        )

        self.assertTrue(os.path.exists(output_path))

        import json
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertIn("language", data)
            self.assertIn("duration", data)
            self.assertIn("segments", data)
        print("[成功] JSON 格式测试通过")

    def test_invalid_audio_file(self):
        """测试 6: 无效的音频文件路径"""
        output_path = os.path.join(self.test_dir, "output_invalid.txt")

        print("\n[测试] 无效文件路径处理...")
        with self.assertRaises((FileNotFoundError, RuntimeError, OSError)):
            transcribe(
                "/non/existent/path/audio.wav",
                model_size="tiny",
                language="zh",
                output_format="txt",
                output_path=output_path,
                device="cpu"
            )
        print("[成功] 无效文件路径测试通过")

    def test_different_model_sizes(self):
        """测试 7: 不同模型大小"""
        self._skip_if_no_audio()

        model_sizes = ["tiny", "base"]

        for size in model_sizes:
            output_path = os.path.join(self.test_dir, f"output_{size}.txt")

            print(f"\n[测试] 模型大小：{size}...")
            transcribe(
                self.audio_file,
                model_size=size,
                language="zh",
                output_format="txt",
                output_path=output_path,
                device="cpu"
            )

            self.assertTrue(os.path.exists(output_path))
            print(f"[成功] {size} 模型测试通过")


def run_quick_test():
    """运行快速测试（不使用单元测试框架）"""
    audio_file = "static/videos/20260420_172156_434147.mp3"

    print("=" * 50)
    print("快速测试：transcribe 函数")
    print("=" * 50)

    if not os.path.exists(audio_file):
        print(f"\n错误：音频文件不存在：{audio_file}")
        print("请确保音频文件存在后重新运行测试")
        return False

    import time
    start_time = time.time()

    try:
        print(f"\n音频文件：{audio_file}")
        print("使用模型：tiny (快速测试)")
        print("设备：CPU")
        print("\n开始转写...\n")

        transcribe(
            audio_file,
            model_size="tiny",
            language="zh",
            output_format="txt",
            output_path="static/videos/test_output.txt",
            device="cpu"
        )

        elapsed = time.time() - start_time
        print(f"\n[成功] 转写完成，耗时：{elapsed:.2f}秒")
        print("输出文件：static/videos/test_output.txt")
        return True

    except Exception as e:
        print(f"\n[失败] {type(e).__name__}: {e}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="测试 transcribe 函数")
    parser.add_argument("--quick", action="store_true", help="运行快速测试")
    parser.add_argument("--full", action="store_true", help="运行完整测试套件")
    parser.add_argument("--audio", type=str, help="指定测试音频文件路径")

    args = parser.parse_args()

    if args.quick or (not args.full and not args.audio):
        run_quick_test()
    elif args.full:
        print("\n运行完整测试套件...\n")
        unittest.main(verbosity=2)
    elif args.audio:
        print(f"\n使用自定义音频文件：{args.audio}")
        if not os.path.exists(args.audio):
            print(f"错误：文件不存在 - {args.audio}")
            sys.exit(1)

        output_file = Path(args.audio).with_suffix(".txt")
        transcribe(
            args.audio,
            model_size="tiny",
            language="zh",
            output_format="txt",
            output_path=str(output_file),
            device="cpu"
        )
        print(f"\n转写完成：{output_file}")
