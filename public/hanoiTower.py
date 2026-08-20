import dsvis

dsvis.set_mode("fine")
dsvis.auto()

class Tower(list):
    """汉诺塔的柱子，用 list 表示，末尾为顶部。
    
    可视化时会显示为独立节点，内部元素变化会触发图更新。
    """
    pass


def move_disk(from_tower, to_tower):
    """移动一个盘子：从 from_tower 顶部取出，放到 to_tower 顶部。"""
    disk = from_tower.pop()
    to_tower.append(disk)


def hanoi(n, from_tower, aux_tower, to_tower):
    if n == 1:
        move_disk(from_tower, to_tower)
        return

    hanoi(n - 1, from_tower, to_tower, aux_tower)
    move_disk(from_tower, to_tower)
    hanoi(n - 1, aux_tower, from_tower, to_tower)


# 初始化三根柱子：A 有 4 个盘子（大到小），B 和 C 空
tower_a = Tower([4, 3, 2, 1])
tower_b = Tower()
tower_c = Tower()

hanoi(4, tower_a, tower_b, tower_c)