import json, xmind

data = json.loads('''
{
  "矩阵乘法": {
    "定义": "针对两个矩阵（二维数组）的乘法",
    "要求": [
      "前一个矩阵的列数必须等于后一个矩阵的行数",
      "M行N列的矩阵只能和N行P列的矩阵相乘",
      "结果矩阵的形状为M行P列"
    ],
    "算法": [
      "A11乘以B11加上A12乘以B21",
      "逐行逐列进行乘法和加法运算"
    ],
    "示例": {
      "矩阵A": "三行两列",
      "矩阵B": "两行一列",
      "结果矩阵": "三行一列"
    },
    "作业要求": {
      "使用原生Python代码": "对两个二维列表进行矩阵乘法运算",
      "不能使用第三方库": "包括NumPy",
      "封装函数": "metrics(list1, list2)",
      "返回结果": "矩阵乘法的结果"
    }
  }
}
''')


def add_node(parent, data):
    for key, value in data.items():
        if isinstance(value, dict):
            topic = parent.addSubTopic()
            topic.setTitle(key)
            add_node(topic, value)
        if isinstance(value, list):
            topic = parent.addSubTopic()
            topic.setTitle(key)
            for item in value:
                subtopic = topic.addSubTopic()
                subtopic.setTitle(item)
        if isinstance(value, str):
            topic = parent.addSubTopic()
            topic.setTitle(key)
            subtopic = topic.addSubTopic()
            subtopic.setTitle(value)


if __name__ == '__main__':
    workbook = xmind.load(f"./test_1.xmind")
    sheet = workbook.getPrimarySheet()
    sheet.setTitle('矩阵乘法')
    sheet.getRootTopic().setTitle("矩阵乘法")
    add_node(sheet.getRootTopic(), data['矩阵乘法'])
    xmind.save(workbook)