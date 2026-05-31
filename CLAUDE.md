# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI 课程学习平台 - A FastAPI-based web application that processes educational videos using AI to generate course notes, mind maps (XMind), exam questions, and key frames.

## Tech Stack

- **Backend**: Python + FastAPI
- **Database**: MySQL (SQLModel ORM)
- **AI Models**: 
  - Dashscope (Qwen-plus) for text generation (summaries, mind maps, exams)
  - OpenAI Whisper for speech-to-text
  - Custom XMind generation
- **Frontend**: Jinja2 templates + vanilla JS

## Project Structure

```
chapter07/
├── main.py           # FastAPI app: routes, upload, exam handling
├── model.py          # SQLModel database models (Users, Videos, Exams, Scores)
├── module.py         # Core AI processing functions
├── schedule.py       # Background job for data enrichment
├── testcode/         # Test/experiment scripts
├── templates/        # Jinja2 HTML templates
├── static/           # Static assets (videos, frames, xminds, css, js)
└── .env              # Environment variables (AES keys, API keys)
```

## Core Modules

### model.py
SQLModel database schema with 4 tables:
- `Users`: User authentication (userid, username, password, role)
- `Videos`: Video metadata + AI-generated content (summary, xmindjson, examjson, etc.)
- `Exams`: Exam questions linked to videos (choice/qa types)
- `Scores`: User exam submissions and scores

### main.py (API Endpoints)
- `GET /` - Homepage with video list
- `GET /detail/{videoid}` - Video detail page with mind map and references
- `GET /exam/{videoid}` - Exam page for a video
- `POST /login` - User login with AES-encrypted token
- `POST /checklogin` - Token validation
- `POST /upload` - Video upload + AI processing pipeline
- `POST /exam/submit/{videoid}/{token}` - Exam submission with auto-grading

### module.py (AI Processing Functions)
- `aes_encrypt/decrypt()` - Token encryption (CBC mode)
- `check_token()` - Token validation with expiry check
- `video_audio()` - Extract audio from video (moviepy)
- `audio_text()` - Speech-to-text (Whisper-large-v3-turbo)
- `summarize()` - Generate course notes (Qwen-plus)
- `gen_xmind_json()` - Generate mind map JSON structure
- `write_xmind_file()` - Write XMind file
- `gen_exam()` - Generate exam questions (8 choices + 3 Q&A)
- `insert_exam()` - Save exam questions to database
- `gen_reference()` - Search related references (Aliyun OpenSearch)
- `gen_key_frames()` - Extract key frames from video (OpenCV)
- `ai_score()` - AI grading for Q&A questions
- `insert_score()` - Save exam scores

## Environment Variables (.env)

Required:
- `Token_AES_Key` - AES encryption key for JWT-like tokens
- `Token_AES_IV` - AES CBC IV
- `Dashscope_API_Key` - Alibaba Dashscope API key (Qwen models)
- `Aliyun_Search_Key` - Aliyun OpenSearch API key

## Database Connection

MySQL connection string in `model.py`:
```python
engine = create_engine("mysql+pymysql://qiang:123456@127.0.0.1:3306/course")
```

## Running the Application

```bash
# Start the main FastAPI server
python main.py

# Start background data enrichment job
python schedule.py

# Run test scripts (in testcode/)
python testcode/main.py
```

## Video Upload Flow

1. Upload video file → Save to `static/videos/`
2. Extract audio → `video_audio()`
3. Speech-to-text → `audio_text()` (Whisper)
4. Generate summary → `summarize()` (Qwen)
5. Generate mind map → `gen_xmind_json()` + `write_xmind_file()`
6. Generate references → `gen_reference()` (Aliyun Search)
7. Generate exam questions → `gen_exam()` + `insert_exam()`
8. Extract key frames → `gen_key_frames()` (OpenCV)

## Security Notes

- Token format: `username|userid|role|realname|expiredTime` (pipe-delimited, AES-CBC encrypted)
- Token expiry: 24 hours from login
- User roles: `student`, `admin` (role check in exam submission)

## Dependencies

Key packages: `fastapi`, `sqlmodel`, `uvicorn`, `dashscope`, `openai`, `moviepy`, `xmind`, `opencv-python`, `transformers`, `pycryptodome`
