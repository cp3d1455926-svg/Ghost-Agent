"""
写一个数据分析脚本
"""
from collections import Counter
import math

def analyze(data):
    if not data: return {"error": "空数据"}
    r = {"总数": len(data)}
    if all(isinstance(x, (int, float)) for x in data):
        s = sorted(data); n = len(data); avg = sum(data)/n
        r.update({"最小值": min(data), "最大值": max(data), "总和": sum(data), "平均值": avg, "中位数": s[n//2] if n%2 else (s[n//2-1]+s[n//2])/2, "标准差": math.sqrt(sum((x-avg)**2 for x in data)/n)})
    if all(isinstance(x, str) for x in data):
        lens = [len(x) for x in data]
        r.update({"最短": min(lens), "最长": max(lens), "平均长度": sum(lens)/len(lens), "最常见": Counter(data).most_common(5)})
    return r

if __name__ == "__main__":
    nums = [23,45,67,12,89,34,56,78,91,15,62,37]
    for k,v in analyze(nums).items():
        print(f"  {k}: {v}")
