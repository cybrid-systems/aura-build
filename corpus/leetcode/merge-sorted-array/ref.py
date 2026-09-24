import sys
import json
import re

def parse_case(s):
    # Format: CASE0=m=3,n=2,nums1=[1,2,3,0,0,0],nums2=[2,5,7]
    s = s.strip()
    # Remove prefix CASE0=
    eq = s.find('=')
    s = s[eq+1:]
    # Parse key=value pairs separated by commas
    pairs = []
    depth = 0
    cur = ''
    for ch in s:
        if ch in '[{(':
            depth += 1
            cur += ch
        elif ch in ']})':
            depth -= 1
            cur += ch
        elif ch == ',' and depth == 0:
            pairs.append(cur)
            cur = ''
        else:
            cur += ch
    if cur:
        pairs.append(cur)
    result = {}
    for p in pairs:
        k, v = p.split('=', 1)
        result[k.strip()] = v.strip()
    return result

def parse_int(s):
    return int(s)

def parse_list(s):
    # s like "[1,2,3]"
    inner = s.strip()[1:-1]
    if not inner:
        return []
    return [int(x.strip()) for x in inner.split(',')]

def solve(m, n, nums1, nums2):
    # In-place merge from the back
    a = nums1
    b = nums2
    i = m - 1
    j = n - 1
    k = m + n - 1
    while i >= 0 and j >= 0:
        if a[i] > b[j]:
            a[k] = a[i]
            i -= 1
        else:
            a[k] = b[j]
            j -= 1
        k -= 1
    while j >= 0:
        a[k] = b[j]
        j -= 1
        k -= 1
    # Return a copy so caller can serialize
    return list(a)

CASES = [
    {"id": 0, "raw": "CASE0=m=3,n=2,nums1=[1,2,3,0,0,0],nums2=[2,5,7]"},
    {"id": 1, "raw": "CASE0=m=1,n=1,nums1=[1,0],nums2=[2]"},
    {"id": 2, "raw": "CASE0=m=0,n=3,nums1=[0,0,0],nums2=[1,2,3]"},
    {"id": 3, "raw": "CASE0=m=3,n=3,nums1=[1,2,3,0,0,0],nums2=[1,2,3]"},
    {"id": 4, "raw": "CASE0=m=4,n=2,nums1=[-3,-1,0,2,0,0],nums2=[-2,1]"},
    {"id": 5, "raw": "CASE0=m=2,n=0,nums1=[5,6,0],nums2=[]"},
    {"id": 6, "raw": "CASE0=m=5,n=5,nums1=[1,3,5,7,9,0,0,0,0,0],nums2=[2,4,6,8,10]"},
    {"id": 7, "raw": "CASE0=m=3,n=3,nums1=[4,5,6,0,0,0],nums2=[1,2,3]"},
]

if __name__ == '__main__':
    out = []
    for c in CASES:
        parsed = parse_case(c["raw"])
        m = parse_int(parsed["m"])
        n = parse_int(parsed["n"])
        nums1 = parse_list(parsed["nums1"])
        nums2 = parse_list(parsed["nums2"])
        result = solve(m, n, nums1, nums2)
        out.append({
            "id": c["id"],
            "input": {"m": m, "n": n, "nums1": nums1, "nums2": nums2},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
