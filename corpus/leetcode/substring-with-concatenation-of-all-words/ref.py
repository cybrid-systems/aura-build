from typing import List
import json
from collections import Counter


def solve(s: str, words: List[str]) -> List[int]:
    if not s or not words or not words[0]:
        return []
    
    n = len(s)
    m = len(words)
    w = len(words[0])
    total_len = m * w
    
    if total_len > n:
        return []
    
    result = []
    need = Counter(words)
    
    # Only check w different starting offsets
    for offset in range(w):
        left = offset
        current = Counter()
        matched = 0
        
        # Slide a window starting at `offset`, jumping by w
        j = offset
        while j + w <= n:
            word = s[j:j + w]
            j += w
            
            if word in need:
                current[word] += 1
                matched += 1
                
                # If we have too many of this word, shrink from left
                while current[word] > need[word]:
                    left_word = s[left:left + w]
                    current[left_word] -= 1
                    matched -= 1
                    left += w
                
                # If all matched, record and shift window by one word
                if matched == m:
                    result.append(left)
                    # Slide forward by one word to find next potential match
                    left_word = s[left:left + w]
                    current[left_word] -= 1
                    matched -= 1
                    left += w
            else:
                # Reset window
                current.clear()
                matched = 0
                left = j
    
    return result


CASES = [
    {"s": "barfoothefoobarman", "words": ["foo", "bar"]},
    {"s": "wordgoodgoodgoodbestword", "words": ["word", "good", "best", "good"]},
    {"s": "barfoofoobarthefoobarman", "words": ["bar", "foo", "the"]},
    {"s": "", "words": ["foo"]},
    {"s": "abcdef", "words": ["a", "b", "c"]},
    {"s": "aaaaaaaaaa", "words": ["a", "a", "a"]},
    {"s": "lingmindrotatom", "words": ["rot", "atom", "mind", "ling"]},
    {"s": "abcabcabc", "words": ["abc", "abc"]},
]


if __name__ == '__main__':
    outputs = []
    for i, case in enumerate(CASES):
        result = solve(case["s"], case["words"])
        outputs.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(outputs, separators=(',', ':'), ensure_ascii=False))
