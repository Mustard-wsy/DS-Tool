import dsvis
dsvis.auto()


def bubble_sort(arr):
    n = len(arr)

    for i in range(n):
        # 每一轮都会把最大值“冒泡”到末尾
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                # 交换
                arr[j], arr[j + 1] = arr[j + 1], arr[j]


# ===============================
# 内部测试（无输入输出）
# ===============================

import random

data = list(range(20))
random.shuffle(data)

bubble_sort(data)