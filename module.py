import json, os, dashscope, requests, xmind
import time
import subprocess
import cv2, numpy as np
from openai import OpenAI
from datetime import datetime
import moviepy.editor as mp
from model import *
from sqlmodel import Session, select, func
from dotenv import load_dotenv
load_dotenv()

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from binascii import a2b_hex

key = os.getenv("Token_AES_Key").encode()
iv = os.getenv("Token_AES_IV").encode()
# 禁用 cuDNN（GTX 1080 Ti 兼容性）
os.environ["CT2_USE_CUDNN"] = "0"

import torch
torch.backends.cudnn.enabled = False

import argparse
import sys
from pathlib import Path


def download_video(video_url, output_dir="static/videos"):
    """
    使用 yt-dlp 从链接下载视频

    Args:
        video_url: 视频链接（支持 B站、YouTube 等）
        output_dir: 输出目录

    Returns:
        dict: {"filename": 下载的视频文件名, "title": 视频标题}
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 生成文件名
    filename = datetime.now().strftime("%Y%m%d_%H%M%S_%f.mp4")
    output_path = os.path.join(output_dir, filename)

    print(f"[INFO] 开始下载视频：{video_url}")

    # 获取 B站 cookie（解决 412 错误）
    cookies_args = ["--cookies-from-browser", "firefox"]

    # 先获取视频标题
    try:
        title_result = subprocess.run(
            ["yt-dlp", "--get-title", video_url] + cookies_args,
            capture_output=True, text=True, timeout=30
        )
        video_title = title_result.stdout.strip()
        if not video_title:
            video_title = filename.split(".")[0]
        # 清理标题中的非法字符
        video_title = "".join(c for c in video_title if c.isalnum() or c in (' ', '-', '_'))[:100]
    except Exception as e:
        print(f"[WARN] 获取视频标题失败：{e}，使用文件名作为标题")
        video_title = filename.split(".")[0]

    # 下载视频（stdout/stderr 直通终端，实时显示进度）
    cmd = [
        "yt-dlp",
        "-o", output_path,
        "-f", "bestvideo[ext=mp4][vcodec^=avc]+bestaudio[ext=m4a]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio",
        "--merge-output-format", "mp4",
        "--no-check-certificates",
    ] + cookies_args + [video_url]
    print(f"[INFO] 开始下载，进度将实时打印...")
    ret = subprocess.run(cmd)
    if ret.returncode != 0:
        raise Exception(f"yt-dlp 下载失败，退出码 {ret.returncode}")
    print(f"[INFO] 视频下载成功：{output_path}")

    return {"filename": filename, "title": video_title}


# 加密登录信息，并返回十六进制的Token
def aes_encrypt(source):
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_data = pad(source.encode(), AES.block_size)
    encrypted = cipher.encrypt(padded_data)
    return encrypted.hex()

# 对Token进行解密，获取到原始明文
def aes_decrypt(encrypted):
    decipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_padded = decipher.decrypt(a2b_hex(encrypted))
    decrypted = unpad(decrypted_padded, AES.block_size)
    return decrypted.decode()

# 此处Token的原文为用户信息，以|分隔：username|userid|role|realname|expiredtime
def check_token(token):
    timestamp = int(time.time())
    try:
        decrypted = aes_decrypt(token)
        temp_list = decrypted.split("|")
        expiredTime = temp_list[4]
        if timestamp > int(expiredTime):
            return {"message": "Token-Expired"}
        else:
            return {"message": "Token-OK", "username": temp_list[0], "userid": temp_list[1], "role": temp_list[2], "realname": temp_list[3]}
    except:
        return {"message": "Token-Error"}

# 检查视频编码是否为 H.264
def is_h264(video_path):
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=codec_name", "-of", "csv=p=0", video_path],
            capture_output=True, text=True, timeout=30
        )
        codec = result.stdout.strip()
        return codec in ("h264", "avc1")
    except Exception:
        return False


# 将视频文件转换为MP3音频文件，用于语音识别
def video_audio(filename):
    video_path = f"static/videos/{filename}"

    # 清理上次失败残留的临时文件
    tmp_file = f"{video_path}.tmp.mp4"
    if os.path.exists(tmp_file):
        os.remove(tmp_file)

    # 非 H.264 才需要转码
    if not is_h264(video_path):
        print(f"[INFO] 非 H.264 视频，使用 GPU 转码: {filename}")
        os.system(f'ffmpeg -y -i "{video_path}" -c:v h264_nvenc -preset medium -c:a aac -pix_fmt yuv420p -movflags +faststart "{tmp_file}"')
        if os.path.exists(tmp_file):
            os.replace(tmp_file, video_path)
    else:
        print(f"[INFO] 已是 H.264 格式，跳过转码: {filename}")

    video = mp.VideoFileClip(video_path)
    audio_name = f"{filename.split('.')[0]}.mp3"
    video.audio.write_audiofile(f'static/videos/{audio_name}')
    # 以字典形式返回音频文件的两个属性，用于后续保存到数据库中
    return {"audio_name": audio_name, "duration": video.duration}


# 对转写文本生成 AI 内容：总结、脑图、关键字、参考、考题
def gen_ai_content(content, filename):
    summary = summarize(content)

    xmind_json_raw = gen_xmind_json(content)
    try:
        xmind_json = json.loads(xmind_json_raw)
    except json.JSONDecodeError as e:
        print(f"[WARN] 脑图 JSON 解析失败: {e}，原始输出: {xmind_json_raw[:200]}")
        xmind_json = {
            "meta": {"name": "未识别", "author": "AI生成", "version": "1.0"},
            "format": "node_tree",
            "data": {"id": "root", "topic": "脑图生成失败", "children": []}
        }

    write_xmind_file(xmind_json, filename)
    keyword = xmind_json.get('meta', {}).get('name', '未识别')
    reference = gen_reference(keyword)
    examtext = gen_exam(content)
    return {
        "summary": summary,
        "xmind_json": xmind_json,
        "keyword": keyword,
        "reference": reference,
        "examtext": examtext,
    }


def transcribe(audio_path, model_size="large-v3", language="zh", output_format="txt", output_path=None, device="cuda"):
    """
    转写音频文件
    
    Args:
        audio_path: 音频文件路径
        model_size: 模型大小 (tiny/base/small/medium/large-v3)
        language: 语言代码 (zh/en等)
        output_format: 输出格式 (txt/srt/json)
        output_path: 输出文件路径（可选）
        device: 设备 (auto/cuda/cpu)
    """
    from faster_whisper import WhisperModel
    from tqdm import tqdm
    import torch

    # 自动检测设备
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"

    print(f"Loading model: {model_size} on {device}...")

    # 根据设备选择计算类型，如果 CUDA 失败则自动降级到 CPU
    try:
        if device == "cuda":
            model = WhisperModel(model_size, device="cuda", compute_type="int8")
        else:
            model = WhisperModel(model_size, device="cpu", compute_type="int8")
    except RuntimeError as e:
        if "CUDA" in str(e):
            print(f"CUDA 初始化失败：{e}，自动切换到 CPU 模式...")
            device = "cpu"
            model = WhisperModel(model_size, device="cpu", compute_type="int8")
        else:
            raise
    
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

    # 使用 tqdm 显示进度
    print("Transcribing segments...")
    all_segments = []
    total_segments = int(info.duration / 3)  # 预估片段数
    processed = 0
    for segment in segments:
        all_segments.append(segment)
        processed += 1
        # 每 10 个片段或最后一个片段显示一次进度
        if processed % 10 == 0:
            print(f"Progress: {processed} segments processed ({segment.end:.1f}s / {info.duration:.1f}s)")
    print(f"Transcribe complete: {len(all_segments)} segments total")
    
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

    # 返回转写文本（字典格式）
    return {"text": "\n".join([seg.text for seg in all_segments])}
# 将mp3音频文件转换为文本，本代码使用Whiper本地模型识别
# 也可以使用Paraformer或其他在线模型识别，速度相差不大，都比较耗时
def audio_text(filename):
    from transformers import pipeline
    transcriber = pipeline(task="automatic-speech-recognition",
                           model="openai/whisper-large-v3-turbo", device="cpu")
    result = transcriber(f"static/videos/{filename}", return_timestamps=True)
    return result["text"]

def summarize(text):
    # 最基础的提示词，完全的自然语言描述，无任何结构和段落
    # prompt = f'''以下文本内容来自老师上课录音，通过AI将其识别成文字，会存在一些口语化表述和识别错误的情况。
    # 请仔细理解给你的这段文字的内容，搞清楚这个老师究竟在讲什么内容，然后根据这段文字，形成一篇课程笔记。
    # 你可以更正内容中存在错误的地方，必要时也可以完善该段摘要，使表述更准确和连贯，总结尽量简洁明了一些。
    # 你不需要对存在的问题进行评论，只输出总结后的内容即可，请严格按照HTML格式输出，以便于在HTML页面中正常显示，
    # 输出HTML格式时不需要输出<html>和<body>等标签，而是正文内容即可。具体授课过程的文本内容如下：\n {text}'''

    # 使用结构化的提示加换行和#标记，让提示词结构更加清晰
    prompt = f'''
    #背景# \n以下文本内容来自老师上课录音，通过AI将其识别成文字，会存在一些口语化表述和识别错误的情况。\n
    #任务# \n请仔细理解给你的这段文字的内容，搞清楚这个老师究竟在讲什么内容，然后根据这段文字，形成一篇课程笔记。\n
    #要求# \n你可以更正内容中存在错误的地方，必要时也可以完善该段摘要，使表述更准确和连贯，总结尽量简洁明了一些。\n
    #输出# \n你不需要对存在的问题进行评论，只输出总结后的内容即可，请严格按照HTML格式输出，以便于在HTML页面中正常显示，
             输出HTML格式时不需要输出<html>和<body>等标签，而是正文内容即可。\n
    #输入# \n 具体授课过程的文本内容如下：\n {text}'''

    messages = [{'role':'system','content':'你是一名老师，擅长对课堂内容进行整理和总结'},
            {'role': 'user','content': prompt}]

    responses = dashscope.Generation.call(
            api_key=os.getenv('Dashscope_API_Key'),
            model="qwen-plus",
            messages=messages,
        )
    return responses.output.text

def gen_xmind_json(text):
    # 使用英文标签来说明提示词的结构
    prompt = '''<task>请根据该文本内容生成xmind格式的思维导图并提取1个关键字，你可以更正内容中存在错误的地方，
    必要时也可以完善该段摘要，使表述更准确和连贯，使思维导图的层次更加合理，提取到的1个关键字也更加准确。</task>\n
    <rules>请以JSON格式输出关键字和思维导图数据（node_tree类型），不需要进行额外的评论</rules>。\n输出的JSON格式为：
    <response_format>
    {"meta": {"name": "提取到的关键字",
              "author": "AI生成",
              "version": "1.0"
             },
     "format": "node_tree",
     "data": {
             "id": "可以按照顺序和章节生成，如1-1,2-3,3-4-2这类格式",
             "topic": "思维导图的节点内容",
             "children": ["此处以列表+字典的形式继续重复id,topic,children"]
    }}
    </response_format>，具体要参考的文本内容如下：\n ''' + text

    messages = [{'role': 'system', 'content': '你是一名老师，擅长将非结构化数据整理为思维导图'},
                {'role': 'user', 'content': prompt}]

    responses = dashscope.Generation.call(
        api_key=os.getenv('Dashscope_API_Key'),
        model="qwen-plus",
        messages=messages,
    )
    # 将大模型输出的 ```json和```的标识符去掉，变成可用的JSON字符串
    text = responses.output.text
    # 移除代码块标记
    text = text.replace("```json", "").replace("```", "")
    # 提取 JSON 部分（从第一个 { 到最后一个 }）
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        text = text[start:end+1]
    return text

# 利用xmind生成思维导图文件
def write_xmind_file(xmind_json, filename):
    # 定义函数用于递归读取和生成
    def add_node(parent, data):
        if isinstance(data, dict):
            parent.setTitle(data['topic'])
            # 如果存在children节点，则递归读取
            if 'children' in data:
                for child in data['children']:
                    topic = parent.addSubTopic()
                    add_node(topic, child)

    # 定义要生成的思维导图文件路径
    filename = f"static/xminds/{filename.split('.')[0]}.xmind"
    workbook = xmind.load(filename)
    sheet = workbook.getPrimarySheet()   # 获取第一个Sheet
    sheet.setTitle(xmind_json['meta']['name'])   # 设置Sheet的名称

    # 开始进行递归调用，将根节点作为第一个父节点进行调用
    add_node(sheet.getRootTopic(), xmind_json['data'])
    xmind.save(workbook)

def gen_exam(text):
    prompt = '''<task>请根据给你的文字内容所涉及到的所有知识点，出8个选择题和3个问答题。
        如果文本中给到的信息不足，你可以联网查询或自行拓展相关知识点的内容来生成对应的考题。
        注意，任何考题一定要跟对应的知识点相关联。</task>，请按照以下JSON结构来出题：
        <response_format>
            {"choices"：
            [{
                "question": "xxxxxxxx",
                "options": {
                             "A": "xxxxxxx",
                             "B": "xxxxxxx",
                             "C": "xxxxxxx",
                             "D": "xxxxxxx"
                },
                "answer": "A"
            }],
            "qas": 
            [{
                "question": "xxxxxxxxx",
                "answer": "xxxxxxxxxxx"
            }]
        </response_example>
        <rules>
        1. 尽量覆盖所有的知识点，允许有关联知识点进行适当扩展。
        2. 题目难度适中，题目难度较高的题目占比50%左右，相对简单的题目占比50%左右。
        3. 必须按照给出的json格式出题，最后请返回生成选择题和问答题的json字符串即可。
        4. 选择题和问答题的出题数目必须严格跟要求数量一致。
        </rules>
        具体要参考的文本内容如下：\n ''' + text

    messages = [{'role': 'system', 'content': '你是一名老师，擅长根据知识要点出各种对应的考试题目'},
                {'role': 'user', 'content': prompt}]

    responses = dashscope.Generation.call(
        api_key=os.getenv('Dashscope_API_Key'),
        model="qwen-plus",
        messages=messages,
    )
    return responses.output.text.replace("```json", "").replace("```", "")


def insert_exam(examtext, videoid):
    exam_json = json.loads(examtext)   # 将JSON字符串解析为JSON
    choices = exam_json['choices']     # 提取单选和简单题目
    qas = exam_json['qas']

    with Session(engine) as session:
        sql = select(Exams).where(Exams.videoid == videoid)
        # 如果已经在Exams中存在该视频的考题，则不再插入
        if len(session.execute(sql).all()) > 0:
            return

        # 遍历每一道单选题，并作为一行插入到exams表中
        for choice in choices:
            question = choice['question']
            answer = choice['answer']
            options = choice['options']   # options仍然为一个JSON，此处不再单独解析
            type = "choice"
            t_exam = Exams(videoid=videoid, question=question, answer=answer, type=type,
                           score=5, options=str(options), createtime=datetime.now())
            session.add(t_exam)
            session.commit()

        # 遍历每一道简答题，并作为一行插入到exams表中
        for qa in qas:
            question = qa['question']
            answer = qa['answer']
            type = "qa"
            t_exam = Exams(videoid=videoid, question=question, answer=answer,
                           type=type, score=20, createtime=datetime.now())
            session.add(t_exam)
            session.commit()

def gen_reference(keyword):
    # url = "http://default-w4yy.platform-cn-shanghai.opensearch.aliyuncs.com/v3/openapi/workspaces/default/web-search/ops-web-search-001"
    url = "http://default-3j53.platform-cn-shanghai.opensearch.aliyuncs.com/v3/openapi/workspaces/default/web-search/ops-web-search-001"
    
    header = {"Content-Type": "application/json", "Authorization": f"Bearer {os.getenv('Aliyun_Search_Key')}"}
    data = {"query": keyword, "top_k": 4}
    try:
        resp = requests.post(url, headers=header, json=data)
        result_json = resp.json()
        if 'result' in result_json:
            search_list = result_json['result']['search_result']
        elif 'data' in result_json:
            search_list = result_json['data'].get('search_result', [])
        else:
            print(f"Search API response format unexpected: {result_json}")
            search_list = []
        return str(search_list)
    except Exception as e:
        print(f"gen_reference error: {e}")
        return "[]"

# 读取视频里面的帧，并且进行对比，差异大的就认为是关键帧
def gen_key_frames(filepath):
    # 如果目录不存在，则以视频文件名创建目录，便于后续读取
    filename = filepath.split("/")[-1]
    if not os.path.exists(f"static/frames/{filename}"):
        os.mkdir(f"static/frames/{filename}")
    else:
        return   # 如果已经存在，说明已经生成过，不再生成

    key_frames = []   # 保存抽样帧图片
    cap = cv2.VideoCapture(filepath)
    # 获取视频的总帧数
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # 遍历所有帧，每500帧提取一张截图
    for i in range(frame_count):
        ret, frame = cap.read()   # 读取每一帧
        if i % 500 == 0:          # 每200帧抽样一帧，可根据实际情况修改间隔
            key_frames.append(frame)
    cap.release()

    # 遍历所有的抽样帧，并比较两者之间的差异，差异大则保存为关键帧
    for i in range(len(key_frames)-1):
        # 将彩色图片转换为灰度图，以减少比较运算的数据量
        prev_gray = cv2.cvtColor(key_frames[i], cv2.COLOR_BGR2GRAY)
        next_gray = cv2.cvtColor(key_frames[i+1], cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(prev_gray, next_gray)   # 比较两张图片之间的差异
        diff_avg = np.average(diff)      # 取差异的平均值

        # 0.8被视为差异较大，该值可能需要在具体操作时进行测试和调整
        if diff_avg > 0.8:
            # 将关键帧保存到文件夹中
            cv2.imwrite(f"static/frames/{filename}/{i}.jpg", key_frames[i+1])

def ai_score(user_answer, userid, examid, question, ai_answer):
    prompt = f'''这是一道简答题，题目内容是：\n {question} \n，你是一名老师，需要对该题目进行评分。
    其中，本题总分为：20分，而系统也给出了一个参考答案：\n {ai_answer} \n，
    请你根据该参考答案，对学生提供的答案进行准确的评分，学生的答案为：\n {user_answer} \n，
    请注意：对其进行评分后，直接输出一个纯数字的分数，不需要做任何评论或输出其他内容。
    '''

    messages = [{'role': 'system', 'content': '你是一名老师，擅长对学生的简答题进行准确的评分'},
                {'role': 'user', 'content': prompt}]

    responses = dashscope.Generation.call(
        api_key=os.getenv('Dashscope_API_Key'),
        model="qwen-plus",
        messages=messages,
        temperature=0.5,   # 减少温度参数，使相同答案的评分尽量相同
    )
    score = int(responses.output.text)
    return score


def insert_score(userid, videoid, examid, answer, score):
    with Session(engine) as session:
        score = Scores(userid=userid, videoid=videoid, examid=examid,
                answer=answer, score=score, createtime=datetime.now())
        session.add(score)
        session.commit()


_marker_model_cache = None


def _pdf_to_md_pymupdf(pdf_path, output_path):
    """使用 pymupdf 转换简单文本 PDF，根据字体大小判断标题层级"""
    import pymupdf as fitz

    doc = fitz.open(pdf_path)
    md_lines = []
    font_sizes = []

    # 第一遍：收集所有字体大小用于确定标题阈值
    for page in doc:
        blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        font_sizes.append((span["size"], span["font"]))

    doc.close()

    if not font_sizes:
        raise ValueError("PDF 中没有可提取的文本")

    font_sizes.sort(reverse=True)
    # 去重（保留差异明显的字体大小）
    unique_sizes = []
    for size, _ in font_sizes:
        if not unique_sizes or size < unique_sizes[-1] - 0.5:
            unique_sizes.append(size)

    # 第二遍：生成 Markdown
    doc = fitz.open(pdf_path)
    for page in doc:
        blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
        for block in blocks:
            if "lines" not in block:
                continue
            # 判断块类型（0=文本，1=图片）
            if block.get("type") == 1:
                continue  # 跳过图片块

            # 获取块中最大字体大小
            max_font_size = 0
            for line in block["lines"]:
                for span in line["spans"]:
                    if span["size"] > max_font_size:
                        max_font_size = span["size"]

            # 确定标题层级
            heading_level = None
            for i, hs in enumerate(unique_sizes[:5]):
                if abs(max_font_size - hs) < 0.5:
                    heading_level = i + 1
                    break

            # 提取文本行
            for line in block["lines"]:
                line_text = "".join(span["text"] for span in line["spans"]).strip()
                if not line_text:
                    continue

                if heading_level and heading_level <= 3:
                    prefix = "#" * (heading_level + 1)
                    md_lines.append(f"{prefix} {line_text}")
                else:
                    md_lines.append(line_text)
            md_lines.append("")  # 块之间空行

    doc.close()
    md_text = "\n".join(md_lines)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md_text)

    return md_text


def _pdf_to_md_marker(pdf_path, output_path):
    """使用 marker-pdf 转换复杂 PDF（含表格/公式/扫描件），输出高质量 Markdown"""
    global _marker_model_cache

    if _marker_model_cache is None:
        from marker.models import create_model_dict
        print("[INFO] marker-pdf 正在加载模型，首次调用较慢...")
        _marker_model_cache = create_model_dict()
        print("[INFO] marker-pdf 模型加载完成")

    from marker.config.parser import ConfigParser

    config_parser = ConfigParser({"output_format": "markdown"})
    converter_cls = config_parser.get_converter_cls()
    converter = converter_cls(
        config=config_parser.generate_config_dict(),
        artifact_dict=_marker_model_cache,
        processor_list=config_parser.get_processors(),
        renderer=config_parser.get_renderer(),
    )
    rendered = converter(pdf_path)
    md_text = rendered.markdown
    images = rendered.images if hasattr(rendered, 'images') else {}

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md_text)

    # 保存提取的图片
    if images:
        img_dir = Path(output_path).parent / f"{Path(output_path).stem}_images"
        img_dir.mkdir(parents=True, exist_ok=True)
        for name, img in images.items():
            img_path = img_dir / name
            img.save(img_path)
            # 替换 markdown 中的图片路径
            md_text = md_text.replace(f"images/{name}", str(img_path))
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md_text)

    return md_text


def _pdf_page_to_base64_image(pdf_path, page_idx, dpi=300):
    """将 PDF 指定页转换为 base64 编码的 JPEG 图片"""
    import pymupdf as fitz
    import base64

    doc = fitz.open(pdf_path)
    page = doc[page_idx]
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    img_bytes = pix.tobytes("jpeg")
    doc.close()

    return base64.b64encode(img_bytes).decode("utf-8")


def _pdf_to_md_qwen_vl(pdf_path, output_path):
    """使用 Qwen3-VL 云端模型将扫描件/手写版 PDF 转换为 Markdown"""
    import base64
    import dashscope
    import pymupdf as fitz

    api_key = os.getenv("Dashscope_API_Key")
    if not api_key:
        raise ValueError("未找到 Dashscope_API_Key 环境变量")
    dashscope.api_key = api_key

    doc = fitz.open(pdf_path)
    page_count = len(doc)
    doc.close()

    prompt = """你是一个专业的文档识别助手。请仔细识别图片中的所有文字内容，包括文字、标题、公式、表格等，
并按照 Markdown 格式输出完整的文档内容。

要求：
1. 标题使用 # 标记，层级清晰
2. 公式使用 LaTeX 格式（行内 $...$，独立 $$...$$）
3. 表格使用 Markdown 表格格式
4. 列表、粗体、斜体等格式要保留
5. 手写体内容要尽量准确识别
6. 直接输出 Markdown 内容，不需要额外解释
7. 这是第{page_num}页的内容，请确保内容完整连贯
""".strip()

    md_pages = []

    total_input = 0
    total_output = 0
    total_image = 0

    for i in range(page_count):
        print(f"[INFO] 正在识别第 {i+1}/{page_count} 页 ...")

        img_base64 = _pdf_page_to_base64_image(pdf_path, i, dpi=200)

        messages = [
            {
                "role": "user",
                "content": [
                    {"image": f"data:image/jpeg;base64,{img_base64}"},
                    {"text": prompt.format(page_num=i+1)},
                ]
            }
        ]

        max_retries = 3
        for retry in range(max_retries):
            try:
                response = dashscope.MultiModalConversation.call(
                    model="qwen-vl-plus",
                    messages=messages,
                    top_p=0.01,
                    temperature=0.01,
                )

                if response.status_code == 200:
                    page_md = response.output.choices[0].message.content[0]["text"]
                    md_pages.append(page_md)

                    # 提取 token 用量
                    usage = response.usage if hasattr(response, "usage") else {}
                    in_tokens = usage.get("input_tokens", 0)
                    out_tokens = usage.get("output_tokens", 0)
                    img_tokens = usage.get("image_tokens", 0)
                    total_input += in_tokens
                    total_output += out_tokens
                    total_image += img_tokens

                    print(f"[OK] 第 {i+1} 页识别完成 ({len(page_md)} 字符, input={in_tokens}, output={out_tokens}, image={img_tokens})")
                    break
                else:
                    print(f"[WARN] 第 {i+1} 页请求失败 (status={response.status_code}): {response.message}")
                    if retry < max_retries - 1:
                        import time
                        time.sleep(2 ** retry)
                    else:
                        md_pages.append(f"\n--- 第 {i+1} 页识别失败 ---\n")
            except Exception as e:
                print(f"[WARN] 第 {i+1} 页请求异常: {e}")
                if retry < max_retries - 1:
                    import time
                    time.sleep(2 ** retry)
                else:
                    md_pages.append(f"\n--- 第 {i+1} 页识别失败 ---\n")

    md_text = "\n\n---\n\n".join(md_pages)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md_text)

    # 计算费用（qwen-vl-plus: 输入1元/百万token, 输出10元/百万token）
    input_cost = total_input * 1.0 / 1_000_000
    output_cost = total_output * 10.0 / 1_000_000
    total_cost = input_cost + output_cost

    print(f"\n=== Token 用量统计 ===")
    print(f"输入 token: {total_input:,}")
    print(f"图片 token: {total_image:,}")
    print(f"输出 token: {total_output:,}")
    print(f"输入费用: {input_cost:.4f} 元")
    print(f"输出费用: {output_cost:.4f} 元")
    print(f"总费用: {total_cost:.4f} 元")
    print(f"=====================\n")

    return md_text


def pdf_to_md(pdf_path, output_path=None, method="auto"):
    """
    将 PDF 文件转换为 Markdown 文档

    Args:
        pdf_path: PDF 文件路径
        output_path: 输出 MD 文件路径（可选，默认与 PDF 同目录同名 .md）
        method: 转换方式
            - "auto"     自动判断（纯文本用 pymupdf，扫描件/复杂用 marker）
            - "pymupdf"  强制使用 pymupdf（快，适合纯文本 PDF）
            - "marker"   强制使用 marker（慢但质量高，适合含表格/公式的 PDF）
            - "qwen-vl"  使用 Qwen3-VL 云端模型（快，适合手写/扫描 PDF，按页收费）
    Returns:
        dict: {"md_path": md文件路径, "md_text": markdown文本, "pages": 页数}
    """
    import pymupdf as fitz

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")

    if output_path is None:
        output_path = Path(pdf_path).with_suffix(".md")
    else:
        output_path = str(output_path)

    doc = fitz.open(pdf_path)
    page_count = len(doc)

    if method == "auto":
        # 扫描第一页判断是否有文本
        first_page_text = doc[0].get_text().strip()
        if first_page_text:
            method = "pymupdf"
            print(f"[INFO] 检测到文本 PDF，使用 pymupdf 转换")
        else:
            method = "qwen-vl"
            print(f"[INFO] 检测到扫描 PDF，使用 Qwen3-VL 云端识别（速度快，成本约0.003元/页）")
        doc.close()

    try:
        if method == "pymupdf":
            md_text = _pdf_to_md_pymupdf(pdf_path, output_path)
        elif method == "marker":
            md_text = _pdf_to_md_marker(pdf_path, output_path)
        elif method == "qwen-vl":
            md_text = _pdf_to_md_qwen_vl(pdf_path, output_path)
        else:
            raise ValueError(f"不支持的转换方式: {method}")

        print(f"[INFO] PDF 转 MD 完成: {output_path} ({page_count} 页)")
        return {"md_path": output_path, "md_text": md_text, "pages": page_count}
    except Exception as e:
        print(f"[WARN] {method} 转换失败: {e}，回退到 marker")
        md_text = _pdf_to_md_marker(pdf_path, output_path)
        return {"md_path": output_path, "md_text": md_text, "pages": page_count}


if __name__ == '__main__':
    pass

    # source = "woniu|123456|2"
    # encrypted = aes_encrypt(source)
    # print(encrypted)
    # decrypted = aes_decrypt(encrypted)
    # print(decrypted)

    # text = audio_text("test.mp3")
    # print(text)

    # text = "我们来看一看啊 关于这个矩阵乘法这也是我们科学运算里边啊大批量数据处理的时候也经常用到的一种算法啊这一种惩罚方式呢它呢 针对的是两个矩阵 也就是二维数组了 对吧二维数组就是一个矩阵嘛 对不对就是一个二维数组针对这个二维数组那么矩正乘法这个就是我们矩正里边的一种很特殊的情况那么矩正比方说这是A大A这是一个矩正这个矩正对应的是不是一个三行两列你用二位书主表示就是一个是不是三行两列B呢是一个两行一列对吧两行一列好那么最后这个矩正乘法算出来的结果是什么呢注意算出来的结果是三行一列这里面就以据乘乘法就有一个要求M行N列只能和N行P列这个列前一个矩阵的列和后一个矩阵的行必须是一样大的比方说我有一个矩阵是三行四列那我要乘的另外一个矩阵它必须是四行它必须是四行多少列无所谓三列也行四列也行五列也行那最后这两个矩阵乘法乘出来的结果是多少三行五列这个怎么算的来我们来看一看这边算法是这样的算法是这样的比方说A11 A12这是不是一个三行两列加上两行一列他们的算法就是A11乘以B11加上A12乘以B21是这样来算的这个和这个这个和这个算出来的结果等于什么等于他们的第一个值好这一行呢又和这个这个A2又和B21算出来的结果呢又等于这个这个和它相乘然后这个呢又和它相乘算出来结果等于第三个那你自己先看一看那么也就是说针对M乘以N的一个矩阵和N乘一个P的矩阵他们俩才能正常的做矩阵乘法注意这根点击啊点乘是不一样的矩正存法那这是三行两列那这边两行四列运算出来的结果就是三行四列它怎么算的来我给大家看看19是怎么算的两行三列三行两列嘛那就1乘以那个1乘以3得到的是3完了以后加上3乘以2得到了16那就得到第一个值9这是不是还有几列刚才这个是一列嘛这边是四列了那就继续写一下1和33和2得到一个什么9然后接下来又1和63和73和7得到27接下来是1和93和83和824得到33接下来是1乘以43乘以3等于13好 接下来又开始第二行第二行是什么那就5乘以3加上2乘以2等于什么19然后5乘以7加上不是7加乘以65乘以6加上2乘以72714575630444明白这意思了吗这样呢就是我们的矩阵乘法的运算规则好现在呢我来给大家稍微的定义这么两个矩阵n d 1等于 np 点 array二维的 1234或者我们就用这个好了135204好135250 4 是不是定义了一个三行两类N第二呢 我就定义两行四两五六来的四列 那就36943694 在第一行对吧 第二行2783那么我们来看看NP.DOTND1ND2他们的矩正乘法乘出来的结果是不是这个数92733131944是不是这个数OK这个叫矩正乘法对应简单来说就是对应位置的行和对应位置的列相乘最终M乘N乘以N乘P得到的是M乘P的这么一个新的矩阵新的矩阵这个呢跟我们的卷积那种还有点像有点那个意思但是算法不一样对吧有点那个意思这个叫矩阵存法它可以让我们呢比较方便的对这些数据进行一个快速的批量的运算比较简洁调用一个dota就搞定了好这就是矩正惩罚有没有问题No.py里边内置的没有问题的话那我现在就要出今天的第一个作业利用原生python代码对两个二维列表进行矩正乘法运算进行一个不能使用任何第三方库包括number five只能有最原始的对两个二维列表我这边是不是定义的就是两个列表对吧两个列表但这个列表要通用啊然后呢对进行然后包封装到封装到这个方法函数函数metrics中然后里面的参数传的是什么list1 list2list1返回矩正乘法的结果返回矩正存法的结果 能听懂这个题目的要求吗啊 然后就是说呢我们使用最原始的方法 你们来用python手算一下啊 还是那种今天呢 还是让大家就是用比较纯粹的方式 但我给他讲了一些python化的编程方式哈 你能利用尽量利用 但是你不能使用第三方库啊 你说我直接调一下np点dota完事啊老师这个什么这个作业啊我们使用原生的当然明白这个意思啊自己去循环去算乘法再算加法再把它合并成一个什么新的二维数组新的二维数组好吧这是我们今天的第一个作业那么number pi呢我就先给大家去讲到这了其他的一些操作后边我们还会经常使用但基本操作我们都给大家讲过了你那明天就稍微的把这些操作快速的放几个列表出来念一念有点概念就行了然后后边用到的时候大家就这个正常用正常去使用它好吧这就是关于number pi的部分就给大家去梳理到这里就可以了我们学会我今天讲的这些number pi的基本操作就OK了不需要再去学别的了"
    # summary = summarize(text)
    # print(summary)

    # result = gen_xmind(text)
    # print(result)

    # exam = gen_exam(text, 1)
    # print(result)


    # key_frames("testcode/test.mp4")


    # question = "请简述矩阵乘法的基本规则，并说明其与点乘的区别。"
    # ai_answer = "矩阵乘法的基本规则是：两个矩阵相乘的前提是第一个矩阵的列数必须等于第二个矩阵的行数。结果矩阵的行数等于第一个矩阵的行数，列数等于第二个矩阵的列数。每个元素的值是由第一个矩阵的某一行与第二个矩阵的某一列对应元素相乘再求和得到的。而点乘是指两个相同维度的向量或矩阵对应位置元素相乘并求和，结果是一个标量值，而不是一个矩阵。"
    # user_answer = "两个矩阵相乘的前提是第一个矩阵的列数必须等于第二个矩阵的行数。结果矩阵的行数等于第一个矩阵的行数，列数等于第二个矩阵的列数。"
    # ai_score(user_answer, userid=1, examid=1, question=question, ai_answer=ai_answer)

    # # 以单引号分隔的JSON字符串，只能使用eval
    # data = "{'A': '选项一', 'B': '选项二', 'C': '选项三', 'D': '选项四'}"
    # print(eval(data))
    # print(json.loads(data))  # 报错, json.loads必须要求双引号
    # # 以双引号分隔的JSON字符串，两者均可以使用
    # data2 = '{"A": "选项一", "B": "选项二", "C": "选项三", "D": "选项四"}'
    # print(eval(data2))
    # print(json.loads(data2))