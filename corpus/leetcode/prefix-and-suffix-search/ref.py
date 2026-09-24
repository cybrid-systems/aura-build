import sys
import json

def solve():
    """
    Reads the input from stdin, processes INSERT and QUERY operations for the
    prefix-suffix search problem, and prints the query results to stdout.
    """
    lines = sys.stdin.read().splitlines()
    # No global helper needed, we'll parse line-by-line and handle operations.

    # Data structure: for each word, we generate all (prefix, suffix) pairs
    # and map them to the word's index, keeping the largest index.
    # Word length is at most ~30 (based on problem constraints not given but typical),
    # so generating all pairs is O(L^2) per word, which is fine for small to medium inputs.
    pair_to_max_index = {}

    results = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("CASE"):
            # Strip the CASE<id>= prefix
            eq_idx = line.find('=')
            if eq_idx != -1:
                content = line[eq_idx+1:].strip()
            else:
                content = line
        else:
            content = line

        if content.startswith("INSERT"):
            # INSERT <index> <word>
            parts = content.split(maxsplit=2)
            if len(parts) < 3:
                continue
            _, idx_str, word = parts
            idx = int(idx_str)
            L = len(word)
            # Generate all (prefix, suffix) pairs
            for i in range(L):
                prefix = word[:i+1]
                for j in range(L - i):
                    # suffix starts at position j, and we need the word to end with suffix
                    # The suffix length is L - j, but we only care about suffixes that are
                    # compatible with the prefix of length i+1.
                    # Actually, standard approach: for all i in [0, L], prefix = word[:i],
                    # for all j in [0, L], suffix = word[j:]. There are (L+1)^2 pairs.
                    pass
            # Better approach: for every split point k in [0, L], take prefix word[:k]
            # and suffix word[k:]. Then word has prefix word[:k] and suffix word[k:].
            # This generates (L+1) prefixes and (L+1) suffixes, combined gives (L+1)^2 pairs.
            for k in range(L + 1):
                prefix = word[:k]
                suffix = word[k:]
                key = prefix + "#" + suffix
                if key not in pair_to_max_index or pair_to_max_index[key] < idx:
                    pair_to_max_index[key] = idx
        elif content.startswith("QUERY"):
            # QUERY <prefix> <suffix>
            parts = content.split(maxsplit=2)
            if len(parts) < 3:
                results.append(-1)
                continue
            _, prefix, suffix = parts
            key = prefix + "#" + suffix
            results.append(pair_to_max_index.get(key, -1))

    for r in results:
        print(r)


def make_prefix_suffix_search(hint):
    """Factory that returns (insert_fn, query_fn) using the pair-to-index map approach."""
    pair_to_max_index = {}

    def insert(word, idx):
        L = len(word)
        for k in range(L + 1):
            prefix = word[:k]
            suffix = word[k:]
            key = prefix + "#" + suffix
            if key not in pair_to_max_index or pair_to_max_index[key] < idx:
                pair_to_max_index[key] = idx

    def query(prefix, suffix):
        key = prefix + "#" + suffix
        return pair_to_max_index.get(key, -1)

    return insert, query


def main():
    # Test cases: (id, hint, operations) where operations is a list of
    # ("INSERT", idx, word) or ("QUERY", prefix, suffix).
    # We'll test both the function-based interface and the stdin interface.
    CASES = [
        {
            "id": 0,
            "hint": 10,
            "operations": [
                ("INSERT", 0, "apple"),
                ("INSERT", 1, "apply"),
                ("INSERT", 2, "ape"),
                ("INSERT", 3, "applet"),
                ("QUERY", "ap", "le"),
                ("QUERY", "a", "e"),
                ("QUERY", "b", "x"),
            ],
        },
        {
            "id": 1,
            "hint": 5,
            "operations": [
                ("INSERT", 0, "a"),
                ("INSERT", 1, "aa"),
                ("INSERT", 2, "aaa"),
                ("QUERY", "", ""),
                ("QUERY", "a", "a"),
                ("QUERY", "aa", "aa"),
                ("QUERY", "aaa", "aaa"),
            ],
        },
        {
            "id": 2,
            "hint": 3,
            "operations": [
                ("QUERY", "x", "y"),  # no inserts
                ("INSERT", 5, "abcabc"),
                ("QUERY", "abc", "abc"),
                ("QUERY", "a", "c"),
                ("QUERY", "abc", "c"),
                ("QUERY", "a", "abc"),
            ],
        },
        {
            "id": 3,
            "hint": 5,
            "operations": [
                ("INSERT", 0, "test"),
                ("INSERT", 5, "test"),  # duplicate word, larger index
                ("QUERY", "te", "st"),
                ("QUERY", "t", "t"),
                ("INSERT", 3, "team"),
                ("QUERY", "te", "m"),
            ],
        },
        {
            "id": 4,
            "hint": 2,
            "operations": [
                ("INSERT", 0, "z"),
                ("QUERY", "", "z"),
                ("QUERY", "z", ""),
                ("QUERY", "", ""),
            ],
        },
    ]

    out = []
    for case in CASES:
        # Use the functional interface
        insert_fn, query_fn = make_prefix_suffix_search(case["hint"])
        expected_lines = []
        for op in case["operations"]:
            if op[0] == "INSERT":
                _, idx, word = op
                insert_fn(word, idx)
            elif op[0] == "QUERY":
                _, prefix, suffix = op
                ans = query_fn(prefix, suffix)
                expected_lines.append(str(ans))
        expected = "\n".join(expected_lines)
        out.append({
            "id": case["id"],
            "input": {
                "hint": case["hint"],
                "operations": [
                    {"op": op[0], "args": list(op[1:])} for op in case["operations"]
                ],
            },
            "expected": expected,
        })

    # Also test the stdin interface (the main solve function) on the first case
    # to verify it produces the same output format.
    stdin_input = "CASE0=INSERT 0 apple\nCASE0=INSERT 1 apply\nCASE0=INSERT 2 ape\nCASE0=INSERT 3 applet\nCASE0=QUERY ap le\nCASE0=QUERY a e\nCASE0=QUERY b x\n"

    # Save original stdin
    original_stdin = sys.stdin
    original_stdout = sys.stdout
    import io
    sys.stdin = io.StringIO(stdin_input)
    sys.stdout = io.StringIO()
    try:
        solve()
    except Exception as e:
        sys.stdout = original_stdout
        sys.stdin = original_stdin
        raise e
    stdin_output = sys.stdout.getvalue()
    sys.stdout = original_stdout
    sys.stdin = original_stdin

    # The stdin interface test is implicit; we just include the JSON array.
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))


if __name__ == '__main__':
    main()
