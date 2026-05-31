import os
import sys
from module import gen_key_frames

# 测试 gen_key_frames 方法
def test_gen_key_frames():
    # 使用一个现有的视频文件进行测试
    video_path = "static/videos/20260422_115634_081546.mp4"

    if not os.path.exists(video_path):
        print(f"视频文件不存在：{video_path}")
        return

    print(f"开始测试 gen_key_frames，视频路径：{video_path}")
    print(f"视频文件大小：{os.path.getsize(video_path) / 1024 / 1024:.2f} MB")

    # 调用 gen_key_frames 方法
    try:
        gen_key_frames(video_path)
        print("gen_key_frames 执行完成")
    except Exception as e:
        print(f"gen_key_frames 执行出错：{e}")
        import traceback
        traceback.print_exc()
        return

    # 检查生成的关键帧目录
    filename = video_path.split("/")[-1]
    frames_dir = f"static/frames/{filename}"

    if os.path.exists(frames_dir):
        files = os.listdir(frames_dir)
        print(f"关键帧目录：{frames_dir}")
        print(f"生成的关键帧数量：{len(files)}")
        print(f"关键帧文件：{files}")
    else:
        print(f"关键帧目录未创建：{frames_dir}")

if __name__ == '__main__':
    test_gen_key_frames()
