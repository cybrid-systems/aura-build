def simplify_path(path: str) -> str:
    parts = path.split('/')
    stack = []
    for part in parts:
        if part == '' or part == '.':
            continue
        if part == '..':
            if stack:
                stack.pop()
        else:
            stack.append(part)
    return '/' + '/'.join(stack)


def solve(path: str) -> str:
    return simplify_path(path)


CASES = [
    {"path": "/a/./b/../../c/"},
    {"path": "/home//foo/"},
    {"path": "/../"},
    {"path": "/a/b/c/d/./e/../f"},
    {"path": "/"},
    {"path": "/a/b/c"},
    {"path": "/a/.."},
    {"path": "/a/b/../../../"},
    {"path": "/.../"},
    {"path": "/foo/./bar/../baz//qux/"},
]


if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
