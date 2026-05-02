"""
写一个数学计算器
Ghost Agent 自动生成
"""
import math
import random

class Calculator:
    """科学计算器"""

    @staticmethod
    def add(a, b): return a + b
    @staticmethod
    def sub(a, b): return a - b
    @staticmethod
    def mul(a, b): return a * b
    @staticmethod
    def div(a, b): return a / b if b != 0 else float("inf")
    @staticmethod
    def power(a, b): return a ** b
    @staticmethod
    def sqrt(a): return math.sqrt(a) if a >= 0 else None
    @staticmethod
    def factorial(n): return math.factorial(n) if n >= 0 else None
    @staticmethod
    def fibonacci(n):
        if n <= 0: return []
        if n == 1: return [0]
        fib = [0, 1]
        for i in range(2, n):
            fib.append(fib[-1] + fib[-2])
        return fib
    @staticmethod
    def is_prime(n):
        if n < 2: return False
        for i in range(2, int(math.sqrt(n)) + 1):
            if n % i == 0: return False
        return True
    @staticmethod
    def gcd(a, b): return math.gcd(a, b)
    @staticmethod
    def lcm(a, b): return abs(a * b) // math.gcd(a, b)

if __name__ == "__main__":
    calc = Calculator()
    print("=== 数学计算器 ===")
    print(f"  2 + 3 = {calc.add(2, 3)}")
    print(f"  10 - 4 = {calc.sub(10, 4)}")
    print(f"  6 * 7 = {calc.mul(6, 7)}")
    print(f"  100 / 3 = {calc.div(100, 3):.4f}")
    print(f"  2^10 = {calc.power(2, 10)}")
    print(f"  sqrt(144) = {calc.sqrt(144)}")
    print(f"  10! = {calc.factorial(10)}")
    print(f"  fib(15) = {calc.fibonacci(15)}")
    print(f"  17 是质数? {calc.is_prime(17)}")
    print(f"  gcd(12, 18) = {calc.gcd(12, 18)}")
    print(f"  lcm(12, 18) = {calc.lcm(12, 18)}")
