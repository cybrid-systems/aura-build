import json


def solve(words: list[str], maxWidth: int) -> list[str]:
    result = []
    i = 0
    n = len(words)
    while i < n:
        # Determine how many words fit on this line
        line_len = len(words[i])
        j = i + 1
        while j < n and line_len + 1 + len(words[j]) <= maxWidth:
            line_len += 1 + len(words[j])
            j += 1
        # words[i:j] are the words for this line
        line_words = words[i:j]
        num_words = j - i
        # Last line or single word: left-justify
        if j == n or num_words == 1:
            line = " ".join(line_words)
            line = line + " " * (maxWidth - len(line))
        else:
            total_spaces = maxWidth - sum(len(w) for w in line_words)
            gaps = num_words - 1
            base = total_spaces // gaps
            extra = total_spaces % gaps
            parts = []
            for k in range(num_words - 1):
                parts.append(line_words[k])
                spaces_for_gap = base + (1 if k < extra else 0)
                parts.append(" " * spaces_for_gap)
            parts.append(line_words[-1])
            line = "".join(parts)
        result.append(line)
        i = j
    return result


CASES = [
    {
        "words": ["This", "is", "an", "example", "of", "text", "justification."],
        "maxWidth": 16,
    },
    {
        "words": ["What", "must", "be", "acknowledgment", "shall", "be"],
        "maxWidth": 16,
    },
    {
        "words": ["Science", "is", "what", "we", "understand"],
        "maxWidth": 20,
    },
    {
        "words": ["Single"],
        "maxWidth": 10,
    },
    {
        "words": ["a", "b", "c"],
        "maxWidth": 3,
    },
    {
        "words": ["Two", "words"],
        "maxWidth": 6,
    },
    {
        "words": ["Listen", "to", "many", "speak", "to", "a", "few", "of", "those", "who", "are", "good", "speakers"],
        "maxWidth": 16,
    },
    {
        "words": ["The", "quick", "brown", "fox", "jumps", "over", "the", "lazy", "dog"],
        "maxWidth": 11,
    },
]


if __name__ == "__main__":
    output = []
    for idx, case in enumerate(CASES):
        result = solve(case["words"], case["maxWidth"])
        expected_str = json.dumps(result, separators=(",", ":"), ensure_ascii=False)
        output.append({"id": idx, "input": case, "expected": expected_str})
    print(json.dumps(output, separators=(",", ":"), ensure_ascii=False))
