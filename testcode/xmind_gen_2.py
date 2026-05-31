import json, xmind

data = json.loads('''
{
	"meta": {
		"name": "矩阵乘法思维导图",
		"author": "AI生成",
		"version": "1.0"
	},
	"format": "node_tree",
	"data": {
		"id": "root",
		"topic": "矩阵乘法知识要求",
		"children": [{
				"id": "1",
				"topic": "概念理解",
				"children": [{
						"id": "1-1",
						"topic": "定义：两个矩阵（二维数组）的特殊乘法运算"
					},
					{
						"id": "1-2",
						"topic": "前提条件：前矩阵列数等于后矩阵行数（M行N列 × N行P列）"
					},
					{
						"id": "1-3",
						"topic": "规则：结果矩阵维度为M行P列"
					},
					{
						"id": "1-4",
						"topic": "计算逻辑：C[i][j] = Σ(A[i][k] × B[k][j])，k从0到N-1"
					}
				]
			},
			{
				"id": "2",
				"topic": "计算示例",
				"children": [{
						"id": "2-1",
						"topic": "示例矩阵：A(3行2列) × B(2行4列) = C(3行4列)"
					},
					{
						"id": "2-2",
						"topic": "计算步骤：行与列对应元素相乘后求和（如A11×B11 + A12×B21）"
					}
				]
			},
			{
				"id": "3",
				"topic": "编程实现要求",
				"children": [{
						"id": "3-1",
						"topic": "函数定义：metrics(list1, list2)"
					},
					{
						"id": "3-2",
						"topic": "输入参数：两个二维列表（list1和list2）"
					},
					{
						"id": "3-3",
						"topic": "返回值：矩阵乘法结果的二维列表"
					},
					{
						"id": "3-4",
						"topic": "限制条件：禁用第三方库（如NumPy），仅用原生Python",
						"children": [{
								"id": "3-4-1",
								"topic": "XXXXXXXXX"
							},
							{
								"id": "3-4-2",
								"topic": "YYYYYYY"
							}
						]
					},
					{
						"id": "3-5",
						"topic": "实现逻辑：使用嵌套循环遍历行列并计算求和"
					}
				]
			}
		]
	}
}
''')


def add_node(parent, data):
    if isinstance(data, dict):
        parent.setTitle(data['topic'])
        if 'children' in data:
            for child in data['children']:
                topic = parent.addSubTopic()
                add_node(topic, child)

    # for key, value in data.items():
    #     if isinstance(value, dict):
    #         topic = parent.addSubTopic()
    #         topic.setTitle(data['topic'])
    #         add_node(topic, value)
    #     if isinstance(value, list):
    #         topic = parent.addSubTopic()
    #         topic.setTitle(data['topic'])
    #         add_node(topic, value)
    #     if isinstance(value, str):
    #         topic = parent.addSubTopic()
    #         topic.setTitle(value)


if __name__ == '__main__':
    workbook = xmind.load(f"./test_2.xmind")
    sheet = workbook.getPrimarySheet()
    sheet.setTitle(data['meta']['name'])
    # sheet.getRootTopic().setTitle(data['data']['topic'])
    add_node(sheet.getRootTopic(), data['data'])
    xmind.save(workbook)