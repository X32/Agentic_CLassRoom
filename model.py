from sqlmodel import create_engine, Field, SQLModel, Column
from sqlalchemy.dialects.mysql import LONGTEXT
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "llm_backend")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

class Users(SQLModel, table=True):
    userid: Optional[int] = Field(default=None, primary_key=True)
    username: str
    password: str
    realname: str
    role: str
    createtime: datetime

class Videos(SQLModel, table=True):
    videoid: Optional[int] = Field(default=None, primary_key=True)
    videotitle: str
    filename: str
    video_url: str = Field(default="")
    duration: int
    coursename: str
    content: str = Field(sa_column=Column(LONGTEXT))
    summary: str = Field(sa_column=Column(LONGTEXT))
    keyword: str
    reference: str
    xmindjson: str = Field(sa_column=Column(LONGTEXT))
    examjson: str = Field(sa_column=Column(LONGTEXT))
    createtime: datetime

class Exams(SQLModel, table=True):
    examid: Optional[int] = Field(default=None, primary_key=True)
    videoid: Optional[int] = Field(default=None, foreign_key="videos.videoid")
    question: str
    type: str
    answer: str
    score: int
    options: str
    createtime: datetime

class Scores(SQLModel, table=True):
    scoreid: Optional[int] = Field(default=None, primary_key=True)
    userid: Optional[int] = Field(default=None, foreign_key="users.userid")
    videoid: Optional[int] = Field(default=None, foreign_key="videos.videoid")
    examid: Optional[int] = Field(default=None, foreign_key="exams.examid")
    answer: str
    score: int
    createtime: datetime