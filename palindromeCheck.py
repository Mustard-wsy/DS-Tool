import dsvis
dsvis.set_mode("fine")

dsvis.auto()
@dsvis.watch_vars("cleaned", "left", "right")
def is_palindrome(s):
    # 清理字符串：去空格、转小写、去标点
    cleaned = ""
    for ch in s:
        if ch.isalnum():
            cleaned += ch.lower()
    
    return _check_palindrome(cleaned, 0, len(cleaned) - 1)

def _check_palindrome(s, left, right):
    if left >= right:
        return True
    if s[left] != s[right]:
        return False
    return _check_palindrome(s, left + 1, right - 1)

test_cases = [
    "Madam, I'm Adam",
    "A man, a plan, a canal: Panama",
    "hello",
    "racecar",
    "Was it a car or a cat I saw"
]

results = [is_palindrome(tc) for tc in test_cases]