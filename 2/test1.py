import dsvis

class Node:
    def __init__(self,v):
        self.next = None
        self.prev = None
        self.val=v
        self.val2=5


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

dsvis.capture()