# Narrative — 邮差 vs 活对象 / Postman vs live object

Aura-build is not a prettier shell around an LLM. It is the **dev-time room on the execution floor** of a live FlatAST runtime.

## The postman problem

Most “AI coding” stacks still behave like Postman + git:

1. Serialize intent into a prompt or patch mail.
2. Ship it to a cold workspace (often a worktree clone).
3. Wait for a reply: diff, test log, CI badge.
4. Merge or discard. Context dies between trips.

That loop treats the program as **dead letters**. Every round-trip rehydrates symbols, re-searches files, re-argues about what `NodeId` meant last turn. Soft plugins and editor chrome do not fix the underlying mail protocol.

## The live-object floor

Aura keeps a **hot FlatAST**: stable IDs, query/mutate, concurrency, audit, incremental compile. The “codebase” is not a bag of files waiting for the postman — it is a mutable object graph you can point at.

aura-build sits **on that floor**:

- **Worldlines** — fork candidates as fibers over the same live graph, not as duplicate git checkouts.
- **Select-best** — evaluate fitness (tests, incr-compile cost, audit constraints) and collapse to a winner.
- **Trajectory** — every scout→mutate→eval→select episode is durable fuel for RL and specialist distillation.
- **Self-evolving harness** — L1 strategy code; L2 offline weights; L3 online weights (experimental only).

The interesting work happens in the **0–1%** of the loop that is actually decision + mutation under runtime feedback — not in shipping prettier mail.

## Floor, not agent

Reference surface shape (headless / CI / later ACP) may resemble tools like grok-build. The product north star does not:

| grok-build-like surface | aura-build substance |
|-------------------------|----------------------|
| Terminal agent that edits files | Room that mutates live FlatAST |
| Worktree / patch mail | Hot worldlines |
| Plugin marketplace as moat | Soft ≠ Restricted — deny plugin-as-moat |
| Chat transcript as memory | Trajectory store + evolving L1/L2/L3 |

If Aura is not under the demo, the demo is impossible. If a storm of candidates still cannot stay incremental, we have failed the floor. External deps must remain auditable; trajectories must be reproducible.

## Dogfood

Primary dogfood target: [cybrid-systems/aura](https://github.com/cybrid-systems). aura-build exists to make building Aura (and Aura-shaped repos) faster on Aura itself — then to export the resulting trajectories so the harness and specialists improve.

## One sentence

Stop mailing the codebase. Stand on the execution floor, fan out worldlines, pick the best, and keep the tape.
