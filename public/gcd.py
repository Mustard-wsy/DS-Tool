import dsvis

dsvis.set_mode("fine")
dsvis.auto()

class GcdStep(list):
    pass


def gcd_step(a_step, b_step, gcd_state):
    """执行一次GCD取模计算步骤：a = b, b = a % b"""
    a = a_step[-1]
    b = b_step[-1]
    
    # 计算新值
    new_a = b
    new_b = a % b
    
    # 保存到步骤列表中
    a_step.append(new_a)
    b_step.append(new_b)
    gcd_state.append(new_b)


def gcd(a, b, a_step, b_step, gcd_state):
    # 递归终止条件：b == 0 时，a 就是最大公约数
    if b == 0:
        return
    
    # 执行一步取模计算
    gcd_step(a_step, b_step, gcd_state)
    
    # 递归调用
    gcd(b, a % b, a_step, b_step, gcd_state)


# 初始化GCD计算的可视化容器（模仿汉诺塔柱子）
a_values = GcdStep([48, ])   # 初始第一个数 a = 48
b_values = GcdStep([18, ])   # 初始第二个数 b = 18
gcd_result = GcdStep([18, ]) # 保存每一步计算结果

# 执行 GCD 算法
gcd(48, 18, a_values, b_values, gcd_result)