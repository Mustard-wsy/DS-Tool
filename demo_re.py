import dsvis
#dsvis.set_mode("fine")
dsvis.auto()

class Node:
    def __init__(self, val, next=None):
        self.val = val
        self.next = next



head = Node(1, Node(2, Node(3)))
