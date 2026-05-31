#!/usr/bin/env python3
"""
测试使用 transformers 库的 Whisper GPU 加速
"""

import os
# 禁用 cuDNN（GTX 1080 Ti 兼容性）
os.environ["CT2_USE_CUDNN"] = "0"

import torch
from transformers import WhisperProcessor, WhisperForConditionalGeneration, pipeline

print(f"PyTorch 版本：{torch.__version__}")
print(f"CUDA 版本：{torch.version.cuda}")
print(f"CUDA 可用：{torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"GPU 设备：{torch.cuda.get_device_name(0)}")
    device = "cuda:0"
else:
    print("CUDA 不可用，使用 CPU")
    device = "cpu"

# 加载模型
print("\n加载模型...")
model_name = "openai/whisper-tiny"
processor = WhisperProcessor.from_pretrained(model_name)
model = WhisperForConditionalGeneration.from_pretrained(model_name)
model.to(device)

print(f"模型已加载到：{device}")

# 测试音频文件
audio_file = "testsrc/20260420_172156_434147.mp3"
print(f"\n开始转写：{audio_file}")

# 创建 pipeline
transcriber = pipeline(
    task="automatic-speech-recognition",
    model=model,
    tokenizer=processor.tokenizer,
    feature_extractor=processor.feature_extractor,
    device=device
)

result = transcriber(audio_file, return_timestamps=True)
print(f"\n转写结果:")
print(result["text"])
print("\n✓ 测试成功")
