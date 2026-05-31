#!/usr/bin/env python3
"""
测试 module.py 中的 video_audio 方法
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from module import video_audio

def test_video_audio():
    """测试 video_audio 方法"""
    print("=" * 50)
    print("测试 video_audio 方法")
    print("=" * 50)

    # 测试视频文件
    test_video = "20260420_172156_434147.mp4"
    video_path = f"static/videos/{test_video}"

    if not os.path.exists(video_path):
        print(f"错误：视频文件不存在：{video_path}")
        return

    print(f"\n测试视频：{test_video}")
    print(f"文件路径：{video_path}")

    try:
        print("\n开始转换...")
        result = video_audio(test_video)

        print("\n✓ 转换成功")
        print(f"结果：{result}")
        print(f"  - 音频文件名：{result['audio_name']}")
        print(f"  - 视频时长：{result['duration']:.2f} 秒")

        # 验证输出文件是否存在
        audio_path = f"static/videos/{result['audio_name']}"
        if os.path.exists(audio_path):
            file_size = os.path.getsize(audio_path) / (1024 * 1024)  # MB
            print(f"  - 输出文件大小：{file_size:.2f} MB")
            print(f"\n✓ 音频文件已保存：{audio_path}")
        else:
            print(f"\n✗ 警告：输出文件未找到：{audio_path}")

    except Exception as e:
        print(f"\n✗ 转换失败：{e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_video_audio()
