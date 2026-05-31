#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 summarize 方法
"""

import sys
import os

# 添加父目录到路径，以便导入 module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from module import summarize
import time

# 测试文本 1：矩阵乘法相关内容（短文本）
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

# 测试文本 2：较长的课堂录音转录（中长文本）
test_text_2 = """
我们来看一看啊 关于这个矩阵乘法这也是我们科学运算里边啊大批量数据处理的时候
也经常用到的一种算法啊这一种惩罚方式呢它呢 针对的是两个矩阵 也就是二维数组了
对吧二维数组就是一个矩阵嘛 对不对就是一个二维数组针对这个二维数组那么矩正乘法
这个就是我们矩正里边的一种很特殊的情况那么矩正比方说这是 A 大 A 这是一个矩正
这个矩正对应的是不是一个三行两列你用二位书主表示就是一个是不是三行两列 B 呢
是一个两行一列对吧两行一列好那么最后这个矩正乘法算出来的结果是什么呢注意算出来
的结果是三行一列这里面就以据乘乘法就有一个要求 M 行 N 列只能和 N 行 P 列这个列
前一个矩阵的列和后一个矩阵的行必须是一样大的比方说我有一个矩阵是三行四列那我
要乘的另外一个矩阵它必须是四行它必须是四行多少列无所谓三列也行四列也行五列也行
那最后这两个矩阵乘法乘出来的结果是多少三行五列这里面就以据乘乘法就有一个要求
M 行 N 列只能和 N 行 P 列这个列前一个矩阵的列和后一个矩阵的行必须是一样大的
好现在呢我来给大家稍微的定义这么两个矩阵 n d 1 等于 np 点 array 二维的 1234
或者我们就用这个好了 135204 好 135250 4 是不是定义了一个三行两类 N 第二呢
我就定义两行四两五六来的四列 那就 36943694 在第一行对吧 第二行 2783 那么我们
来看看 NP.DOTND1ND2 他们的矩正乘法乘出来的结果是不是这个数 92733131944 是不是
这个数 OK 这个叫矩正乘法对应简单来说就是对应位置的行和对应位置的列相乘最终 M 乘 N
乘以 N 乘 P 得到的是 M 乘 P 的这么一个新的矩阵新的矩阵这个呢跟我们的卷积那种还有
点像有点那个意思对吧有点那个意思这个叫矩阵存法它可以让我们呢比较方便的对这些
数据进行一个快速的批量的运算比较简洁调用一个 dota 就搞定了好这就是矩正惩罚
有没有问题 No.py 里边内置的没有问题的话那我现在就要出今天的第一个作业利用原生
python 代码对两个二维列表进行矩正乘法运算进行一个不能使用任何第三方库包括 number
five 只能有最原始的对两个二维列表我这边是不是定义的就是两个列表对吧两个列表但
这个列表要通用啊然后呢对然后包封装到封装到这个方法函数函数 metrics 中然后里面
的参数传的是什么 list1 list2list1 返回矩正乘法的结果返回矩正存法的结果 能听懂
这个题目的要求吗啊 然后就是说呢我们使用最原始的方法 你们来用 python 手算一下啊
还是那种今天呢 还是让大家就是用比较纯粹的方式 但我给他讲了一些 python 化的编程
方式哈 你能利用尽量利用 但是你不能使用第三方库啊 你说我直接调一下 np 点 dota 完事
啊老师这个什么这个作业啊我们使用原生的当然明白这个意思啊自己去循环去算乘法再算
加法再把它合并成一个什么新的二维数组新的二维数组好吧这是我们今天的第一个作业
"""

# 测试文本 3：极简短文本
test_text_3 = "今天天气真好，我们去公园散步吧。"

def print_separator(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")

def test_summarize():
    print_separator("Summarize 方法测试")

    # 测试 1：短文本
    print_separator("测试 1：短文本（矩阵乘法简介）")
    print(f"输入文本长度：{len(test_text_1)} 字符")
    print("-" * 40)

    start_time = time.time()
    try:
        result_1 = summarize(test_text_1)
        elapsed = time.time() - start_time
        print(f"\n调用耗时：{elapsed:.2f} 秒")
        print("\n返回结果:")
        print("-" * 40)
        print(result_1)
        print("-" * 40)
        print(f"输出长度：{len(result_1)} 字符")
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n调用耗时：{elapsed:.2f} 秒后出错")
        print(f"错误信息：{e}")

    # 测试 2：中长文本
    print_separator("测试 2：中长文本（完整课堂录音）")
    print(f"输入文本长度：{len(test_text_2)} 字符")
    print("-" * 40)

    start_time = time.time()
    try:
        result_2 = summarize(test_text_2)
        elapsed = time.time() - start_time
        print(f"\n调用耗时：{elapsed:.2f} 秒")
        print("\n返回结果:")
        print("-" * 40)
        print(result_2)
        print("-" * 40)
        print(f"输出长度：{len(result_2)} 字符")
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n调用耗时：{elapsed:.2f} 秒后出错")
        print(f"错误信息：{e}")

    # 测试 3：极简短文本
    print_separator("测试 3：极简短文本")
    print(f"输入文本长度：{len(test_text_3)} 字符")
    print("-" * 40)

    start_time = time.time()
    try:
        result_3 = summarize(test_text_3)
        elapsed = time.time() - start_time
        print(f"\n调用耗时：{elapsed:.2f} 秒")
        print("\n返回结果:")
        print("-" * 40)
        print(result_3)
        print("-" * 40)
        print(f"输出长度：{len(result_3)} 字符")
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n调用耗时：{elapsed:.2f} 秒后出错")
        print(f"错误信息：{e}")

    print_separator("测试完成")

if __name__ == '__main__':
    test_summarize()
