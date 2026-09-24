# Task Scheduler

## Statement

You are given `n` tasks, each labeled by an uppercase letter `A` to `Z`. Identical tasks cannot run in two consecutive time slots; there must be at least one slot of rest (or a different task) between two occurrences of the same letter. Every slot holds exactly one task, and an idle slot (rest) is allowed.

Determine the minimum number of time slots required to execute all given tasks while respecting the cooldown constraint.

## Function Signature

```python
def solve(tasks: str) -> int:
    ...
```

## Input / Output (Aura harness convention)

The harness reads cases from `stdin` in the following line format; there is no leading test-case count.

```
CASE0=AAABBC
CASE1=A
CASE2=ABC
CASE3=AAAA
CASE4=ABABAB
```

For each `CASEx=<value>` line, invoke `solve(value)` and write the result as one line:

```
ANS0=<result>
ANS1=<result>
ANS2=<result>
ANS3=<result>
ANS4=<result>
```

Lines that do not start with `CASE` are ignored.

## Notes

- The cooldown is fixed to `1` slot between two identical tasks (i.e., no two identical letters may be adjacent in the schedule).
- Idle slots are permitted; they count toward the total length.
- The answer is at most the number of tasks plus enough idle slots to separate the most frequent task from its repetitions.
- `tasks` is non-empty and contains only uppercase letters `A`–`Z`.
