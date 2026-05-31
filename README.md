# AutoContentPipeline

AI 课程学习平台，基于阿里云通义千问（Qwen）对教学视频进行自动处理，生成课程笔记、思维导图（XMind）、考试题目和关键帧。

## 功能

- **视频上传**：支持本地上传或通过 URL（B站等）下载视频
- **文本上传**：支持上传 `.md` / `.txt` 文本文件
- **PDF 上传**：支持上传 PDF，自动识别（纯文本用 PyMuPDF，扫描件用 Qwen-VL 云端 OCR）
- **AI 内容生成**：
  - 课程笔记（Qwen-plus）
  - 思维导图 XMind（Qwen-plus）
  - 考试题目：8 道选择题 + 3 道简答题（Qwen-plus）
  - 参考资料（阿里云 OpenSearch）
- **视频转文字**：faster-whisper 本地识别，结果缓存避免重复转写
- **关键帧提取**：OpenCV 提取视频关键帧
- **考试系统**：选择题自动评分，简答题 AI 评分
- **流式聊天**：基于 Qwen 的流式问答接口
- **AES Token 认证**：24 小时有效期的加密 Token

## 技术栈

| 类别 | 技术 |
|------|------|
| 后端 | FastAPI + Uvicorn |
| 数据库 | MySQL (SQLModel ORM) |
| AI 大模型 | 阿里云通义千问 Qwen-plus、Qwen3-VL |
| 语音识别 | faster-whisper (local) |
| PDF 识别 | PyMuPDF、marker-pdf、Qwen-VL |
| 思维导图 | xmind |
| 视频处理 | moviepy、OpenCV |
| 前端 | Jinja2 Templates + vanilla JS |
| 安全 | PyCryptodome (AES-CBC Token) |

## 快速开始

### 1. 环境准备

```bash
cd chapter07
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件：

```env
# Token 加密密钥
Token_AES_Key=your_aes_key_16_chars
Token_AES_IV=your_aes_iv_16_chars

# 阿里云 Dashscope API Key
Dashscope_API_Key=sk-xxxxxxxxxxxxxxxx

# 阿里云 OpenSearch 搜索 API Key
Aliyun_Search_Key=OS-xxxxxxxxxxxx

# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_NAME=llm_lesson
DB_USER=root
DB_PASSWORD=your_password
```

### 3. 数据库初始化

```bash
# 执行 SQL 初始化脚本
mysql -u root -p llm_lesson < course.sql
```

### 4. 运行

```bash
# 启动 Web 服务
python main.py

# 后台任务（可选，用于处理已有视频中缺失的 AI 内容）
python schedule.py
```

服务默认运行在 `http://localhost:8000`。

## 项目结构

```
chapter07/
├── main.py           # FastAPI 应用：路由、上传、考试处理
├── model.py          # SQLModel 数据库模型（Users、Videos、Exams、Scores）
├── module.py         # AI 处理核心模块（语音识别、摘要、脑图、考试、OCR）
├── schedule.py       # 后台定时任务，补齐已有视频缺失的 AI 内容
├── course.sql        # 数据库初始化 SQL 脚本
├── insert_test_users.py  # 插入测试用户数据
├── templates/        # HTML 模板（首页、详情、考试、答案等）
├── static/           # 静态资源（视频、音频、帧、脑图、样式、脚本）
├── testcode/         # 测试/实验脚本
├── audio_to_text.py  # 独立音频转写脚本
└── .env              # 环境变量（已加入 .gitignore）
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 首页，显示所有课程 |
| GET | `/detail/{videoid}` | 课程详情（视频、笔记、脑图、关键帧） |
| GET | `/exam/{videoid}` | 考试页面 |
| POST | `/login` | 用户登录，返回 AES Token |
| POST | `/checklogin` | 验证 Token |
| POST | `/upload` | 上传视频文件 |
| POST | `/upload-url` | 通过 URL 下载视频 |
| POST | `/upload-text` | 上传 md/txt 文本 |
| POST | `/upload-pdf` | 上传 PDF 文件 |
| POST | `/exam/submit/{videoid}/{token}` | 提交考试答案 |
| POST | `/stream` | 流式 AI 聊天 |
| GET | `/answer/{videoid}` | 查看答案（需已考试） |
| GET | `/review/{videoid}` | 考试对比回顾 |

## 安全注意

- `.env` 文件已加入 `.gitignore`，请勿提交包含密钥的配置文件
- Token 有效期 24 小时，使用 AES-CBC 加密
- 考试系统通过 Token 验证学生身份后才允许提交
- 简答题由 AI 自动评分，评分温度参数为 0.5（保证相同答案得分一致）
