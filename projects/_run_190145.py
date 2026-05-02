"""write a math calculator"""
import math

def add(a,b): return a+b
def sub(a,b): return a-b
def mul(a,b): return a*b
def div(a,b): return a/b if b else float("inf")
def power(a,b): return a**b
def sqrt(a): return math.sqrt(a) if a>=0 else None
def fact(n): return math.factorial(n) if n>=0 else None
def fib(n):
    if n<=0: return []
    f=[0,1]
    for i in range(2,n): f.append(f[-1]+f[-2])
    return f if n>1 else [0]
def is_prime(n):
    if n<2: return False
    return all(n%i for i in range(2,int(math.sqrt(n))+1))
gcd = math.gcd
def lcm(a,b): return abs(a*b)//math.gcd(a,b)

if __name__ == "__main__":
    print("2+3=" + str(add(2,3)) + " 10-4=" + str(sub(10,4)))
    print("6*7=" + str(mul(6,7)) + " 100/3=" + str(round(div(100,3),2)))
    print("2^10=" + str(power(2,10)) + " sqrt(144)=" + str(sqrt(144)))
    print("10!=" + str(fact(10)))
    print("fib(15)=" + str(fib(15)))
    print("is_prime(17)=" + str(is_prime(17)))
    print("gcd(12,18)=" + str(gcd(12,18)) + " lcm=" + str(lcm(12,18)))
