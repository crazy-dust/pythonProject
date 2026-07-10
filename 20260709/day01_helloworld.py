# 1. Python 最大的第一差异：不用声明类型
name = "张三"
age = 17
active = True
test = None
print(name, age, active, test)

# 2. Python 是动态强类型
# a = "1"
# b = 2
#
# print(a + b)

# 3. 缩进就是代码块
if age >= 18:
    print("成年")

# 4. if 判断
if age >= 18:
    print("OK")
else:
    print("ok1")

num = 100
if num >= 80:
    print(">= 80")
elif num >= 70:
    print(">= 70")
elif num >= 60:
    print(">= 60")
else:
    print("test")

# 5. Python 的比较运算
a = 10
b = 20
print(a == b)
print(a >= b)
print(a <= b)
print(a != b)

if a >= 10 and b <= 20:
    print(123)

if a == 10 or b == 20:
    print("ok")

deleted = False
if not deleted:
    print("deleted")

# 6. 更 Pythonic 的区间判断
# java： if (age >= 18 && age <= 60)
if 18 <= a <= 60:
    print("ok")

# 7. for 循环
for i in range(1, 10):
    print(i)

# 步长：
for n in range(1, 10, 2):
    print(n)

# 8. 遍历 list
names = ["1", "2", "3", "4", "5"]
for name in names:
    print(name)

for index, value in enumerate(names):
    print(index, value)

# 9. while 循环
count = 0
while count < 3:
    print(count)
    count += 1


# 10. 函数
def test(a: int, b: int) -> int:
    return a + b
test(1, 2)


# 11. 默认参数
def say_hello(name: str = "匿名用户") -> None:
    print(f"你好，{name}")

say_hello()
say_hello("张三")

# 12. f-string 字符串格式化
def helloword(t1 : str = "测试啊") -> None:
    print(f"是嘛？{t1}")
helloword()

orderNo = "ORD-1234"
amt = 1.99888
print(f"this order: {orderNo}, amt: {amt}")

print(f"{amt:.2f}")

# 13. None
name = None
if names is None:
    print("names is None")
if names is not None and not names:
    print("names is not None")

# 14. Python 的真假判断
# 这些在 Python 里都等价于 False：
# None
# False
# 0
# ""
# []
# {}
# set()
name = ""
if not name:
    print("name为空")

items = []
if not items:
    print("列表为空")

data = {}
if not data:
    print("字典为空")


# 15. input 输入
name = input("请输入你的名字：")
print(f"你好，{name}")
