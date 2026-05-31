"""
测试 module.py 中的 transcribe 方法
"""
import os
import sys
import tempfile
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from module import transcribe


def create_test_audio(output_path: str, duration: float = 5.0, sample_rate: int = 16000):
    """
    创建一个简单的测试音频文件（静音 WAV 文件）

    Args:
        output_path: 输出文件路径
        duration: 音频时长（秒）
        sample_rate: 采样率
    """
    import wave
    import struct

    num_samples = int(duration * sample_rate)

    with wave.open(output_path, 'w') as wav_file:
        wav_file.setnchannels(1)  # 单声道
        wav_file.setsampwidth(2)  # 16 位
        wav_file.setframerate(sample_rate)

        # 写入静音数据
        for _ in range(num_samples):
            wav_file.writeframes(struct.pack('h', 0))  # 静音

    print(f"Created test audio file: {output_path}")


def test_transcribe_basic():
    """测试基本转写功能"""
    print("\n=== Test 1: Basic Transcribe ===")

    # 创建临时音频文件
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        temp_audio = f.name

    try:
        # 创建测试音频
        create_test_audio(temp_audio, duration=5.0)

        # 调用 transcribe（使用 CPU 避免 CUDA 依赖问题）
        result = transcribe(
            audio_path=temp_audio,
            model_size="tiny",  # 使用最小模型加速测试
            language="zh",
            output_format="txt",
            device="cpu"
        )

        print("Basic transcribe test passed!")
        return True

    except Exception as e:
        print(f"Basic transcribe test failed: {e}")
        return False
    finally:
        # 清理临时文件
        if os.path.exists(temp_audio):
            os.unlink(temp_audio)
        # 清理输出文件
        output_txt = temp_audio.replace('.wav', '.txt')
        if os.path.exists(output_txt):
            os.unlink(output_txt)


def test_transcribe_output_formats():
    """测试不同输出格式"""
    print("\n=== Test 2: Output Formats ===")

    formats = ['txt', 'srt', 'json']
    passed = True

    # 创建临时音频文件
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        temp_audio = f.name

    try:
        create_test_audio(temp_audio, duration=5.0)

        for fmt in formats:
            print(f"\nTesting format: {fmt}")
            output_file = temp_audio.replace('.wav', f'.{fmt}')

            try:
                transcribe(
                    audio_path=temp_audio,
                    model_size="tiny",
                    language="zh",
                    output_format=fmt,
                    output_path=output_file,
                    device="cpu"
                )

                # 验证输出文件存在
                assert os.path.exists(output_file), f"Output file not created: {output_file}"

                # 验证文件格式
                if fmt == 'json':
                    with open(output_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    assert 'language' in data, "JSON missing 'language' field"
                    assert 'segments' in data, "JSON missing 'segments' field"
                    print(f"  JSON format valid: {len(data.get('segments', []))} segments")

                elif fmt == 'srt':
                    with open(output_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    # 静音音频可能没有片段，这是正常的
                    if content.strip():
                        assert '-->' in content, "SRT missing timestamp format"
                    print(f"  SRT format valid (empty audio = no segments)")

                elif fmt == 'txt':
                    with open(output_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    print(f"  TXT format valid: {len(content)} chars")

                print(f"  Format {fmt}: PASSED")

            except Exception as e:
                print(f"  Format {fmt}: FAILED - {e}")
                passed = False
            finally:
                # 清理输出文件
                if os.path.exists(output_file):
                    os.unlink(output_file)

        return passed

    except Exception as e:
        print(f"Output formats test setup failed: {e}")
        return False
    finally:
        if os.path.exists(temp_audio):
            os.unlink(temp_audio)


def test_transcribe_devices():
    """测试不同设备设置"""
    print("\n=== Test 3: Device Selection ===")

    devices = ['cpu', 'auto']
    passed = True

    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        temp_audio = f.name

    try:
        create_test_audio(temp_audio, duration=5.0)

        for device in devices:
            print(f"\nTesting device: {device}")
            output_file = temp_audio.replace('.wav', '_device.txt')

            try:
                transcribe(
                    audio_path=temp_audio,
                    model_size="tiny",
                    language="zh",
                    output_format="txt",
                    output_path=output_file,
                    device=device
                )
                print(f"  Device {device}: PASSED")

            except Exception as e:
                print(f"  Device {device}: FAILED - {e}")
                passed = False
            finally:
                if os.path.exists(output_file):
                    os.unlink(output_file)

        return passed

    except Exception as e:
        print(f"Device selection test setup failed: {e}")
        return False
    finally:
        if os.path.exists(temp_audio):
            os.unlink(temp_audio)


def test_transcribe_custom_output_path():
    """测试自定义输出路径"""
    print("\n=== Test 4: Custom Output Path ===")

    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        temp_audio = f.name

    with tempfile.TemporaryDirectory() as temp_dir:
        custom_output = os.path.join(temp_dir, 'custom_output.txt')

        try:
            create_test_audio(temp_audio, duration=5.0)

            transcribe(
                audio_path=temp_audio,
                model_size="tiny",
                language="zh",
                output_format="txt",
                output_path=custom_output,
                device="cpu"
            )

            assert os.path.exists(custom_output), f"Custom output not created: {custom_output}"
            print("Custom output path test: PASSED")
            return True

        except Exception as e:
            print(f"Custom output path test: FAILED - {e}")
            return False
        finally:
            if os.path.exists(temp_audio):
                os.unlink(temp_audio)


def test_transcribe_real_audio():
    """测试真实音频文件转写"""
    print("\n=== Test 6: Real Audio Transcribe ===")

    # 真实音频文件路径
    real_audio_path = "/home/x32/Desktop/数据盘/workplace/AIagentLesson/chapter07/testsrc/20260420_172156_434147.mp3"

    # 检查文件是否存在
    if not os.path.exists(real_audio_path):
        print(f"Real audio file not found: {real_audio_path}")
        return False

    # 获取文件大小（MB）
    file_size_mb = os.path.getsize(real_audio_path) / (1024 * 1024)
    print(f"Audio file size: {file_size_mb:.2f} MB")

    try:
        # 测试转写真实音频（使用 GPU）
        output_path = "/tmp/real_audio_transcript.txt"

        transcribe(
            audio_path=real_audio_path,
            model_size="tiny",  # 使用最小模型加速测试
            language="zh",
            output_format="txt",
            output_path=output_path,
            device="cuda"  # 使用 GPU 加速
        )

        # 验证输出文件
        assert os.path.exists(output_path), f"Output file not created: {output_path}"

        # 读取并显示部分内容
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()

        print(f"Output file size: {len(content)} characters")
        print(f"\n--- First 500 chars ---")
        print(content[:500] if content else "(empty)")
        print(f"--- End Preview ---\n")

        # 清理输出文件
        os.unlink(output_path)

        print("Real audio transcribe test: PASSED")
        return True

    except Exception as e:
        print(f"Real audio transcribe test: FAILED - {e}")
        return False


def test_transcribe_error_handling():
    """测试错误处理"""
    print("\n=== Test 5: Error Handling ===")

    passed = True

    # 测试不存在的文件
    print("\nTesting non-existent file:")
    try:
        transcribe(
            audio_path="/non/existent/file.wav",
            model_size="tiny",
            device="cpu"
        )
        print("  Non-existent file: FAILED (should have raised exception)")
        passed = False
    except FileNotFoundError as e:
        print(f"  Non-existent file: PASSED (correctly raised FileNotFoundError)")
    except Exception as e:
        print(f"  Non-existent file: PASSED (raised {type(e).__name__}: {e})")

    # 测试无效的模型大小
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        temp_audio = f.name

    try:
        create_test_audio(temp_audio, duration=5.0)

        print("\nTesting invalid model size:")
        try:
            transcribe(
                audio_path=temp_audio,
                model_size="invalid_model",
                device="cpu"
            )
            print("  Invalid model: FAILED (should have raised exception)")
            passed = False
        except Exception as e:
            print(f"  Invalid model: PASSED (raised {type(e).__name__})")

    finally:
        if os.path.exists(temp_audio):
            os.unlink(temp_audio)

    return passed


def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("Transcribe Function Test Suite")
    print("=" * 50)

    results = {
        "Basic Transcribe": test_transcribe_basic(),
        "Output Formats": test_transcribe_output_formats(),
        "Device Selection": test_transcribe_devices(),
        "Custom Output Path": test_transcribe_custom_output_path(),
        "Error Handling": test_transcribe_error_handling(),
        "Real Audio Transcribe": test_transcribe_real_audio(),
    }

    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"  {name}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    return passed == total


if __name__ == "__main__":
    # success = run_all_tests()
    test_transcribe_real_audio()
    #sys.exit(0 if success else 1)
