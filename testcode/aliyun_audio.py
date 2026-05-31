# 使用paraformer识别mp3文件

from dashscope.audio.asr import Recognition
import dashscope, os
from dotenv import load_dotenv
load_dotenv()

dashscope.api_key = os.getenv('Dashscope_API_Key')

recognition = Recognition(model='paraformer-realtime-v2',
                          format='wav',
                          sample_rate=16000,
                          language_hints=['zh', 'en'],
                          callback=None)
result = recognition.call('./test.wav')
print(result.get_sentence())