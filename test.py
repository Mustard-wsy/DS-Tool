from dsvis import capture
from dsvis import set_mode
def algorithm():
    a = [1, 2, 3]
    capture()
    a[0] = 99
    capture(focus_vars=["a"])

algorithm()