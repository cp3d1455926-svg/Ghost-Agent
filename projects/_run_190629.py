"""write a data analysis script"""
from collections import Counter
import math

def analyze(data):
    if not data: return {"error": "empty"}
    r = {"count": len(data)}
    if all(isinstance(x, (int, float)) for x in data):
        s = sorted(data); n = len(data); avg = sum(data)/n
        r["min"] = min(data)
        r["max"] = max(data)
        r["sum"] = sum(data)
        r["avg"] = avg
        r["median"] = s[n//2] if n%2 else (s[n//2-1]+s[n//2])/2
        r["std"] = math.sqrt(sum((x-avg)**2 for x in data)/n)
    if all(isinstance(x, str) for x in data):
        lens = [len(x) for x in data]
        r["shortest"] = min(lens)
        r["longest"] = max(lens)
        r["avg_len"] = sum(lens)/len(lens)
        r["common"] = Counter(data).most_common(5)
    return r

if __name__ == "__main__":
    nums = [23,45,67,12,89,34,56,78,91,15,62,37]
    for k,v in analyze(nums).items():
        print("  " + str(k) + ": " + str(v))
