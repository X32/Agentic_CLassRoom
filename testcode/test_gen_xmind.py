#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 gen_xmind_json 方法
"""

import sys
import os
import json

# 添加父目录到路径，以便导入 module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from module import gen_xmind_json
import time

# 测试文本 1：矩阵乘法相关内容
test_text_1 = """
我们来看一看啊 关于这个矩阵乘法这也是我们科学运算里边啊大批量数据处理的时候
也经常用到的一种算法啊这一种惩罚方式呢它呢 针对的是两个矩阵 也就是二维数组了
对吧二维数组就是一个矩阵嘛 对不对就是一个二维数组针对这个二维数组那么矩正乘法
这个就是我们矩正里边的一种很特殊的情况那么矩正比方说这是 A 大 A 这是一个矩正
这个矩正对应的是不是一个三行两列你用二位书主表示就是一个是不是三行两列 B 呢
是一个两行一列对吧两行一列好那么最后这个矩正乘法算出来的结果是什么呢注意算出来
的结果是三行一列这里面就以据乘乘法就有一个要求 M 行 N 列只能和 N 行 P 列这个列
前一个矩阵的列和后一个矩阵的行必须是一样大的比方说我有一个矩阵是三行四列那我
要乘的另外一个矩阵它必须是四行它必须是四行多少列无所谓三列也行四列也行五列也行
那最后这两个矩阵乘法乘出来的结果是多少三行五列
"""

# 测试文本 2：Python 基础知识
test_text_2 = """
今天我们来讲一讲 Python 编程语言的基础知识。Python 是一种高级编程语言，
由 Guido van Rossum 于 1989 年发明。Python 的设计哲学强调代码的可读性和
简洁的语法。Python 支持多种编程范式，包括面向对象编程、函数式编程和
命令式编程。Python 的主要特点有：第一，语法简洁清晰，使用缩进来表示
代码块；第二，拥有丰富的标准库和第三方库；第三，跨平台运行；第四，
支持动态类型和自动内存管理。在数据类型方面，Python 提供了整数、浮点数、
字符串、列表、元组、字典等多种内置类型。列表是可变的有序序列，使用
方括号表示；元组是不可变的有序序列，使用圆括号表示；字典是键值对的
集合，使用花括号表示。控制结构方面，Python 支持 if-elif-else 条件语句，
for 循环和 while 循环。函数使用 def 关键字定义，可以接受参数并返回值。
Python 还支持面向对象编程，使用 class 关键字定义类，类可以包含属性和方法。
"""

# 测试文本 3：机器学习简介
test_text_3 = """
机器学习是人工智能的一个分支，它使计算机能够从数据中学习并做出决策或预测，
而无需明确编程。机器学习的主要类型包括：监督学习、无监督学习和强化学习。
监督学习使用带标签的训练数据，常见的算法有线性回归、逻辑回归、决策树、
随机森林、支持向量机和神经网络。无监督学习处理无标签数据，用于聚类、
降维和关联规则挖掘，常见算法包括 K-means 聚类、层次聚类和主成分分析。
强化学习通过与环境交互来学习最优策略，广泛应用于游戏、机器人和控制领域。
机器学习的工作流程通常包括：数据收集、数据预处理、特征工程、模型选择、
模型训练、模型评估和模型部署。深度学习是机器学习的一个子领域，使用多层
神经网络来学习数据的层次化表示，在图像识别、自然语言处理和语音识别等
领域取得了突破性进展。
"""

def print_separator(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")

def validate_xmind_json(json_str):
    """验证 XMind JSON 的结构"""
    errors = []

    # 检查是否为空
    if not json_str:
        errors.append("返回的 JSON 字符串为空")
        return errors

    # 尝试解析 JSON
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        errors.append(f"JSON 解析失败：{e}")
        return errors

    # 检查必需字段
    if 'meta' not in data:
        errors.append("缺少 'meta' 字段")
    else:
        if 'name' not in data['meta']:
            errors.append("meta 中缺少 'name' 字段（关键字）")
        else:
            print(f"  提取的关键字：{data['meta']['name']}")

    if 'format' not in data:
        errors.append("缺少 'format' 字段")
    elif data['format'] != 'node_tree':
        errors.append(f"format 字段值应为 'node_tree'，实际为 '{data['format']}'")

    if 'data' not in data:
        errors.append("缺少 'data' 字段")
    else:
        # 检查 data 结构
        if 'id' not in data['data']:
            errors.append("data 中缺少 'id' 字段")
        if 'topic' not in data['data']:
            errors.append("data 中缺少 'topic' 字段")
        else:
            print(f"  根节点主题：{data['data']['topic']}")

        # 检查 children（可选）
        if 'children' in data['data']:
            children = data['data']['children']
            print(f"  子节点数量：{len(children)}")
            # 递归检查 children 结构
            def check_children(children, level=1):
                for i, child in enumerate(children):
                    if 'topic' not in child:
                        errors.append(f"第{level}层子节点 [{i}] 缺少 'topic' 字段")
                    if 'children' in child:
                        check_children(child['children'], level+1)
            check_children(children)

    return errors

def test_gen_xmind_json():
    print_separator("gen_xmind_json 方法测试")

    test_cases = [
        ("测试 1：矩阵乘法", test_text_1),
        ("测试 2：Python 基础知识", test_text_2),
        ("测试 3：机器学习简介", test_text_3),
    ]

    results = []

    for title, text in test_cases:
        print_separator(title)
        print(f"输入文本长度：{len(text)} 字符")
        print("-" * 50)

        start_time = time.time()
        try:
            result = gen_xmind_json(text)
            elapsed = time.time() - start_time

            print(f"\n调用耗时：{elapsed:.2f} 秒")
            print(f"返回结果长度：{len(result)} 字符")

            print("\n原始返回结果:")
            print("-" * 50)
            # 格式化输出 JSON
            try:
                parsed = json.loads(result)
                print(json.dumps(parsed, ensure_ascii=False, indent=2))
            except:
                print(result)
            print("-" * 50)

            # 验证 JSON 结构
            print("\n结构验证:")
            errors = validate_xmind_json(result)
            if errors:
                print("  验证失败:")
                for err in errors:
                    print(f"    - {err}")
            else:
                print("  验证通过!")

            results.append((title, "成功", elapsed, len(result)))

        except Exception as e:
            elapsed = time.time() - start_time
            print(f"\n调用耗时：{elapsed:.2f} 秒后出错")
            print(f"错误信息：{type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            results.append((title, "失败", elapsed, 0))

    # 汇总报告
    print_separator("测试汇总")
    print(f"{'测试名称':<25} {'状态':<8} {'耗时 (秒)':<10} {'输出长度':<10}")
    print("-" * 55)
    for name, status, elapsed, length in results:
        status_str = "✓ " + status if status == "成功" else "✗ " + status
        print(f"{name:<25} {status_str:<8} {elapsed:<10.2f} {length:<10}")
    print("-" * 55)
    success_count = sum(1 for _, s, _, _ in results if s == "成功")
    print(f"总计：{success_count}/{len(results)} 测试通过")

if __name__ == '__main__':
    test_gen_xmind_json()
