# -*- coding: utf-8 -*-
"""
DSVis Comprehensive Test Suite
Tests all public interfaces and their functions

Usage:
  python test_comprehensive.py [test_name]

If test_name is not specified, runs all tests
"""

import sys
import os
import dsvis
from collections import deque


# ============ Test 1: capture() - Basic Functionality ============

def test_capture_basic():
    """Test basic capture() functionality"""
    print("\n[TEST 1] capture() Basic Functionality")
    
    class Node:
        def __init__(self, val):
            self.val = val
            self.next = None
    
    head = Node(1)
    dsvis.capture()
    
    head.next = Node(2)
    dsvis.capture()
    
    head.next.next = Node(3)
    dsvis.capture()
    
    print("[OK] capture() basic test passed")


# ============ Test 2: capture() - Parameters ============

def test_capture_parameters():
    """Test capture() with various parameters"""
    print("\n[TEST 2] capture() Parameters")
    
    class Tree:
        def __init__(self, val):
            self.val = val
            self.left = None
            self.right = None
    
    root = Tree(1)
    
    # Test max_nodes parameter
    root.left = Tree(2)
    dsvis.capture(max_nodes=100)
    
    # Test include_private parameter
    root._private = 42
    dsvis.capture(include_private=True)
    
    # Test focus_vars parameter
    root.right = Tree(3)
    other_var = "should not show"
    dsvis.capture(focus_vars={"root"})
    
    print("[OK] capture() parameters test passed")


# ============ Test 3: capture() - Container Handling ============

def test_capture_containers():
    """Test capture() with containers"""
    print("\n[TEST 3] capture() Container Handling")
    
    class DataStruct:
        def __init__(self):
            self.items = []
            self.mapping = {}
            self.queued = deque()
    
    ds = DataStruct()
    
    # Empty containers
    dsvis.capture(include_containers=True)
    
    # Add list elements
    ds.items = [1, 2, 3, 4, 5]
    dsvis.capture(include_containers=True)
    
    # Add dict data
    ds.mapping = {"a": 1, "b": 2, "c": 3}
    dsvis.capture(include_containers=True)
    
    # Add deque data
    ds.queued = deque([10, 20, 30])
    dsvis.capture(include_containers=True)
    
    print("[OK] capture() container test passed")


# ============ Test 4: observe() - Basic Functionality ============

def test_observe_basic():
    """Test basic observe() functionality"""
    print("\n[TEST 4] observe() Basic Functionality")
    
    class Stack:
        def __init__(self):
            self.items = []
    
    stack = Stack()
    
    # Observe only specific variable
    dsvis.observe(vars={"stack"})
    
    stack.items.append(10)
    dsvis.observe(vars={"stack"})
    
    stack.items.append(20)
    dsvis.observe(vars={"stack"})
    
    print("[OK] observe() basic test passed")


# ============ Test 5: observe() - Pointer Monitoring ============

def test_observe_pointers():
    """Test observe() pointer monitoring"""
    print("\n[TEST 5] observe() Pointer Monitoring")
    
    class Array:
        def __init__(self, data):
            self.data = data
    
    arr = Array([10, 20, 30, 40, 50])
    
    # Monitor pointer position changes
    i = 0
    dsvis.observe(
        vars={"arr"},
        pointers=[("i", "arr.data")]
    )
    
    i = 2
    dsvis.observe(
        vars={"arr"},
        pointers=[("i", "arr.data")]
    )
    
    i = 4
    dsvis.observe(
        vars={"arr"},
        pointers=[("i", "arr.data")]
    )
    
    print("[OK] observe() pointer test passed")


# ============ Test 6: watch_vars() Decorator ============

def test_watch_vars():
    """Test watch_vars() decorator"""
    print("\n[TEST 6] watch_vars() Decorator")
    
    class Node:
        def __init__(self, val):
            self.val = val
            self.next = None
    
    @dsvis.watch_vars("head")
    def build_list():
        head = None
        dsvis.capture(focus_vars={"head"})
        
        head = Node(1)
        dsvis.capture(focus_vars={"head"})
        
        head.next = Node(2)
        dsvis.capture(focus_vars={"head"})
        
        return head
    
    result = build_list()
    print("[OK] watch_vars() decorator test passed")


# ============ Test 7: set_mode() - Coarse Mode ============

def test_set_mode_coarse():
    """Test set_mode('coarse') - coarse-grained mode"""
    print("\n[TEST 7] set_mode('coarse') - Coarse Mode")
    
    dsvis.set_mode("coarse")
    
    class Tree:
        def __init__(self, val):
            self.val = val
            self.left = None
            self.right = None
    
    root = Tree(1)
    dsvis.capture()
    
    root.left = Tree(2)
    dsvis.capture()
    
    root.right = Tree(3)
    dsvis.capture()
    
    print("[OK] set_mode('coarse') test passed")


# ============ Test 8: set_mode() - Fine Mode ============

def test_set_mode_fine():
    """Test set_mode('fine') - fine-grained mode"""
    print("\n[TEST 8] set_mode('fine') - Fine Mode")
    
    dsvis.set_mode("fine")
    
    class Node:
        def __init__(self, val):
            self.val = val
            self.next = None
    
    head = None
    dsvis.capture()
    
    head = Node(1)
    dsvis.capture()
    
    head.next = Node(2)
    dsvis.capture()
    
    head.next.next = Node(3)
    dsvis.capture()
    
    print("[OK] set_mode('fine') test passed")


# ============ Test 9: bind_fields() - Batch Binding ============

def test_bind_fields():
    """Test bind_fields() batch field binding"""
    print("\n[TEST 9] bind_fields() Batch Binding")
    
    class Node:
        def __init__(self):
            self.keys = []
            self.values = []
            self.children = []
    
    node = Node()
    
    # Bind multiple fields
    dsvis.bind_fields(
        node,
        keys=("KeysGroup", 3),
        values=("ValuesGroup", 1),
        children=("ChildrenGroup", 2)
    )
    
    # Populate data
    node.keys = [1, 2, 3, 4, 5, 6]
    node.values = ['a', 'b', 'c', 'd', 'e', 'f']
    node.children = [Node(), Node(), Node()]
    
    dsvis.capture(include_containers=True)
    
    print("[OK] bind_fields() test passed")


# ============ Test 10: bind_lists() - Class Decorator ============

def test_bind_lists():
    """Test bind_lists() class decorator"""
    print("\n[TEST 10] bind_lists() Class Decorator")
    
    @dsvis.bind_lists(
        "keys@KeyGroup:3",
        "values@KeyGroup:1",
        "children@ChildGroup:2"
    )
    class BNode:
        def __init__(self):
            self.keys = []
            self.values = []
            self.children = []
    
    node = BNode()
    node.keys = [1, 2, 3, 4, 5, 6]
    node.values = ['a', 'b', 'c', 'd', 'e', 'f']
    node.children = [BNode(), BNode()]
    
    dsvis.capture(include_containers=True)
    
    print("[OK] bind_lists() test passed")


# ============ Test 11: Mixed Usage - capture + observe ============

def test_mixed_capture_observe():
    """Test mixed usage of capture() and observe()"""
    print("\n[TEST 11] Mixed Usage - capture() + observe()")
    
    class LinkedList:
        def __init__(self):
            self.head = None
            self.size = 0
    
    class Node:
        def __init__(self, val):
            self.val = val
            self.next = None
    
    ll = LinkedList()
    
    # Use capture for snapshots
    dsvis.capture()
    
    ll.head = Node(1)
    ll.size = 1
    dsvis.capture()
    
    # Use observe for specific variables
    ll.head.next = Node(2)
    ll.size = 2
    dsvis.observe(vars={"ll"})
    
    ll.head.next.next = Node(3)
    ll.size = 3
    dsvis.observe(vars={"ll"})
    
    print("[OK] mixed usage test passed")


# ============ Test 12: Complex Nested Structures ============

def test_complex_structures():
    """Test complex nested data structures"""
    print("\n[TEST 12] Complex Nested Structures")
    
    class TreeNode:
        def __init__(self, val):
            self.val = val
            self.children = []
    
    # Build tree structure
    root = TreeNode(1)
    dsvis.capture()
    
    root.children = [TreeNode(2), TreeNode(3)]
    dsvis.capture(include_containers=True)
    
    root.children[0].children = [TreeNode(4), TreeNode(5), TreeNode(6)]
    dsvis.capture(include_containers=True)
    
    root.children[1].children = [TreeNode(7), TreeNode(8)]
    dsvis.capture(include_containers=True)
    
    print("[OK] complex structures test passed")


# ============ Test 13: Private Attributes ============

def test_private_attributes():
    """Test private attributes handling"""
    print("\n[TEST 13] Private Attributes")
    
    class MyClass:
        def __init__(self):
            self.public = "public_value"
            self._private = "private_value"
            self.__double_private = "double_private_value"
    
    obj = MyClass()
    
    # Don't include private attributes
    dsvis.capture(include_private=False)
    
    # Include private attributes
    dsvis.capture(include_private=True)
    
    print("[OK] private attributes test passed")


# ============ Test 14: max_nodes Limit ============

def test_max_nodes_limit():
    """Test max_nodes parameter"""
    print("\n[TEST 14] max_nodes Limit")
    
    class Node:
        def __init__(self, val):
            self.val = val
            self.children = []
    
    # Build tree with many nodes
    root = Node(1)
    for i in range(10):
        root.children.append(Node(i + 2))
    
    # Limit displayed nodes
    dsvis.capture(
        max_nodes=100,
        include_containers=True
    )
    
    dsvis.capture(
        max_nodes=10,
        include_containers=True
    )
    
    print("[OK] max_nodes test passed")


# ============ Test 15: focus_vars ============

def test_focus_vars():
    """Test focus_vars parameter"""
    print("\n[TEST 15] focus_vars Parameter")
    
    class Node:
        def __init__(self, val):
            self.val = val
            self.next = None
    
    head = Node(1)
    other_var = Node(999)
    irrelevant = {"key": "value"}
    
    # Focus on head only
    dsvis.capture(focus_vars={"head"})
    
    head.next = Node(2)
    
    # Focus on multiple variables
    dsvis.capture(
        focus_vars={"head", "other_var"}
    )
    
    print("[OK] focus_vars test passed")


# ============ Test 16: Empty Structures ============

def test_empty_structures():
    """Test empty data structures"""
    print("\n[TEST 16] Empty Structures")
    
    class Container:
        def __init__(self):
            self.items = []
            self.mapping = {}
    
    c = Container()
    
    # Empty containers
    dsvis.capture(include_containers=True)
    
    # Progressively fill
    c.items.append(1)
    dsvis.capture(include_containers=True)
    
    c.mapping["key"] = "value"
    dsvis.capture(include_containers=True)
    
    print("[OK] empty structures test passed")


# ============ Test 17: Circular References ============

def test_circular_references():
    """Test circular reference handling"""
    print("\n[TEST 17] Circular References")
    
    class Node:
        def __init__(self, val):
            self.val = val
            self.next = None
    
    node1 = Node(1)
    node2 = Node(2)
    node3 = Node(3)
    
    # Create circular reference
    node1.next = node2
    node2.next = node3
    node3.next = node1  # Circular!
    
    dsvis.capture(focus_vars={"node1"})
    
    print("[OK] circular references test passed")


# ============ Test 18: None Values ============

def test_none_values():
    """Test None value handling"""
    print("\n[TEST 18] None Values")
    
    class Node:
        def __init__(self):
            self.value = None
            self.next = None
    
    node = Node()
    dsvis.capture(focus_vars={"node"})
    
    node.value = 42
    dsvis.capture(focus_vars={"node"})
    
    node.value = None
    dsvis.capture(focus_vars={"node"})
    
    print("[OK] None values test passed")


# ============ Test 19: Large Data ============

def test_large_data():
    """Test large data handling"""
    print("\n[TEST 19] Large Data")
    
    class DataHolder:
        def __init__(self):
            self.data = []
    
    holder = DataHolder()
    
    # Large list
    holder.data = list(range(1000))
    dsvis.capture(
        include_containers=True,
        max_nodes=500
    )
    
    # Large dict
    holder.data = {f"key_{i}": i for i in range(100)}
    dsvis.capture(
        include_containers=True,
        max_nodes=200
    )
    
    print("[OK] large data test passed")


# ============ Test Runner ============

def run_tests(test_name=None):
    """Run specified test or all tests"""
    tests = {
        "test_capture_basic": test_capture_basic,
        "test_capture_parameters": test_capture_parameters,
        "test_capture_containers": test_capture_containers,
        "test_observe_basic": test_observe_basic,
        "test_observe_pointers": test_observe_pointers,
        "test_watch_vars": test_watch_vars,
        "test_set_mode_coarse": test_set_mode_coarse,
        "test_set_mode_fine": test_set_mode_fine,
        "test_bind_fields": test_bind_fields,
        "test_bind_lists": test_bind_lists,
        "test_mixed_capture_observe": test_mixed_capture_observe,
        "test_complex_structures": test_complex_structures,
        "test_private_attributes": test_private_attributes,
        "test_max_nodes_limit": test_max_nodes_limit,
        "test_focus_vars": test_focus_vars,
        "test_empty_structures": test_empty_structures,
        "test_circular_references": test_circular_references,
        "test_none_values": test_none_values,
        "test_large_data": test_large_data,
    }
    
    if test_name:
        if test_name in tests:
            print(f"\n{'='*60}")
            print(f"Running test: {test_name}")
            print(f"{'='*60}")
            tests[test_name]()
        else:
            print(f"Test not found: {test_name}")
            print(f"Available tests: {', '.join(tests.keys())}")
    else:
        print(f"\n{'='*60}")
        print(f"Running all tests ({len(tests)} total)")
        print(f"{'='*60}")
        passed = 0
        failed = 0
        for name, test_func in tests.items():
            try:
                test_func()
                passed += 1
            except Exception as e:
                print(f"[FAIL] {name} failed: {e}")
                failed += 1
        
        print(f"\n{'='*60}")
        print(f"Test Results: {passed} passed, {failed} failed")
        print(f"{'='*60}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_tests(sys.argv[1])
    else:
        run_tests()
