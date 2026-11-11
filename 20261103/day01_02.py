import json


def parse_order(order_json):
    try:
        json_result = json.loads(order_json)

    except json.JSONDecodeError as e:
        print(f"JSON解析异常: {e}")
        return None

    else:
        print("JSON解析成功")

        # 校验解析结果的数据类型
        if not isinstance(json_result, dict):
            print("数据结构异常，期望字典")
            return None

        return json_result

    finally:
        print("解析结束")


if __name__ == '__main__':
    valid_json = '{"order_id": "SO-1001", "status": "PAID"}'
    print(parse_order(valid_json))

    invalid_json = '{"order_id": "SO-1001", "status": '
    print(parse_order(invalid_json))

    empty_json = '{}'
    print(parse_order(empty_json))

    list_json = '[]'
    print(parse_order(list_json))