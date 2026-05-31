import os
import cv2
import numpy as np

# 测试 gen_key_frames 方法（带调试信息）
def test_gen_key_frames_debug():
    # 使用一个现有的视频文件进行测试
    video_path = "static/videos/20260422_115634_081546.mp4"

    if not os.path.exists(video_path):
        print(f"视频文件不存在：{video_path}")
        return

    print(f"开始测试 gen_key_frames，视频路径：{video_path}")
    print(f"视频文件大小：{os.path.getsize(video_path) / 1024 / 1024:.2f} MB")

    # 如果目录不存在，则以视频文件名创建目录，便于后续读取
    filename = video_path.split("/")[-1]
    if not os.path.exists(f"static/frames/{filename}"):
        os.mkdir(f"static/frames/{filename}")
    else:
        print(f"目录已存在，删除后重新生成：static/frames/{filename}")
        # 删除已有文件
        for f in os.listdir(f"static/frames/{filename}"):
            os.remove(f"static/frames/{filename}/{f}")

    key_frames = []   # 保存抽样帧图片
    cap = cv2.VideoCapture(video_path)
    # 获取视频的总帧数
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    duration = frame_count / fps if fps > 0 else 0

    print(f"视频总帧数：{frame_count}, FPS: {fps:.2f}, 时长：{duration:.2f}秒")

    # 遍历所有帧，每 200 帧提取一张截图
    for i in range(frame_count):
        ret, frame = cap.read()   # 读取每一帧
        if i % 200 == 0:          # 每 200 帧抽样一帧，可根据实际情况修改间隔
            key_frames.append(frame)

    cap.release()
    print(f"提取的抽样帧数量：{len(key_frames)}")

    # 遍历所有的抽样帧，并比较两者之间的差异，差异大则保存为关键帧
    print("\n帧间差异分析：")
    print("-" * 50)
    for i in range(len(key_frames)-1):
        # 将彩色图片转换为灰度图，以减少比较运算的数据量
        prev_gray = cv2.cvtColor(key_frames[i], cv2.COLOR_BGR2GRAY)
        next_gray = cv2.cvtColor(key_frames[i+1], cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(prev_gray, next_gray)   # 比较两张图片之间的差异
        diff_avg = np.average(diff)      # 取差异的平均值

        is_key_frame = diff_avg > 0.8
        print(f"帧{i} -> 帧{i+1}: 差异平均值 = {diff_avg:.4f}, {'[关键帧]' if is_key_frame else ''}")

        # 如果差异较大，保存为关键帧
        if is_key_frame:
            cv2.imwrite(f"static/frames/{filename}/{i}.jpg", key_frames[i+1])

    # 检查生成的关键帧目录
    frames_dir = f"static/frames/{filename}"
    files = os.listdir(frames_dir)
    print("-" * 50)
    print(f"生成的关键帧数量：{len(files)}")
    print(f"关键帧文件：{files}")

if __name__ == '__main__':
    test_gen_key_frames_debug()
