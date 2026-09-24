# Asteroid Collision

## Problem

We are given an integer array `asteroids` where each value represents an asteroid in a row, moving along a number line:

- Positive value → moves to the **right**.
- Negative value → moves to the **left**.

All asteroids travel at the same speed. When two asteroids collide:
- The **smaller** absolute value is destroyed.
- If they are equal in absolute value, **both** are destroyed.
- Two asteroids moving in the **same direction** (both right or both left) never meet.

Return the final state of the asteroids, preserving the order they appear from left to right in the resulting array.

## Input

No external input. The test harness calls your function with a fixed test:

- `CASE0=1 args=[5,10,-5]`
- `CASE1=1 args=[8,-8]`
- `CASE2=1 args=[10,2,-5]`

## Output

Write each result on its own line as a space-separated list, e.g.

```
result=[5 10]
result=[]
result=[10]
```

## Function Signature

```scheme
(define (solve asteroids) -> list?)
```

## Notes

- A **stack** naturally models this: push right-moving asteroids, and on encountering a left-moving one, repeatedly pop the stack to resolve collisions with smaller same-direction survivors.
- After processing, the stack (left-to-right) is already the correct order — no reversal needed.
- An asteroid pushed earlier can only be destroyed by an asteroid that arrives later from the left.
