import uvicorn, json, os
from datetime import datetime
from fastapi import FastAPI, Request, Body, UploadFile, Form, File
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from model import *
from sqlmodel import Session, select, desc, func
from module import *
from openai import OpenAI

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 首页渲染
@app.get("/chat")
def chat(request: Request):
    with Session(engine) as session:
        sql = select(Videos).order_by(desc(Videos.videoid))
        videos = session.execute(sql).mappings().all()
    return templates.TemplateResponse(request=request, name="chat-md.html", context={"results": videos})

@app.get("/detail/{videoid}")
def detail(request: Request, videoid):
    with Session(engine) as session:
        sql = select(Videos).where(Videos.videoid == videoid)
        video = session.execute(sql).mappings().first()
        references = eval(video.Videos.reference)
        # 将 xmindjson 解析为 Python 字典，并使用 json.dumps 转换为标准 JSON 字符串
        # 然后使用 tojson 过滤器在模板中安全输出
        xmind_data = json.loads(video.Videos.xmindjson)

    # 读取 Key Frames 关键帧目录下的文件名，并响应给前端显示
    filename = video.Videos.filename
    frames_path = f"static/frames/{filename}"
    keyframes = os.listdir(frames_path) if os.path.exists(frames_path) else []
    return templates.TemplateResponse(request=request, name="detail.html", context={"video": video.Videos, "references":references, "keyframes":keyframes, "xmind_data": xmind_data})

@app.post("/login")
def login(logins: dict = Body()):
    username = logins["username"]
    password = logins["password"]
    with Session(engine) as session:
        sql = select(Users).where(Users.username == username)
        users = session.execute(sql).mappings().all()
        # 如果找到用户名且密码相等，则登录验证通过
        if len(users) == 1:
            if users[0].Users.password == password:
                userid = str(users[0].Users.userid)
                realname = users[0].Users.realname
                role = users[0].Users.role
                expiredTime = int(time.time()) + 60*60*24
                # 将用户基本信息以 | 分隔，加上有效期一起进行加密，构成一个加密解密型的 Token
                token = aes_encrypt(f"{username}|{userid}|{role}|{realname}|{expiredTime}")
                return {"message": "login-ok", "token": token, "realname": realname}
            else:
                return {"message": "login-fail"}
        else:
            return {"message": "user-not-exist"}

@app.post("/checklogin")
def checklogin(token: dict = Body()):
    token = token["token"]
    message = check_token(token)
    return message

# 上传视频并进行后续处理（文件上传）
@app.post("/upload")
def upload(title: str = Form(), course: str = Form(), file: UploadFile = File()):
    video_file = file.file.read()
    filename = datetime.now().strftime("%Y%m%d_%H%M%S_%f.mp4")
    with open(f"static/videos/{filename}", "wb") as f:
        f.write(video_file)

    # 将视频转换为音频，并读取视频的时长，以 Dict 格式返回
    video_url = ""
    vadict = video_audio(filename)
    audio_name = vadict['audio_name']
    duration = vadict['duration']

    # 使用 transcribe 方法将音频转换为文字
    audio_path = f"static/videos/{audio_name}"
    txt_path = f"static/videos/{audio_name}.txt"  # 转写文本缓存文件

    # 检查是否已经转写过，避免重复转写
    if os.path.exists(txt_path):
        print(f"[INFO] 发现转写缓存：{txt_path}，直接读取")
        with open(txt_path, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        print(f"[INFO] 开始转写音频：{audio_path}")
        result = transcribe(audio_path, model_size="large-v3", language="zh", output_format="txt")
        content = result["text"]
        # 保存转写结果到文本文件，防止后续重复转写
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[INFO] 转写文本已保存：{txt_path}")

    aicontent = gen_ai_content(content, filename)
    summary = aicontent['summary']
    xmind_json = aicontent['xmind_json']
    keyword = aicontent['keyword']
    reference = aicontent['reference']
    examtext = aicontent['examtext']

    with Session(engine) as session:
        video=Videos(videotitle=title, filename=filename, video_url=video_url, duration=duration,
                      coursename=course, content=content, summary=summary,
                      keyword=keyword, reference=reference, examjson=examtext,
                      xmindjson=json.dumps(xmind_json, ensure_ascii=False), createtime=datetime.now())
        session.add(video)
        session.commit()
        session.refresh(video)    # 此处需要刷新一下才能获取到新增的 videoid

    insert_exam(examtext, video.videoid)

    # 生成关键帧
    video_path = f"static/videos/{filename}"
    print(f"[INFO] 开始生成关键帧：{video_path}")
    gen_key_frames(video_path)

    return "Upload-Complete"


# 通过链接上传视频（使用 yt-dlp 下载）
@app.post("/upload-url")
def upload_url(data: dict = Body()):
    video_url = data["video_url"]
    title = data.get("title", "")
    course = data.get("course", "其他")

    # 检查是否已下载过该 URL，避免重复下载
    with Session(engine) as session:
        existing = session.exec(
            select(Videos).where(Videos.video_url == video_url)
        ).first()
        if existing:
            print(f"[INFO] 视频已存在，跳过下载: {video_url} (videoid={existing.videoid})")
            return {
                "message": "Video already exists",
                "videoid": existing.videoid,
                "videotitle": existing.videotitle,
            }

    # 使用 yt-dlp 下载视频
    video_info = download_video(video_url)
    filename = video_info["filename"]
    if not title:
        title = video_info["title"]

    # 将视频转换为音频，并读取视频的时长
    vadict = video_audio(filename)
    audio_name = vadict['audio_name']
    duration = vadict['duration']

    # 使用 transcribe 方法将音频转换为文字
    audio_path = f"static/videos/{audio_name}"
    txt_path = f"static/videos/{audio_name}.txt"

    # 检查是否已经转写过
    if os.path.exists(txt_path):
        print(f"[INFO] 发现转写缓存：{txt_path}，直接读取")
        with open(txt_path, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        print(f"[INFO] 开始转写音频：{audio_path}")
        result = transcribe(audio_path, model_size="large-v3", language="zh", output_format="txt")
        content = result["text"]
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[INFO] 转写文本已保存：{txt_path}")

    aicontent = gen_ai_content(content, filename)
    summary = aicontent['summary']
    xmind_json = aicontent['xmind_json']
    keyword = aicontent['keyword']
    reference = aicontent['reference']
    examtext = aicontent['examtext']

    with Session(engine) as session:
        video=Videos(videotitle=title, filename=filename, video_url=video_url, duration=duration,
                      coursename=course, content=content, summary=summary,
                      keyword=keyword, reference=reference, examjson=examtext,
                      xmindjson=json.dumps(xmind_json, ensure_ascii=False), createtime=datetime.now())
        session.add(video)
        session.commit()
        session.refresh(video)

    insert_exam(examtext, video.videoid)

    # 生成关键帧
    video_path = f"static/videos/{filename}"
    print(f"[INFO] 开始生成关键帧：{video_path}")
    gen_key_frames(video_path)

    return "Upload-Complete"


# 上传 md/txt 文本文件并生成笔记、脑图、考题
@app.post("/upload-text")
def upload_text(title: str = Form(), course: str = Form(), file: UploadFile = File()):
    if not file.filename.lower().endswith((".md", ".txt")):
        return {"message": "只支持 .md 或 .txt 文件"}

    file_content = file.file.read()
    ext = os.path.splitext(file.filename)[1].lower()
    filename = datetime.now().strftime(f"%Y%m%d_%H%M%S_%f{ext}")

    text_content = file_content.decode("utf-8")
    lines = len(text_content.splitlines())

    print(f"\n{'='*50}")
    print(f"[上传文本文件] 文件名: {filename}, 行数: {lines}, 字符数: {len(text_content)}")
    print(f"{'='*50}")
    print(text_content)
    print(f"{'='*50}")

    os.makedirs("static/docs", exist_ok=True)
    file_path = f"static/docs/{filename}"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text_content)

    aicontent = gen_ai_content(text_content, filename)
    summary = aicontent['summary']
    xmind_json = aicontent['xmind_json']
    keyword = aicontent['keyword']
    reference = aicontent['reference']
    examtext = aicontent['examtext'] 

    with Session(engine) as session:
        video = Videos(videotitle=title, filename=filename, video_url="",
                       duration=lines, coursename=course, content=text_content,
                       summary=summary, keyword=keyword, reference=reference,
                       examjson=examtext,
                       xmindjson=json.dumps(xmind_json, ensure_ascii=False),
                       createtime=datetime.now())
        session.add(video)
        session.commit()
        session.refresh(video)

    insert_exam(examtext, video.videoid)

    return "Upload-Complete"


# 上传 PDF 文件并生成笔记、脑图、考题
@app.post("/upload-pdf")
def upload_pdf(title: str = Form(), course: str = Form(), file: UploadFile = File()):
    if not file.filename.lower().endswith(".pdf"):
        return {"message": "只支持 PDF 文件"}

    pdf_file = file.file.read()
    filename = datetime.now().strftime("%Y%m%d_%H%M%S_%f.pdf")

    os.makedirs("static/pdfs", exist_ok=True)
    pdf_path = f"static/pdfs/{filename}"
    with open(pdf_path, "wb") as f:
        f.write(pdf_file)

    # PDF 转 Markdown
    print(f"[INFO] 开始转换 PDF: {filename}")
    md_result = pdf_to_md(pdf_path)
    content = md_result["md_text"]
    pages = md_result["pages"]

    aicontent = gen_ai_content(content, filename)
    summary = aicontent['summary']
    xmind_json = aicontent['xmind_json']
    keyword = aicontent['keyword']
    reference = aicontent['reference']
    examtext = aicontent['examtext']

    with Session(engine) as session:
        video=Videos(videotitle=title, filename=filename, video_url="",
                      duration=pages, coursename=course, content=content,
                      summary=summary, keyword=keyword, reference=reference,
                      examjson=examtext,
                      xmindjson=json.dumps(xmind_json, ensure_ascii=False),
                      createtime=datetime.now())
        session.add(video)
        session.commit()
        session.refresh(video)

    insert_exam(examtext, video.videoid)

    return "Upload-Complete"


@app.get("/exam/{videoid}")
def exam(request: Request, videoid):
    with (Session(engine) as session):
        # 查询跟视频关联的考题
        sql = select(Exams).where(Exams.videoid==videoid)
        exams = session.execute(sql).mappings().all()

        # 解析 exams 表中的 options，并且将其单独渲染给前端页面
        for exam in exams:
            if exam.Exams.options is not None:
                # 此处使用 eval，而不是 json.loads，原因是什么？
                exam.Exams.options = eval(exam.Exams.options)

        return templates.TemplateResponse(request=request, name="exam.html",
                context={"exams": exams})

@app.post("/exam/submit/{videoid}/{token}")
def exam_submit(videoid, token, answers: dict = Body()):
    # 判断用户是否已经登录，未登录的情况下，无法传递有效的 token
    if token is None:
        return "Need-Login"

    # 即使传递了一个无效 token，此处检查也无法通过，因为无法对 token 进行解密
    token_json = check_token(token)
    if token_json['message'] != "Token-OK":
        return "Token-Fail"
    elif token_json['role'] != 'student':
        return "Not-Student"

    userid = check_token(token)['userid']   # 解密 token 并读取用户 ID

    with Session(engine) as session:
        # 如果用户已经提交过考试结果，则不能继续提交
        sql = select(Scores).where(Scores.userid == userid).where(Scores.videoid == videoid)
        if len(session.execute(sql).all()) > 0:
            return "Already-Exam"

        score_list = []   # 用于记录每道题目的分数，以统计总分

        # 遍历每一个考题的答案
        for k, v in answers.items():
            sql = select(Exams).where(Exams.videoid == videoid)
            exams = session.execute(sql).mappings().all()
            # 从 exams 表中选取标准答案
            for exam in exams:
                if k == "choices":   # 单选题评分，只是对比即可
                    for choice in v:  # 提取到每一道题的 ID 和答案
                        examid = choice.split("-")[1]
                        answer = choice.split("-")[2]
                        # 如果与 exams 表中的 ID 相等，则说明是同一题，再比较答案
                        if (exam.Exams.examid == int(examid)):
                            if (exam.Exams.answer == answer):
                                insert_score(userid, videoid, examid, answer, 5)
                                score_list.append(5)
                            else:
                                insert_score(userid, videoid, examid, answer, 0)
                                score_list.append(0)
                else:
                    examid = k.split("-")[1]
                    answer = v    # 简答题直接通过 AI 判定分数
                    if (exam.Exams.examid == int(examid)):
                        score = ai_score(answer, userid, examid, exam.Exams.question, exam.Exams.answer)
                        insert_score(userid, videoid, examid, answer, score)
                        score_list.append(score)

        return sum(score_list)   # 计算总分并响应给前端


# 流式聊天接口
@app.post("/stream")
def stream_chat(question: dict = Body()):
    content = question['content']
    messages = [{'role': 'system', 'content': 'You are a helpful assistant.'},
                {"role": "user", "content": content}]

    def stream_gen():
        client = OpenAI(api_key=os.getenv("Dashscope_API_Key"),
                        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")

        completion = client.chat.completions.create(
            model="qwen-plus",
            messages=messages,
            stream=True,
            stream_options={"include_usage": False}
        )
        for chunk in completion:
            choice = chunk.choices[0].delta.content
            if choice:
                yield json.dumps({"content": choice}) + "\n"

    return StreamingResponse(stream_gen(), media_type="text/event-stream")


@app.get("/")
def index(request: Request, token: str = None):
    with Session(engine) as session:
        sql = select(Videos).order_by(desc(Videos.videoid))
        videos = session.execute(sql).mappings().all()

    # 如果传递了 token，查询每个视频的用户得分
    user_scores = {}
    userid = None
    if token:
        token_json = check_token(token)
        if token_json.get('message') == 'Token-OK':
            userid = token_json.get('userid')
            # 查询该用户的所有分数记录
            sql = select(Scores.userid, Scores.videoid, func.sum(Scores.score).label('total_score')).where(Scores.userid == userid).group_by(Scores.userid, Scores.videoid)
            scores = session.execute(sql).all()
            for s in scores:
                user_scores[s.videoid] = s.total_score

    # 将分数信息添加到视频中
    results = []
    for video in videos:
        videoid = video.Videos.videoid
        score = user_scores.get(videoid, None)
        # 如果有分数，说明可以查看答案
        can_view_answer = score is not None
        results.append({"video": video, "user_score": score, "can_view_answer": can_view_answer, "userid": userid})

    return templates.TemplateResponse(request=request, name="index.html", context={"results": results, "token": token})


@app.get("/index1")
def index1(request: Request, token: str = None):
    with Session(engine) as session:
        sql = select(Videos).order_by(desc(Videos.videoid))
        videos = session.execute(sql).mappings().all()

    user_scores = {}
    userid = None
    if token:
        token_json = check_token(token)
        if token_json.get('message') == 'Token-OK':
            userid = token_json.get('userid')
            sql = select(Scores.userid, Scores.videoid, func.sum(Scores.score).label('total_score')).where(Scores.userid == userid).group_by(Scores.userid, Scores.videoid)
            scores = session.execute(sql).all()
            for s in scores:
                user_scores[s.videoid] = s.total_score

    results = []
    for video in videos:
        videoid = video.Videos.videoid
        score = user_scores.get(videoid, None)
        can_view_answer = score is not None
        results.append({"video": video, "user_score": score, "can_view_answer": can_view_answer, "userid": userid})

    return templates.TemplateResponse(request=request, name="index1.html", context={"results": results, "token": token})


@app.get("/answer/{videoid}")
def answer(request: Request, videoid, token: str = None):
    # 检查用户是否登录
    if not token:
        return templates.TemplateResponse(request=request, name="error.html", context={"message": "请先登录"})

    token_json = check_token(token)
    if token_json.get('message') != 'Token-OK':
        return templates.TemplateResponse(request=request, name="error.html", context={"message": "Token 无效"})

    userid = token_json.get('userid')

    with Session(engine) as session:
        # 查询用户是否有该视频的分数
        sql = select(func.sum(Scores.score)).where(Scores.userid == userid).where(Scores.videoid == videoid)
        total_score = session.execute(sql).scalar()

        if total_score is None:
            # 没有分数，不能查看答案
            return templates.TemplateResponse(request=request, name="error.html", context={"message": "你还没有参加该视频的考试，无法查看答案"})

        # 查询该视频的所有考题和答案
        sql = select(Exams).where(Exams.videoid == videoid).order_by(Exams.examid)
        exams = session.execute(sql).mappings().all()

        # 解析选择题的 options 字段（从字符串转为字典），存储到单独的字典中
        exam_options = {}
        for exam in exams:
            examid = exam.Exams.examid
            if exam.Exams.options is not None:
                exam_options[examid] = eval(exam.Exams.options)
            else:
                exam_options[examid] = None

        # 查询用户的答案
        sql = select(Scores).where(Scores.userid == userid).where(Scores.videoid == videoid)
        user_answers = session.execute(sql).mappings().all()
        user_answer_dict = {a.Scores.examid: a.Scores.answer for a in user_answers}

    return templates.TemplateResponse(request=request, name="answer.html", context={
        "video_id": videoid,
        "exams": exams,
        "exam_options": exam_options,
        "user_answers": user_answer_dict,
        "total_score": total_score
    })


@app.get("/review/{videoid}")
def review(request: Request, videoid, token: str = None):
    # 检查用户是否登录
    if not token:
        return templates.TemplateResponse(request=request, name="error.html", context={"message": "请先登录"})

    token_json = check_token(token)
    if token_json.get('message') != 'Token-OK':
        return templates.TemplateResponse(request=request, name="error.html", context={"message": "Token 无效"})

    userid = token_json.get('userid')

    with Session(engine) as session:
        # 查询用户是否有该视频的分数
        sql = select(func.sum(Scores.score)).where(Scores.userid == userid).where(Scores.videoid == videoid)
        total_score = session.execute(sql).scalar()

        if total_score is None:
            return templates.TemplateResponse(request=request, name="error.html", context={"message": "你还没有参加该视频的考试，无法查看对比"})

        # 查询该视频的所有考题
        sql = select(Exams).where(Exams.videoid == videoid).order_by(Exams.examid)
        exams = session.execute(sql).mappings().all()

        # 解析选择题的 options 字段
        exam_options = {}
        for exam in exams:
            examid = exam.Exams.examid
            if exam.Exams.options is not None:
                exam_options[examid] = eval(exam.Exams.options)
            else:
                exam_options[examid] = None

        # 查询用户的答案和得分
        sql = select(Scores).where(Scores.userid == userid).where(Scores.videoid == videoid)
        user_answers = session.execute(sql).mappings().all()
        # 构建 {examid: {answer: xxx, score: xxx}} 字典
        user_result_dict = {}
        for a in user_answers:
            user_result_dict[a.Scores.examid] = {
                "answer": a.Scores.answer,
                "score": a.Scores.score
            }

        # 计算总分和正确题数
        correct_count = sum(1 for a in user_answers if a.Scores.score > 0)

    return templates.TemplateResponse(request=request, name="review.html", context={
        "video_id": videoid,
        "exams": exams,
        "exam_options": exam_options,
        "user_result_dict": user_result_dict,
        "total_score": total_score,
        "correct_count": correct_count,
        "total_count": len(exams)
    })


if __name__ == "__main__":
    #uvicorn.run(app)
    uvicorn.run(app, host="0.0.0.0", port=9000)
