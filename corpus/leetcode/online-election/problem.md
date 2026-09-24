# Online Election

## Problem

In an election, votes are cast over time. At each vote, a person is identified by an integer `id`. The person with the most votes at a given moment is the current leader (ties are broken in favor of the smaller `id`).

You must support two operations:

- **Vote cast**: record that person `id` received a vote at a given timestamp.
- **Query**: given a timestamp `t`, report the id of the leader at that moment. If the timestamp `t` falls exactly between two vote events, return the leader of the most recent vote at or before `t`. Timestamps in queries strictly increase.

## Function Signature

```
(define (solve votes-at votes-for times)
  ;; votes-at:  vector<int> of timestamps when votes were cast (strictly increasing)
  ;; votes-for: vector<int> of ids corresponding to each vote (same length as votes-at)
  ;; times:     vector<int> of query timestamps (strictly increasing)
  ;; returns:   vector<int> where result[i] is the leader's id at query times[i]
  )
```

## Input Convention

The harness feeds structured parameters. A typical CASE line looks like:

```
CASE0=(votes-at=[0,5,10,15] votes-for=[1,2,2,1] times=[3,12,15,20])
```

Return the resulting leader ids as a flat list:

```
ANS0=[2,2,1,1]
```

## Notes

- `votes-at` is strictly increasing; the length `n` of `votes-at` equals `len(votes-for)`.
- `times` is strictly increasing and may extend beyond the last vote timestamp; in that case use the leader of the final vote.
- A clean approach preprocesses the prefix leader after each vote in O(n), then answers each query in O(log n) via binary search on `votes-at`.
- Constraints typically allow an O(n + q log n) solution comfortably; O(n + q) is achievable with two pointers.
