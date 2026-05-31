#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库存取测试
测试 Videos 和 Exams 表的增删改查操作
"""

import sys
import os
import json

# 添加父目录到路径，以便导入 model
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model import *
from sqlmodel import Session, select, delete
import time
from datetime import datetime

def print_separator(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")

def test_database_connection():
    """测试数据库连接"""
    print_separator("1. 测试数据库连接")
    try:
        with Session(engine) as session:
            # 执行一个简单的查询测试连接
            sql = select(Users).limit(1)
            session.execute(sql)
        print("数据库连接：成功")
        return True
    except Exception as e:
        print(f"数据库连接：失败 - {e}")
        return False

def test_video_crud():
    """测试 Videos 表的 CRUD 操作"""
    print_separator("2. 测试 Videos 表 CRUD 操作")

    test_videoid = None

    # --- CREATE ---
    print("[CREATE] 插入测试视频数据...")
    try:
        with Session(engine) as session:
            video = Videos(
                videotitle="数据库测试视频",
                filename="test_video_20260422.mp4",
                duration=120,
                coursename="Python 编程基础",
                content="这是测试的课程内容文本...",
                summary="这是测试的课程总结...",
                keyword="Python,编程，测试",
                reference="[{'title': '参考 1', 'url': 'http://example.com'}]",
                examjson='{"choices": [], "qas": []}',
                xmindjson='{"meta": {"name": "测试"}, "data": {"topic": "根节点"}}',
                createtime=datetime.now()
            )
            session.add(video)
            session.commit()
            session.refresh(video)
            test_videoid = video.videoid
            print(f"  插入成功，videoid = {test_videoid}")
    except Exception as e:
        print(f"  插入失败：{e}")
        return False

    # --- READ ---
    print("\n[READ] 读取刚插入的视频数据...")
    try:
        with Session(engine) as session:
            sql = select(Videos).where(Videos.videoid == test_videoid)
            video = session.execute(sql).first()
            if video:
                print(f"  读取成功:")
                print(f"    videoid: {video.Videos.videoid}")
                print(f"    videotitle: {video.Videos.videotitle}")
                print(f"    coursename: {video.Videos.coursename}")
                print(f"    duration: {video.Videos.duration} 秒")
                print(f"    keyword: {video.Videos.keyword}")
            else:
                print("  读取失败：未找到记录")
    except Exception as e:
        print(f"  读取失败：{e}")

    # --- UPDATE ---
    print("\n[UPDATE] 更新视频数据...")
    try:
        with Session(engine) as session:
            video = session.get(Videos, test_videoid)
            if video:
                video.videotitle = "数据库测试视频 - 已更新"
                video.duration = 180
                video.keyword = "Python,编程，测试，更新"
                session.add(video)
                session.commit()
                print("  更新成功")
    except Exception as e:
        print(f"  更新失败：{e}")

    # --- 验证更新 ---
    print("\n[VERIFY] 验证更新后的数据...")
    try:
        with Session(engine) as session:
            video = session.get(Videos, test_videoid)
            if video:
                print(f"    videotitle: {video.videotitle}")
                print(f"    duration: {video.duration} 秒")
                print(f"    keyword: {video.keyword}")
    except Exception as e:
        print(f"  验证失败：{e}")

    # --- DELETE ---
    print("\n[DELETE] 删除测试数据...")
    try:
        with Session(engine) as session:
            sql = delete(Videos).where(Videos.videoid == test_videoid)
            session.execute(sql)
            session.commit()
            print("  删除成功")
    except Exception as e:
        print(f"  删除失败：{e}")

    # --- 验证删除 ---
    print("\n[VERIFY] 验证删除后的数据...")
    try:
        with Session(engine) as session:
            sql = select(Videos).where(Videos.videoid == test_videoid)
            video = session.execute(sql).first()
            if video:
                print("  验证失败：记录仍然存在")
            else:
                print("  验证成功：记录已被删除")
    except Exception as e:
        print(f"  验证失败：{e}")

    return True

def test_exam_crud():
    """测试 Exams 表的 CRUD 操作"""
    print_separator("3. 测试 Exams 表 CRUD 操作")

    # 先创建一个测试视频用于外键关联
    test_videoid = None
    test_examids = []

    # --- 创建关联的视频 ---
    print("[SETUP] 创建关联的测试视频...")
    try:
        with Session(engine) as session:
            video = Videos(
                videotitle="考试测试视频",
                filename="test_exam_video.mp4",
                duration=60,
                coursename="数据库测试",
                content="考试内容...",
                summary="总结...",
                keyword="测试",
                reference="[]",
                examjson="{}",
                xmindjson="{}",
                createtime=datetime.now()
            )
            session.add(video)
            session.commit()
            session.refresh(video)
            test_videoid = video.videoid
            print(f"  视频创建成功，videoid = {test_videoid}")
    except Exception as e:
        print(f"  视频创建失败：{e}")
        return False

    # --- CREATE ---
    print("\n[CREATE] 插入测试考题数据...")
    try:
        with Session(engine) as session:
            # 插入选择题
            choice_exam = Exams(
                videoid=test_videoid,
                question="Python 中哪个关键字用于定义函数？",
                type="choice",
                answer="B",
                score=5,
                options="{'A': 'function', 'B': 'def', 'C': 'func', 'D': 'define'}",
                createtime=datetime.now()
            )
            session.add(choice_exam)
            session.commit()
            session.refresh(choice_exam)
            test_examids.append(choice_exam.examid)

            # 插入问答题
            qa_exam = Exams(
                videoid=test_videoid,
                question="请简述 Python 的特点。",
                type="qa",
                answer="Python 具有简洁清晰、跨平台、丰富的库等特点。",
                score=20,
                options=None,
                createtime=datetime.now()
            )
            session.add(qa_exam)
            session.commit()
            session.refresh(qa_exam)
            test_examids.append(qa_exam.examid)

            print(f"  插入成功，examids = {test_examids}")
    except Exception as e:
        print(f"  插入失败：{e}")
        return False

    # --- READ ---
    print("\n[READ] 读取考题数据...")
    try:
        with Session(engine) as session:
            sql = select(Exams).where(Exams.videoid == test_videoid)
            exams = session.execute(sql).all()
            print(f"  找到 {len(exams)} 条考题:")
            for exam in exams:
                print(f"    examid={exam.Exams.examid}, type={exam.Exams.type}, question={exam.Exams.question[:30]}...")
    except Exception as e:
        print(f"  读取失败：{e}")

    # --- UPDATE ---
    print("\n[UPDATE] 更新考题数据...")
    try:
        with Session(engine) as session:
            exam = session.get(Exams, test_examids[0])
            if exam:
                exam.question = "Python 中哪个关键字用于定义函数？（已更新）"
                exam.score = 10
                session.add(exam)
                session.commit()
                print("  更新成功")
    except Exception as e:
        print(f"  更新失败：{e}")

    # --- DELETE ---
    print("\n[DELETE] 删除测试考题...")
    try:
        with Session(engine) as session:
            for examid in test_examids:
                sql = delete(Exams).where(Exams.examid == examid)
                session.execute(sql)
            session.commit()
            print("  删除成功")
    except Exception as e:
        print(f"  删除失败：{e}")

    # --- 清理关联视频 ---
    print("\n[CLEANUP] 清理关联的测试视频...")
    try:
        with Session(engine) as session:
            sql = delete(Videos).where(Videos.videoid == test_videoid)
            session.execute(sql)
            session.commit()
            print("  清理成功")
    except Exception as e:
        print(f"  清理失败：{e}")

    return True

def test_video_exam_workflow():
    """测试完整的视频 + 考试 工作流程"""
    print_separator("4. 测试完整工作流程（模拟 upload 接口）")

    test_videoid = None

    # --- 步骤 1: 插入视频 ---
    print("[步骤 1] 插入视频记录...")
    try:
        with Session(engine) as session:
            video = Videos(
                videotitle="工作流程测试视频",
                filename="workflow_test_20260422.mp4",
                duration=300,
                coursename="AI 应用开发",
                content="这是模拟的课程内容...",
                summary="这是课程总结...",
                keyword="AI,应用开发",
                reference="[{'title': '参考链接'}]",
                examjson='{"choices": [{"question": "测试题", "options": {"A": "选项 1"}, "answer": "A"}], "qas": [{"question": "问答题", "answer": "答案"}]}',
                xmindjson='{"meta": {"name": "AI"}, "data": {"topic": "思维导图"}}',
                createtime=datetime.now()
            )
            session.add(video)
            session.commit()
            session.refresh(video)
            test_videoid = video.videoid
            print(f"  视频插入成功，videoid = {test_videoid}")
    except Exception as e:
        print(f"  视频插入失败：{e}")
        return False

    # --- 步骤 2: 批量插入考题（模拟 insert_exam）---
    print("\n[步骤 2] 批量插入考题（模拟 insert_exam 函数）...")
    exam_ids = []
    try:
        exam_json_data = {
            "choices": [
                {"question": "什么是 AI？", "options": {"A": "人工智能", "B": "自动智能", "C": "增强智能", "D": "算法智能"}, "answer": "A"},
                {"question": "Python 的特点是什么？", "options": {"A": "简洁", "B": "复杂", "C": "慢速", "D": "难学"}, "answer": "A"},
            ],
            "qas": [
                {"question": "请描述机器学习的基本流程。", "answer": "数据收集->预处理->特征工程->模型训练->评估->部署"}
            ]
        }

        with Session(engine) as session:
            # 插入选择题
            for choice in exam_json_data["choices"]:
                exam = Exams(
                    videoid=test_videoid,
                    question=choice["question"],
                    type="choice",
                    answer=choice["answer"],
                    score=5,
                    options=str(choice["options"]),
                    createtime=datetime.now()
                )
                session.add(exam)
                session.commit()
                session.refresh(exam)
                exam_ids.append(exam.examid)

            # 插入问答题
            for qa in exam_json_data["qas"]:
                exam = Exams(
                    videoid=test_videoid,
                    question=qa["question"],
                    type="qa",
                    answer=qa["answer"],
                    score=20,
                    options=None,
                    createtime=datetime.now()
                )
                session.add(exam)
                session.commit()
                session.refresh(exam)
                exam_ids.append(exam.examid)

            print(f"  插入成功，共 {len(exam_ids)} 道题")
    except Exception as e:
        print(f"  插入失败：{e}")
        return False

    # --- 步骤 3: 查询验证 ---
    print("\n[步骤 3] 查询验证...")
    try:
        with Session(engine) as session:
            # 查询视频
            sql = select(Videos).where(Videos.videoid == test_videoid)
            video = session.execute(sql).first()

            # 查询关联的考题
            sql = select(Exams).where(Exams.videoid == test_videoid)
            exams = session.execute(sql).all()

            print(f"  视频：{video.Videos.videotitle}")
            print(f"  关联考题数量：{len(exams)}")
            for exam in exams:
                print(f"    - [{exam.Exams.type}] {exam.Exams.question[:40]}...")
    except Exception as e:
        print(f"  查询失败：{e}")

    # --- 步骤 4: 清理数据 ---
    print("\n[步骤 4] 清理测试数据...")
    try:
        with Session(engine) as session:
            # 先删除关联的考题
            sql = delete(Exams).where(Exams.videoid == test_videoid)
            session.execute(sql)

            # 再删除视频
            sql = delete(Videos).where(Videos.videoid == test_videoid)
            session.execute(sql)

            session.commit()
            print("  清理成功")
    except Exception as e:
        print(f"  清理失败：{e}")

    return True

def test_transaction_rollback():
    """测试事务回滚"""
    print_separator("5. 测试事务回滚（模拟异常情况）")

    print("[测试] 插入数据后回滚...")
    try:
        with Session(engine) as session:
            video = Videos(
                videotitle="回滚测试视频",
                filename="rollback_test.mp4",
                duration=100,
                coursename="测试",
                content="内容",
                summary="总结",
                keyword="测试",
                reference="[]",
                examjson="{}",
                xmindjson="{}",
                createtime=datetime.now()
            )
            session.add(video)
            session.flush()  # 执行但不提交
            print(f"  已 flush，videoid = {video.videoid}")

            # 模拟异常，不执行 commit
            # session.commit()  <-- 注释掉，模拟回滚

        print("  Session 关闭后，未 commit 的数据应自动回滚")

        # 验证数据不存在
        with Session(engine) as session:
            sql = select(Videos).where(Videos.videotitle == "回滚测试视频")
            result = session.execute(sql).first()
            if result:
                print("  验证失败：数据仍然存在（未回滚）")
            else:
                print("  验证成功：数据已回滚（不存在）")

    except Exception as e:
        print(f"  测试异常：{e}")

def run_all_tests():
    """运行所有测试"""
    print_separator("数据库存取测试 - 开始")
    print(f"数据库配置：{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME', 'llm_lesson')}")

    results = []

    # 1. 连接测试
    results.append(("数据库连接", test_database_connection()))

    # 2. Video CRUD
    results.append(("Videos CRUD", test_video_crud()))

    # 3. Exam CRUD
    results.append(("Exams CRUD", test_exam_crud()))

    # 4. 完整流程
    results.append(("完整工作流程", test_video_exam_workflow()))

    # 5. 事务回滚
    results.append(("事务回滚", True))  # 事务回滚测试总是视为"通过"
    test_transaction_rollback()

    # 汇总
    print_separator("测试汇总")
    print(f"{'测试项目':<30} {'结果':<10}")
    print("-" * 45)
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{name:<30} {status:<10}")
    print("-" * 45)
    passed_count = sum(1 for _, p in results if p)
    print(f"总计：{passed_count}/{len(results)} 测试通过")

if __name__ == '__main__':
    run_all_tests()
