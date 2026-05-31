from module import *
import time, json
from model import engine, Videos
from sqlmodel import Session, select

while True:
    with Session(engine) as session:
        videos = session.execute(select(Videos)).mappings().all()
        for video in videos:
            videotitle = video.Videos.videotitle
            filename = video.Videos.filename
            content = video.Videos.content
            summary = video.Videos.summary
            keyword = video.Videos.keyword
            reference = video.Videos.reference
            xmind_json = video.Videos.xmindjson
            exam_json = video.Videos.examjson

            if content is None or content == "":
                print(f"视频 {videotitle} 的正文内容为空，正在更新...")
                content = audio_text(f"{filename.split('.')[0]}.mp3")
                video.Videos.Content = content
            if summary is None or summary == "":
                print(f"视频 {videotitle} 的笔记内容为空，正在更新...")
                summary = summarize(content)
                video.Videos.summary = summary
            if xmind_json is None or xmind_json == "":
                print(f"视频 {videotitle} 的XMind JSON为空，正在更新...")
                xmind_json = json.loads(gen_xmind_json(content))
                keyword = xmind_json['meta']['name']
                video.Videos.keyword = keyword
                video.Videos.xmindjson = str(xmind_json)
                write_xmind_file(xmind_json, filename)
            if reference is None or reference == "":
                print(f"视频 {videotitle} 的参考链接为空，正在更新...")
                reference = gen_reference(keyword)
                video.Videos.reference = reference
            if exam_json is None or exam_json == "":
                print(f"视频 {videotitle} 的考试题目为空，正在更新...")
                exam_json = gen_exam(content)
                video.Videos.examjson = exam_json
                insert_exam(str(exam_json), video.Videos.videoid)

            session.commit()

            # 如果未生成关键帧，则生成
            if not os.path.exists(f"static/frames/{filename}"):
                print(f"正在为 {filename} 生成关键帧...")
                gen_key_frames(f"static/videos/{filename}")

    print("本次处理完成，正在等待下一次处理...")
    time.sleep(60)