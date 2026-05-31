#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 gen_reference 方法
"""

import sys
import os

# 添加父目录到路径，以便导入 module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from module import gen_reference
import time

# 测试关键字列表
test_keywords = [
    "矩阵乘法",
    "Python 编程",
    "机器学习",
    "深度学习",
    "神经网络",
    "数据分析",
    "人工智能",
    "无效关键字测试 abc123xyz",  # 测试无搜索结果的情况
]

def print_separator(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")

def test_gen_reference():
    print_separator("gen_reference 方法测试")
    print("测试阿里云 OpenSearch 接口")
    print("-" * 70)

    results = []

    for i, keyword in enumerate(test_keywords, 1):
        print(f"\n[测试 {i}/{len(test_keywords)}] 关键字：{keyword}")
        print("-" * 50)

        start_time = time.time()
        try:
            result = gen_reference(keyword)
            elapsed = time.time() - start_time

            print(f"调用耗时：{elapsed:.2f} 秒")
            print(f"返回结果类型：{type(result)}")
            print(f"返回结果长度：{len(result)}")

            # 尝试解析为列表
            try:
                ref_list = eval(result)
                if isinstance(ref_list, list):
                    print(f"解析成功：包含 {len(ref_list)} 条参考结果")
                    for j, item in enumerate(ref_list, 1):
                        print(f"\n  [{j}]")
                        if isinstance(item, dict):
                            for key, value in item.items():
                                # 截断过长的内容
                                val_str = str(value)
                                if len(val_str) > 100:
                                    val_str = val_str[:100] + "..."
                                print(f"      {key}: {val_str}")
                        else:
                            print(f"      {item}")
                else:
                    print(f"警告：返回结果不是列表类型，而是 {type(ref_list)}")
            except Exception as e:
                print(f"解析返回结果失败：{e}")
                print(f"原始返回：{result[:200]}...")

            results.append((keyword, "成功", elapsed, len(result)))

        except Exception as e:
            elapsed = time.time() - start_time
            print(f"调用耗时：{elapsed:.2f} 秒后出错")
            print(f"错误信息：{type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            results.append((keyword, "失败", elapsed, 0))

        # 每次请求间隔 1 秒，避免频率限制
        if i < len(test_keywords):
            time.sleep(1)

    # 汇总报告
    print_separator("测试汇总")
    print(f"{'关键字':<20} {'状态':<10} {'耗时 (秒)':<12} {'返回长度':<10}")
    print("-" * 55)
    for kw, status, elapsed, length in results:
        # 截断长关键字
        kw_display = kw[:18] + ".." if len(kw) > 20 else kw
        status_str = "✓ " + status if status == "成功" else "✗ " + status
        print(f"{kw_display:<20} {status_str:<10} {elapsed:<12.2f} {length:<10}")
    print("-" * 55)
    success_count = sum(1 for _, s, _, _ in results if s == "成功")
    print(f"总计：{success_count}/{len(results)} 测试通过")

    # 测试环境变量
    print_separator("环境变量检查")
    api_key = os.getenv('Aliyun_Search_Key')
    if api_key:
        print(f"Aliyun_Search_Key: {api_key[:10]}...{api_key[-5:]}")
        print("状态：已配置")
    else:
        print("Aliyun_Search_Key: 未设置")
        print("状态：警告 - 需要配置 API Key 才能正常使用")

if __name__ == '__main__':
    test_gen_reference()
