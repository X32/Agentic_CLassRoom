import os
import sys

# 切换到项目目录，确保能导入 module
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from module import video_audio


def create_test_video(output_path, duration=5, width=1280, height=720):
    """用 ffmpeg 生成一个测试视频"""
    cmd = (
        f'ffmpeg -y -f lavfi -i "testsrc=duration={duration}'
        f':size={width}x{height}:rate=25" '
        f'-f lavfi -i "sine=frequency=440:duration={duration}" '
        f'-c:v libx264 -c:a aac -pix_fmt yuv420p {output_path}'
    )
    ret = os.system(cmd)
    assert ret == 0, f"生成测试视频失败，退出码 {ret}"
    print(f"[OK] 生成测试视频: {output_path} ({duration}s, {width}x{height})")


def test_video_audio_basic():
    """基本功能测试：转码 + 提取音频 + 返回正确结果"""
    os.makedirs("static/videos", exist_ok=True)
    filename = "test_clip.mp4"
    filepath = f"static/videos/{filename}"

    # 生成 5 秒测试视频
    create_test_video(filepath, duration=5)

    # 调用被测试函数
    result = video_audio(filename)

    # 1. 检查返回值
    assert isinstance(result, dict), "返回值应为字典"
    assert "audio_name" in result, "返回值缺少 audio_name"
    assert "duration" in result, "返回值缺少 duration"
    print(f"[OK] 返回值: {result}")

    # 2. 检查音频文件是否生成
    audio_path = f"static/videos/{result['audio_name']}"
    assert os.path.exists(audio_path), f"音频文件未生成: {audio_path}"
    audio_size = os.path.getsize(audio_path)
    print(f"[OK] 音频文件存在: {audio_path} ({audio_size / 1024:.1f} KB)")

    # 3. 检查 duration 合理性（允许 ±2 秒误差）
    assert 3 < result["duration"] < 7, f"duration 异常: {result['duration']}"
    print(f"[OK] duration 合理: {result['duration']:.2f}s")

    # 4. 检查原始视频是否被重新编码（tmp 文件不应残留）
    tmp_file = f"static/videos/{filename}.tmp.mp4"
    assert not os.path.exists(tmp_file), f"临时文件未清理: {tmp_file}"
    print(f"[OK] 临时文件已清理")

    print("\n=== test_video_audio_basic PASSED ===")
    return True


def test_video_audio_hd():
    """高清视频测试（1080p）"""
    os.makedirs("static/videos", exist_ok=True)
    filename = "test_clip_1080p.mp4"
    filepath = f"static/videos/{filename}"

    create_test_video(filepath, duration=3, width=1920, height=1080)

    result = video_audio(filename)

    assert result["audio_name"] == "test_clip_1080p.mp3"
    print(f"[OK] 1080p 视频处理成功, audio_name={result['audio_name']}")
    print("\n=== test_video_audio_hd PASSED ===")
    return True


def test_video_audio_different_formats():
    """不同输入格式测试"""
    os.makedirs("static/videos", exist_ok=True)

    # 生成一个 AVI 格式测试
    filename = "test_clip.avi"
    filepath = f"static/videos/{filename}"
    cmd = (
        f'ffmpeg -y -f lavfi -i "testsrc=duration=2:size=640x480:rate=25" '
        f'-f lavfi -i "sine=frequency=440:duration=2" '
        f'-c:v mpeg4 -c:a aac {filepath}'
    )
    os.system(cmd)
    assert os.path.exists(filepath), "生成 AVI 测试文件失败"
    print(f"[OK] 生成测试 AVI 文件")

    result = video_audio(filename)

    assert result["audio_name"] == "test_clip.mp3"
    assert os.path.exists(f"static/videos/{result['audio_name']}")
    print(f"[OK] AVI 格式处理成功, audio_name={result['audio_name']}")
    print("\n=== test_video_audio_different_formats PASSED ===")
    return True


if __name__ == "__main__":
    print("=" * 50)
    print("  video_audio() 测试")
    print("=" * 50)

    passed = 0
    failed = 0

    for test_func in [
        test_video_audio_basic,
        test_video_audio_hd,
        test_video_audio_different_formats,
    ]:
        try:
            print(f"\n--- 运行: {test_func.__name__} ---")
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n[FAIL] {test_func.__name__}: {e}")
            failed += 1

    print("\n" + "=" * 50)
    print(f"结果: {passed} passed, {failed} failed")
    print("=" * 50)
