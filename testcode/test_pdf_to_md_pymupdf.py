import os
import sys

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from module import _pdf_to_md_pymupdf


PDF_PATH = "testsrc/26春-6S+-05步步为营-手写版解析.pdf"
OUTPUT_PATH = "testsrc/test_output.md"


def test_pdf_to_md_basic():
    """基本功能测试：转换 PDF 为 Markdown"""
    assert os.path.exists(PDF_PATH), f"测试 PDF 不存在: {PDF_PATH}"

    md_text = _pdf_to_md_pymupdf(PDF_PATH, OUTPUT_PATH)

    # 1. 检查返回值非空
    assert isinstance(md_text, str), "返回值应为字符串"
    assert len(md_text.strip()) > 0, "返回的 Markdown 文本不应为空"
    print(f"[OK] 返回值长度: {len(md_text)} 字符")

    # 2. 检查输出文件已生成
    assert os.path.exists(OUTPUT_PATH), f"输出文件未生成: {OUTPUT_PATH}"
    print(f"[OK] 输出文件存在: {OUTPUT_PATH}")

    # 3. 检查包含 Markdown 标题标记（# 开头）
    has_headings = any(line.startswith("#") for line in md_text.splitlines())
    print(f"[INFO] 是否包含标题: {has_headings}")

    # 4. 检查提取到中文文本
    has_chinese = any('一' <= c <= '鿿' for c in md_text)
    assert has_chinese, "应提取到中文文本"
    print(f"[OK] 包含中文文本")

    # 5. 打印前 50 行预览
    print("\n--- Markdown 前 50 行预览 ---")
    for line in md_text.splitlines()[:50]:
        print(line)
    print("--- 预览结束 ---\n")

    # 清理测试输出
    if os.path.exists(OUTPUT_PATH):
        os.remove(OUTPUT_PATH)
        print("[OK] 测试输出已清理")

    print("\n=== test_pdf_to_md_basic PASSED ===")
    return True


def test_pdf_to_md_page_count():
    """检查多页 PDF 是否正确处理"""
    import pymupdf as fitz

    doc = fitz.open(PDF_PATH)
    page_count = len(doc)
    doc.close()

    md_text = _pdf_to_md_pymupdf(PDF_PATH, OUTPUT_PATH)
    lines = [l for l in md_text.splitlines() if l.strip()]

    assert page_count > 1, f"测试 PDF 应有多个页，实际 {page_count} 页"
    assert len(lines) > 10, f"提取行数过少: {len(lines)}"
    print(f"[OK] PDF 页数: {page_count}, 提取行数: {len(lines)}")

    if os.path.exists(OUTPUT_PATH):
        os.remove(OUTPUT_PATH)

    print("\n=== test_pdf_to_md_page_count PASSED ===")
    return True


def test_pdf_to_md_empty():
    """边界测试：无文本的 PDF 应抛出异常"""
    import pymupdf as fitz

    # 创建一个空白 PDF（只有图片，无文本）
    blank_pdf = "testsrc/blank.pdf"
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.draw_circle((300, 400), 50, color=(1, 0, 0))
    doc.save(blank_pdf)
    doc.close()

    try:
        _pdf_to_md_pymupdf(blank_pdf, "testsrc/blank_output.md")
        print("[FAIL] 应抛出 ValueError")
        return False
    except ValueError as e:
        print(f"[OK] 正确抛出异常: {e}")
    finally:
        for f in [blank_pdf, "testsrc/blank_output.md"]:
            if os.path.exists(f):
                os.remove(f)

    print("\n=== test_pdf_to_md_empty PASSED ===")
    return True


if __name__ == "__main__":
    print("=" * 50)
    print("  _pdf_to_md_pymupdf() 测试")
    print("=" * 50)

    passed = 0
    failed = 0

    for test_func in [
        test_pdf_to_md_basic,
        test_pdf_to_md_page_count,
        test_pdf_to_md_empty,
    ]:
        try:
            print(f"\n--- 运行: {test_func.__name__} ---")
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n[FAIL] {test_func.__name__}: {e}")
            failed += 1

    print("\n" + "=" * 50)
    print(f"结果: {passed} passed, {failed} failed")
    print("=" * 50)
