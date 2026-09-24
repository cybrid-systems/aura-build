def solve(s: str, p: str) -> list[int]:
    if not p or len(p) > len(s):
        return []
    
    k = len(p)
    # Use ord-based counts for full ASCII support
    need = [0] * 128
    have = [0] * 128
    for ch in p:
        need[ord(ch)] += 1
    
    result = []
    diff = k  # number of characters that still differ (initialized to window length)
    
    for i in range(len(s)):
        ci = ord(s[i])
        have[ci] += 1
        if have[ci] <= need[ci]:
            diff -= 1
        else:
            # if it just exceeded by one, difference grows
            pass  # handled below with explicit checks
        
        # maintain diff accumulator properly
        # The above simplified; let's use a cleaner approach
        
        # Actually, let's redo: track diff properly
    # ...
    return result


# Cleaner implementation below using a diff counter
def solve(s: str, p: str) -> list[int]:
    if not p or len(p) > len(s):
        return []
    
    k = len(p)
    need = [0] * 128
    have = [0] * 128
    for ch in p:
        need[ord(ch)] += 1
    
    # diff = how many character counts differ between have and need
    diff = 0
    for c in range(128):
        diff += abs(need[c])
    
    result = []
    for i in range(len(s)):
        out_ch = s[i - k] if i >= k else None
        in_ch = s[i]
        if out_ch is not None:
            old_have = have[ord(out_ch)]
            old_need = need[ord(out_ch)]
            # removing out_ch from window
            have[ord(out_ch)] -= 1
            # update diff
            # contribution of out_ch changes from |old_have - old_need| to |old_have-1 - old_need|
            new = have[ord(out_ch)]
            diff += (new - old_need) if (new - old_need) >= 0 else -(new - old_need)
            diff -= (old_have - old_need) if (old_have - old_need) >= 0 else -(old_have - old_need)
        
        # adding in_ch to window
        old_have = have[ord(in_ch)]
        old_need = need[ord(in_ch)]
        have[ord(in_ch)] += 1
        new = have[ord(in_ch)]
        diff += (new - old_need) if (new - old_need) >= 0 else -(new - old_need)
        diff -= (old_have - old_need) if (old_have - old_need) >= 0 else -(old_have - old_need)
        
        if i >= k - 1 and diff == 0:
            result.append(i - k + 1)
    
    return result


CASES = [
    {"s": "cbaebabacd", "p": "abc"},
    {"s": "abab", "p": "ab"},
    {"s": "a", "p": "a"},
    {"s": "a", "p": "b"},
    {"s": "af", "p": "be"},
    {"s": "abcdef", "p": "f"},
    {"s": "bacdgabcda", "p": "abcd"},
    {"s": "", "p": "a"},
]


if __name__ == '__main__':
    import json
    out = []
    for idx, case in enumerate(CASES):
        result = solve(case["s"], case["p"])
        out.append({"id": idx, "input": case, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, ensure_ascii=False))
