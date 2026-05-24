import heapq
import dsvis

dsvis.set_mode("coarse")
dsvis.auto()

class HuffmanNode:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq

        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq


class HuffmanTree:
    def __init__(self):
        self.root = None
        self.codes = {}

    # =========================
    # 建树
    # =========================

    def build(self, freq_table):

        heap = []

        # 初始化叶子节点
        for char, freq in freq_table.items():
            heapq.heappush(
                heap,
                HuffmanNode(char, freq)
            )

        # 合并节点
        while len(heap) > 1:

            left = heapq.heappop(heap)
            right = heapq.heappop(heap)

            merged = HuffmanNode(
                None,
                left.freq + right.freq
            )

            merged.left = left
            merged.right = right

            heapq.heappush(heap, merged)

        self.root = heap[0]

        # 生成编码
        self.generate_codes()

    # =========================
    # 生成霍夫曼编码
    # =========================

    def generate_codes(self):

        self.codes.clear()

        def dfs(node, code):

            if node is None:
                return

            # 叶子节点
            if node.char is not None:
                self.codes[node.char] = code
                return

            dfs(node.left, code + "0")
            dfs(node.right, code + "1")

        dfs(self.root, "")

    # =========================
    # 编码
    # =========================

    def encode(self, text):

        encoded = ""

        for ch in text:
            encoded += self.codes[ch]

        return encoded

    # =========================
    # 解码
    # =========================

    def decode(self, binary):

        result = []

        node = self.root

        for bit in binary:

            if bit == "0":
                node = node.left
            else:
                node = node.right

            # 到达叶子
            if node.char is not None:
                result.append(node.char)
                node = self.root

        return "".join(result)

    # =========================
    # 获取所有编码
    # =========================

    def get_codes(self):
        return dict(sorted(self.codes.items()))

    # =========================
    # 校验前缀码性质
    # =========================

    def validate_prefix_code(self):

        values = list(self.codes.values())

        for i in range(len(values)):
            for j in range(len(values)):
                if i == j:
                    continue

                if values[j].startswith(values[i]):
                    return False

        return True


# =====================================
# 教学演示
# =====================================

def huffman_demo():

    tree = HuffmanTree()

    # 经典教材案例
    # 高频字符编码更短

    freq_table = {
        "A": 45,
        "B": 13,
        "C": 12,
        "D": 16,
        "E": 9,
        "F": 5,
    }

    tree.build(freq_table)

    # 示例字符串
    text = "ABBCCCDDDDEEEEEFFFFFF"

    encoded = tree.encode(text)
    decoded = tree.decode(encoded)

    # 校验
    assert decoded == text
    assert tree.validate_prefix_code()

    return tree


if __name__ == "__main__":

    huffman_tree = huffman_demo()

    print("霍夫曼编码：")

    for ch, code in huffman_tree.get_codes().items():
        print(f"{ch}: {code}")