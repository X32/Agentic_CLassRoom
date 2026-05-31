# MD5加密

# import hashlib
#
# password = "woniu123"
# encrypted = hashlib.md5(password.encode()).hexdigest()
# print(encrypted)



# AES加解密

# from Crypto.Cipher import AES
# from Crypto.Util.Padding import pad, unpad
# from binascii import a2b_hex
#
# # 设置密钥，必须是16、24、32字节（即8的倍数）
# key = 'Woniuxy-Good-123'
# # 设置初始向量，提升密文的随机性，也必须是16、24、32字节
# iv = '1234567890ABCDEF'
#
# # 实例化AES对象，key和iv必须转换为二进制数据
# cipher = AES.new(key.encode(), AES.MODE_CBC, iv.encode())
# # 定义原文待加密内容，必须是16的倍数，否则需要填充
# source = "Today is a good day."
# padded = pad(source.encode(), AES.block_size)
# encrypted = cipher.encrypt(padded)  # 加密
# print(encrypted.hex())   # 输出十六进制，便于存储和传输
#
# # 解密过程，其中a2b_hex表示将十六进制转换为二进制
# cipher = AES.new(key.encode(), AES.MODE_CBC, iv.encode())
# encrypted = 'ab23f1e3b29ce07bf3cd44eb918e246bf602e232e2c91fd0716df780457d278e'
# decrypted_padded = cipher.decrypt(a2b_hex(encrypted))
# decrypted = unpad(decrypted_padded, AES.block_size)
# print(decrypted.decode())



import os
from dotenv import load_dotenv
load_dotenv()

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from binascii import a2b_hex

key = os.getenv("Token_AES_Key").encode()
iv = os.getenv("Token_AES_IV").encode()

def aes_encrypt(source):
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_data = pad(source.encode(), AES.block_size)
    encrypted = cipher.encrypt(padded_data)
    return encrypted.hex()

def aes_decrypt(encrypted):
    decipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_padded = decipher.decrypt(a2b_hex(encrypted))
    decrypted = unpad(decrypted_padded, AES.block_size)
    return decrypted.decode()

def check_token(token):
    try:
        decrypted = aes_decrypt(token)
        temp_list = decrypted.split("|")
        print(temp_list)
        # return {"username": temp_list[0], "userid": temp_list[1], "role": temp_list[2]}
    except:
        print("Token ERROR")

if __name__ == '__main__':
    result = check_token("a44eb918e246bf602e232e2c91fd0716df780457d278e")