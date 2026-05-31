from datetime import datetime
from model import Users, engine
from sqlmodel import Session, select

# 插入测试用户数据
test_users = [
    {"username": "student1", "password": "123456", "realname": "测试学生", "role": "student"},
    {"username": "student2", "password": "123456", "realname": "张三", "role": "student"},
    {"username": "teacher1", "password": "123456", "realname": "李老师", "role": "teacher"},
    {"username": "admin", "password": "admin123", "realname": "管理员", "role": "admin"},
]

with Session(engine) as session:
    for user_data in test_users:
        # 检查用户是否已存在
        sql = select(Users).where(Users.username == user_data["username"])
        existing = session.execute(sql).first()

        if existing:
            print(f"用户已存在：{user_data['username']}")
        else:
            # 创建新用户
            user = Users(
                username=user_data["username"],
                password=user_data["password"],
                realname=user_data["realname"],
                role=user_data["role"],
                createtime=datetime.now()
            )
            session.add(user)
            print(f"创建用户：{user_data['username']} ({user_data['realname']}) - 角色：{user_data['role']}")

    session.commit()

print("\n测试用户插入完成！")
print("\n登录信息：")
print("  学生账号：student1 / 123456")
print("  教师账号：teacher1 / 123456")
print("  管理员账号：admin / admin123")
