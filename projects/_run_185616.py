"""
写一个数学计算器
"""
import math
class C:
    add=lambda a,b:a+b; sub=lambda a,b:a-b; mul=lambda a,b:a*b; div=lambda a,b:a/b if b else float("inf")
    power=lambda a,b:a**b; sqrt=lambda a:math.sqrt(a) if a>=0 else None
    fact=lambda n:math.factorial(n) if n>=0 else None
    @staticmethod
    def fib(n):
        if n<=0: return []
        f=[0,1]
        for i in range(2,n): f.append(f[-1]+f[-2])
        return f if n>1 else [0]
    is_prime=lambda n:False if n<2 else all(n%i for i in range(2,int(math.sqrt(n))+1))
    gcd=math.gcd; lcm=lambda a,b:abs(a*b)//math.gcd(a,b)

if __name__ == "__main__":
    c=C()
    print(f"2+3={c.add(2,3)} 10-4={c.sub(10,4)} 6*7={c.mul(6,7)}")
    print(f"2^10={c.power(2,10)} sqrt(144)={c.sqrt(144)} 10!={c.fact(10)}")
    print(f"fib(15)={c.fib(15)} is_prime(17)={c.is_prime(17)}")
    print(f"gcd(12,18)={c.gcd(12,18)} lcm(12,18)={c.lcm(12,18)}")
