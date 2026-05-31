import uvicorn
from fastapi import FastAPI, Request, Body, UploadFile, Form, File
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.responses import StreamingResponse
import json, os
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/chat")
def chat(request: Request):
    return templates.TemplateResponse(request=request, name="chat-md.html")


@app.get("/getxmind")
def get_xmind(request: Request):
    return FileResponse(path="static/test.xmind", filename="test.xmind")

@app.post("/stream")
def stream_chat(question: dict=Body()):
    content = question['content']
    messages = [{'role': 'system', 'content': 'You are a helpful assistant.'},
                {"role": "user", "content": content}]

    def stream_chat():
        client = OpenAI(api_key=os.getenv("Dashscope_API_Key"),
                        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")

        completion = client.chat.completions.create(
            model="qwen-plus",
            messages=messages,
            stream=True,
            stream_options={"include_usage": False}
        )
        for chunk in completion:
            # 使用生成器迭代输出每一个数据流
            choice = chunk.choices[0].delta.content
            yield json.dumps({"content": choice}) + "\n"

    # 以流式响应的方式响应给前端
    return StreamingResponse(stream_chat(), media_type="text/event-stream")

if __name__ == '__main__':
    uvicorn.run(app)