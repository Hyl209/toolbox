import hashlib
import itertools
import sys
from concurrent.futures import ThreadPoolExecutor

# 你的账号信息
SALT = "e76337ee6781224d6daaf30c056709e0"
TARGET_HASH = "678e3fcc1106093822ac005ffffa46317d7500432528d0ce59811f638e5a731"
PWD_PREFIX = "6789"
TOTAL_LEN = 12
LETTER_COUNT = 3
REST_LEN = 8
NUM = "0123456789"
CHAR = "abcdefghijklmnopqrstuvwxyz"

# 正确哈希函数（带冒号）
def check(pwd):
    return hashlib.sha256(f"{SALT}:{pwd}".encode()).hexdigest()

# 破解每组位置组合
def crack_pos(pos):
    pool = [CHAR if i in pos else NUM for i in range(REST_LEN)]
    for suffix in itertools.product(*pool):
        pwd = PWD_PREFIX + ''.join(suffix)
        if check(pwd) == TARGET_HASH:
            return pwd
    return None

# 多线程爆破
def main():
    print("🚀 超快多线程爆破 HhhYl 账号")
    print("规则：12位 | 6789开头 | 3个小写字母 | 不卡顿版")
    print("="*50)

    positions = list(itertools.combinations(range(REST_LEN), LETTER_COUNT))
    total = len(positions)

    with ThreadPoolExecutor(max_workers=8) as executor:
        for idx, result in enumerate(executor.map(crack_pos, positions)):
            # 轻量进度条，不卡电脑
            sys.stdout.write(f"\r进度：{idx+1}/{total}")
            sys.stdout.flush()
            
            if result:
                print("\n\n🎉🎉🎉 密码找到了！！！")
                print(f"👤 账号：HhhYl")
                print(f"🔐 密码：{result}")
                return

    print("\n\n❌ 遍历结束（规则不匹配）")

if __name__ == "__main__":
    main()