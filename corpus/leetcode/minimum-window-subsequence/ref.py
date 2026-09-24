def solve(s: str, t: str) -> str:
    S, T = s, t
    n, m = len(S), len(T)
    if m > n:
        return ""
    
    best_len = float('inf')
    best_start = -1
    best_end = -1
    
    i = 0
    while i <= n - m:
        # Forward scan: find end position j where T[0..k] matches ending at j
        j = i
        k = 0
        while j < n and k < m:
            if S[j] == T[k]:
                k += 1
            j += 1
        if k < m:
            # T cannot be matched starting from i; advance
            i += 1
            continue
        # T matches in S[i..j-1]; end is j-1
        end = j - 1
        
        # Backward scan: find latest start so T still matches in S[start..end]
        start = end
        k = m - 1
        while start >= i:
            if S[start] == T[k]:
                k -= 1
                if k < 0:
                    break
            start -= 1
        
        win_len = end - start
        if win_len < best_len or (win_len == best_len and start < best_start):
            best_len = win_len
            best_start = start
            best_end = end
        
        # Advance: next possible start is start+1 (or end - best_len + 1 if we had one)
        if best_len < float('inf'):
            i = start + 1
        else:
            i += 1
    
    if best_start == -1:
        return ""
    return S[best_start:best_end + 1]


CASES = [
    {"s": "abacbabc", "t": "abcabc"},
    {"s": "abc", "t": "abc"},
    {"s": "abc", "t": "abcd"},
    {"s": "aaaaa", "t": "aaa"},
    {"s": "cabbac", "t": "ab"},
    {"s": "a", "t": "a"},
    {"s": "abcdebdde", "t": "bde"},
    {"s": "jmeqksfrqdcvcwv", "t": "krqe"},
    {"s": "ofashionnation", "t": "ofn"},
    {"s": "xyzabcxyzabc", "t": "abc"},
]


if __name__ == '__main__':
    import json
    out = []
    for idx, case in enumerate(CASES):
        s = case["s"]
        t = case["t"]
        ans = solve(s, t)
        out.append({"id": idx, "input": {"s": s, "t": t}, "expected": ans})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
