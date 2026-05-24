import dsvis
dsvis.auto()


class Dsu:
    def __init__(self, size):
        self.pa = list(range(size))
        self.size = [1] * size

    def find(self, x):
        if self.pa[x] != x:
            self.pa[x] = self.find(self.pa[x])
        return self.pa[x]

    def unite(self, x, y):
        x, y = self.find(x), self.find(y)
        if x == y:
            return
        # 按大小合并：小树挂到大树下
        if self.size[x] < self.size[y]:
            x, y = y, x
        self.pa[y] = x
        self.size[x] += self.size[y]


# ============================================================
# 并查集（DSU）教学演示
# ============================================================
# 固定 8 个元素（0-7），演示四大关键操作：
#   ① 初始化：各自独立
#   ② 多次 union 构建森林
#   ③ 按大小合并（小树挂大树）
#   ④ 路径压缩（find 时扁平化）
# ============================================================

n = 8
dsu = Dsu(n)

#print("=" * 50)
#print("【初始状态】每个元素自成一派")
#print("=" * 50)
#print(f"pa   = {dsu.pa}")
#print(f"size = {dsu.size}\n")

# ---------- 阶段1：两两配对 ----------
#print("=" * 50)
#print("【第1阶段】两两合并 → 形成 4 对 2-元素集合")
#print("=" * 50)
pairs = [(0, 1), (2, 3), (4, 5), (6, 7)]
for a, b in pairs:
    dsu.unite(a, b)
    #print(f"unite({a}, {b})  →  pa = {dsu.pa}   size[{dsu.find(a)}] = {dsu.size[dsu.find(a)]}")

#print()

# ---------- 阶段2：合并 2-元素集 ----------
#print("=" * 50)
#print("【第2阶段】合并 2-元素集合 → 形成 2 个 4-元素集合")
#print("  按大小合并：两集合大小相同，以 union 第一个参数为根")
#print("=" * 50)
dsu.unite(0, 2)
#print(f"unite(0, 2)  →  pa = {dsu.pa}   size[0] = {dsu.size[0]}")
dsu.unite(4, 6)
#print(f"unite(4, 6)  →  pa = {dsu.pa}   size[4] = {dsu.size[4]}")
#print()

# ---------- 阶段3：合并 4-元素集 ----------
#print("=" * 50)
#print("【第3阶段】合并 4-元素集合 → 形成 1 个 8-元素集合")
#print("  按大小合并：两边 size 均为 4，后一个集合挂到前一个")
#print("=" * 50)
dsu.unite(0, 4)
#print(f"unite(0, 4)  →  pa = {dsu.pa}   size[0] = {dsu.size[0]}")
#print()

# ---------- 阶段4：路径压缩 ----------
#print("=" * 50)
#print("【第4阶段】路径压缩")
#print("  find(7) 沿链 7→6→4→0 回溯，沿途节点全部指向根 0")
#print("=" * 50)
dsu.find(7)
#print(f"find(7) 后  →  pa = {dsu.pa}   ← 7, 6, 4 都直接指向 0")
#print()

#print("=" * 50)
#print("【第5阶段】路径压缩（续）")
#print("  find(5) 沿链 5→4→0 回溯")
#print("=" * 50)
dsu.find(5)
#print(f"find(5) 后  →  pa = {dsu.pa}   ← 5 也直接指向 0")
#print()

# ---------- 最终结果 ----------
#print("=" * 50)
#print("【最终结果】所有元素指向同一个根")
#print("=" * 50)
#print(f"pa   = {dsu.pa}")
#print(f"size = {dsu.size}")
roots = {dsu.find(i) for i in range(n)}
#print(f"集合个数 = {len(roots)}  （{'✔ 全部连通' if len(roots) == 1 else '✘ 未完全连通'}）")