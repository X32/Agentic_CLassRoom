import os
import sys

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from module import pdf_to_md

# PDF_PATH = "testsrc/26春-6S+-05步步为营-手写版解析.pdf"
PDF_PATH = "testsrc/26春-6S+-05步步为营-手写版解析.pdf"
TEST_DIR = "testsrc"


def test_pdf_to_md_auto():
    """自动模式：扫描型 PDF 应自动使用 marker"""
    result = pdf_to_md(PDF_PATH, output_path=f"{TEST_DIR}/test_auto.md", method="auto")

    assert isinstance(result, dict), "返回值应为字典"
    assert "md_path" in result, "缺少 md_path"
    assert "md_text" in result, "缺少 md_text"
    assert "pages" in result, "缺少 pages"
    assert len(result["md_text"].strip()) > 0, "Markdown 文本不应为空"
    print(f"[OK] 页数: {result['pages']}, 输出: {result['md_path']}, 文本长度: {len(result['md_text'])}")

    # 预览前 30 行
    print("\n--- Markdown 前 30 行预览 ---")
    for line in result["md_text"].splitlines()[:30]:
        print(line)
    print("--- 预览结束 ---\n")

    _cleanup(f"{TEST_DIR}/test_auto.md")
    print("=== test_pdf_to_md_auto PASSED ===")


def test_pdf_to_md_marker():
    """强制 marker 模式"""
    result = pdf_to_md(PDF_PATH, output_path=f"{TEST_DIR}/test_marker.md", method="marker")

    assert len(result["md_text"].strip()) > 0, "marker 应提取到文本"
    print(f"[OK] 文本长度: {len(result['md_text'])}, 页数: {result['pages']}")
    _cleanup(f"{TEST_DIR}/test_marker.md")
    print("=== test_pdf_to_md_marker PASSED ===")


def test_pdf_to_md_qwen_vl():
    """强制 Qwen-VL 云端模式"""
    result = pdf_to_md(PDF_PATH, output_path=f"{TEST_DIR}/test_qwen_vl1.md", method="qwen-vl")

    assert len(result["md_text"].strip()) > 0, "qwen-vl 应提取到文本"
    print(f"[OK] 文本长度: {len(result['md_text'])}, 页数: {result['pages']}")

    # 预览前 20 行
    print("\n--- Markdown 前 20 行预览 ---")
    for line in result["md_text"].splitlines()[:20]:
        print(line)
    print("--- 预览结束 ---\n")

    _cleanup(f"{TEST_DIR}/test_qwen_vl.md")
    print("=== test_pdf_to_md_qwen_vl PASSED ===")


def test_pdf_to_md_pymupdf_fallback():
    """pymupdf 模式：扫描 PDF 无文本，应触发 fallback 到 marker"""
    result = pdf_to_md(PDF_PATH, output_path=f"{TEST_DIR}/test_fallback.md", method="pymupdf")

    assert len(result["md_text"].strip()) > 0, "fallback 后应提取到文本"
    print(f"[OK] pymupdf 失败后 fallback 到 marker，文本长度: {len(result['md_text'])}")
    _cleanup(f"{TEST_DIR}/test_fallback.md")
    print("=== test_pdf_to_md_pymupdf_fallback PASSED ===")


def test_pdf_to_md_default_output():
    """不指定 output_path 时，默认生成同名 .md"""
    result = pdf_to_md(PDF_PATH, method="auto")
    expected_md = PDF_PATH.rsplit(".", 1)[0] + ".md"

    assert os.path.exists(expected_md), f"默认输出文件不存在: {expected_md}"
    print(f"[OK] 默认输出: {expected_md}")
    _cleanup(expected_md)
    print("=== test_pdf_to_md_default_output PASSED ===")


def _cleanup(path):
    pass
    # if os.path.exists(path):
    #     os.remove(path)
    #     print(f"[OK] 清理: {path}")


if __name__ == "__main__":
    print("=" * 55)
    print("  pdf_to_md() 测试")
    print(f"  测试 PDF: {PDF_PATH}")
    print("=" * 55)

    passed = 0
    failed = 0

    for test_func in [
        #test_pdf_to_md_auto,
        test_pdf_to_md_qwen_vl,
        # test_pdf_to_md_marker,
        # test_pdf_to_md_pymupdf_fallback,
        # test_pdf_to_md_default_output,
    ]:
        try:
            print(f"\n--- 运行: {test_func.__name__} ---")
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n[FAIL] {test_func.__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 55)
    print(f"结果: {passed} passed, {failed} failed")
    print("=" * 55)
