#!/usr/bin/env python3
"""
DSVis 示例启动器
快速运行各种算法示例
"""

import os
import sys
import subprocess
from pathlib import Path

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.absolute()
SRC_DIR = PROJECT_ROOT / "src"

EXAMPLES = {
    "1": ("Btree.py", "B树示例"),
    "2": ("Bubble.py", "冒泡排序"),
    "3": ("hash.py", "哈希表"),
    "4": ("queue.py", "队列"),
    "5": ("stack.py", "栈"),
    "6": ("LongList.py", "长链表"),
}

def print_header():
    print("\n" + "="*50)
    print("🎯 DSVis 示例运行器")
    print("="*50 + "\n")

def print_menu():
    print("请选择要运行的示例:\n")
    for key, (filename, description) in EXAMPLES.items():
        print(f"  {key}. {description:15} ({filename})")
    print(f"  0. 退出\n")

def run_example(choice):
    if choice == "0":
        print("\n👋 再见！")
        return False
    
    if choice not in EXAMPLES:
        print("❌ 无效的选择！")
        return True
    
    filename, description = EXAMPLES[choice]
    example_path = SRC_DIR / filename
    
    if not example_path.exists():
        print(f"❌ 文件不存在: {example_path}")
        return True
    
    print(f"\n▶️  正在运行: {description}")
    print(f"📄 文件: {example_path}")
    print("-" * 50)
    
    try:
        # 在 src 目录下运行脚本
        os.chdir(SRC_DIR)
        result = subprocess.run(
            [sys.executable, filename],
            capture_output=False
        )
        
        if result.returncode == 0:
            print("\n✅ 执行完成！浏览器中应该看到可视化界面。")
        else:
            print(f"\n❌ 执行失败（返回码: {result.returncode}）")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
    finally:
        os.chdir(PROJECT_ROOT)
    
    return True

def main():
    print_header()
    
    # 检查 src 目录
    if not SRC_DIR.exists():
        print(f"❌ 错误: 找不到 src 目录")
        print(f"   预期路径: {SRC_DIR}")
        sys.exit(1)
    
    # 检查 dsvis.py
    if not (SRC_DIR / "dsvis.py").exists():
        print(f"❌ 错误: 找不到 dsvis.py")
        sys.exit(1)
    
    # 运行主循环
    while True:
        print_menu()
        choice = input("选择 (输入数字): ").strip()
        
        if not run_example(choice):
            break
        
        input("\n按 Enter 继续...")
    
    print()

if __name__ == "__main__":
    main()
