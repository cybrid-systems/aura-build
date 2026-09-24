import json
import sys

def solve(prices, k):
    n = len(prices)
    if n == 0 or k == 0:
        return 0
    
    # If k >= n/2, we can do as many transactions as we want
    if k >= n // 2:
        profit = 0
        for i in range(1, n):
            if prices[i] > prices[i-1]:
                profit += prices[i] - prices[i-1]
        return profit
    
    # DP with rolling arrays
    # hold[j] = max profit ending with a share held, having used j transactions (the buy counts as starting a transaction)
    # cash[j] = max profit ending without a share, having completed j transactions
    hold = [-10**9] * (k + 1)
    cash = [0] * (k + 1)
    
    for price in prices:
        for j in range(1, k + 1):
            # Option 1: keep previous hold state (do nothing today)
            # Option 2: buy today - takes cash from previous cash[j-1] minus price
            # hold[j] = max(hold[j], cash[j-1] - price)  # Wait, this is wrong
            
            # Let me reconsider. Let's define:
            # hold[j] = max profit after processing some days, currently holding a stock, with j transactions used so far (bought but not sold yet counts as j-1 completed + 1 ongoing)
            # Actually, simpler: 
            # dp[i][j][0] = max profit on day i with j transactions done, not holding stock
            # dp[i][j][1] = max profit on day i with j transactions done (the current buy counts toward j), holding stock
            
            # cash[j] = max profit, not holding, j transactions completed
            # hold[j] = max profit, holding, j-1 transactions completed (current is ongoing)
            # So buying consumes transaction budget: hold[j] after buying means j-1 transactions completed
            
            # Let me redefine cleanly:
            # cash[j] = not holding, j transactions completed
            # hold[j] = holding, j transactions started but only j-1 completed
            
            # Hmm, that's confusing. Let me use the standard approach:
            # buy[j] = max profit ending with holding stock, having done at most j-1 complete transactions
            # sell[j] = max profit ending with no stock, having done at most j complete transactions
            
            pass
        # Recompute with clearer formulation
        break
    
    # Reset and use clear formulation
    # Let me use: profit[t][s] where t = transactions used, s = 0 (no stock) or 1 (holding)
    # Initial: profit[0][0] = 0, profit[0][1] = -inf
    # Transition:
    #   profit[t][0] = max(profit[t][0], profit[t][1] + price)   # sell today
    #   profit[t][1] = max(profit[t][1], profit[t-1][0] - price) # buy today (uses transaction t)
    
    cash = [0] + [-10**9] * k  # cash[t] = not holding, t transactions done
    hold = [0] + [-10**9] * k  # hold[t] = holding, t-1 transactions done + current ongoing
    # Actually hold[t] should represent holding with t transactions "in progress" counting the buy
    # So buying costs one transaction: hold[t] after buy means we've used t transactions (t-1 done + 1 ongoing)
    
    # Standard LeetCode formulation:
    # buy[j] = max profit after buying (holding stock), considering j transactions (the j-th transaction is ongoing)
    # sell[j] = max profit after selling (not holding), considering j transactions (j transactions completed)
    # buy[j] = max(buy[j], sell[j-1] - price)  # buy uses the j-th transaction budget
    # sell[j] = max(sell[j], buy[j] + price)   # sell completes the j-th transaction
    
    # Hmm, but if j=0, we can't buy. Let me use this:
    buy = [-10**9] * (k + 1)
    sell = [0] * (k + 1)
    
    for price in prices:
        for j in range(1, k + 1):
            # If we buy today, we use transaction j; we come from sell[j-1]
            new_buy = sell[j-1] - price
            if new_buy > buy[j]:
                buy[j] = new_buy
            # If we sell today, we complete transaction j; we come from buy[j]
            new_sell = buy[j] + price
            if new_sell > sell[j]:
                sell[j] = new_sell
    
    return sell[k]


CASES = [
    {"prices": [2, 4, 1, 7, 5, 3, 6, 4], "k": 2},
    {"prices": [3, 2, 6, 5, 0, 3], "k": 2},
    {"prices": [1, 2, 3, 4, 5], "k": 2},
    {"prices": [], "k": 2},
    {"prices": [1, 2], "k": 0},
    {"prices": [1], "k": 1},
    {"prices": [1, 5, 2, 8, 3, 9], "k": 3},
    {"prices": [5, 4, 3, 2, 1], "k": 2},
    {"prices": [1, 2, 4, 2, 5, 7, 2, 4, 9, 0], "k": 3},
]


if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        out = solve(case["prices"], case["k"])
        results.append({"id": i, "input": {"prices": case["prices"], "k": case["k"]}, "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
