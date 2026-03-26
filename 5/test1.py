from contextlib import nullcontext

import dsvis

tag1 = False

class Node:
    def __init__(self,v):
        self.next = None
        self.prev = None
        self.val=v
        self.val2=5


def create_complete_binary_tree(height):
    """
    创建高度为height的完全二叉树
    """
    if height <= 0:
        return None

    # 创建根节点
    root = Node(1)

    # 使用队列进行层序遍历创建
    from collections import deque
    queue = deque([root])
    current_val = 2
    current_height = 1

    while current_height < height:
        level_size = len(queue)

        for _ in range(level_size):
            if current_height == height - 1:  # 最后一层不需要再添加子节点
                break

            node = queue.popleft()

            # 创建左子节点
            node.next = Node(current_val)
            current_val += 1
            queue.append(node.next)
            #if tag1 == True:
                #dsvis.capture()

            # 创建右子节点
            node.prev = Node(current_val)
            current_val += 1
            queue.append(node.prev)
            #if tag1==True:
                #dsvis.capture() # tag1

        current_height += 1

    return root


a=Node(1)
b=Node(2)
c=Node(3)
d=Node(4)
e=Node(5)
f=Node(6)

a.next=b
b.next=c
c.next=d
d.next=e
e.next=a
b.prev=a
c.prev=b
# c.next=a   # 环

#dsvis.capture()
del a,b,c,d,e,f

n=create_complete_binary_tree(4)
if tag1==False:
    #dsvis.capture()
    del n
    n = create_complete_binary_tree(10)

    #dsvis.capture()