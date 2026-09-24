def solve(votes_at, votes_for, times):
    # Preprocess prefix leaders
    leaders = []
    counts = {}
    current_leader = None
    max_votes = 0
    for vid in votes_for:
        counts[vid] = counts.get(vid, 0) + 1
        if counts[vid] >= max_votes:
            # tie -> smaller id wins
            if counts[vid] > max_votes or (current_leader is None) or vid < current_leader:
                max_votes = counts[vid]
                current_leader = vid
        leaders.append(current_leader)
    
    # Answer queries with binary search
    from bisect import bisect_right
    result = []
    for t in times:
        # Find rightmost vote-at <= t
        idx = bisect_right(votes_at, t) - 1
        if idx < 0:
            result.append(None)
        else:
            result.append(leaders[idx])
    return result


CASES = [
    # Basic case from problem
    {"votes_at": [0, 5, 10, 15], "votes_for": [1, 2, 2, 1], "times": [3, 12, 15, 20]},
    # Query before any vote
    {"votes_at": [0, 10, 20], "votes_for": [1, 1, 2], "times": [-5, 0, 5]},
    # All same person
    {"votes_at": [0, 1, 2, 3], "votes_for": [5, 5, 5, 5], "times": [0, 2, 3, 100]},
    # Ties with smaller id winning
    {"votes_at": [0, 5, 10], "votes_for": [1, 2, 3], "times": [0, 5, 10, 15]},
    # Leader changes mid-query
    {"votes_at": [0, 4, 8, 12, 16, 20], "votes_for": [2, 1, 2, 1, 2, 1], "times": [1, 5, 9, 13, 17, 21]},
    # Single vote, multiple queries
    {"votes_at": [0], "votes_for": [42], "times": [0, 1, 2]},
    # Large gap with no queries in between
    {"votes_at": [0, 100, 200, 300], "votes_for": [3, 1, 2, 4], "times": [50, 150, 250, 350]},
    # Tie at leader shift
    {"votes_at": [0, 5, 10, 15], "votes_for": [2, 1, 1, 3], "times": [3, 8, 12, 16]},
]


if __name__ == '__main__':
    import json
    out = []
    for i, c in enumerate(CASES):
        res = solve(c["votes_at"], c["votes_for"], c["times"])
        out.append({"id": i, "input": c, "expected": json.dumps(res, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
