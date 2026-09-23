# Value assessment

## vs grok-build (surface cousin)

| Dimension | grok-build | aura-build |
|-----------|------------|------------|
| Core loop | Agent edits files / shell | Mutate live FlatAST worldlines |
| Concurrency | Sessions / worktrees | Fiber multi-candidate select-best |
| Memory | Chat + tools | Trajectory store + L1/L2/L3 harness |
| Moat claim | Product + model surface | Runtime floor semantics (deny plugin-as-moat) |
| Roadmap echo | TUI / headless / ACP | Same **surface order** only; substance differs |

Use grok-build as a **shape reference** for headless→CI→ACP. Do not copy the agent ontology.

## vs Copilot / generic coding agents

Copilot-class tools optimize **mail to a dead tree** (completion, PR patch, chat). aura-build optimizes **decisions on a live object graph** with audit and incr compile in the fitness function. Completions remain useful as soft inputs; they are not the product.

## Dogfood Aura — efficiency KPIs

Track on cybrid-systems/aura (and aura-repo profile):

| KPI | Intent |
|-----|--------|
| **Time-to-green** | Wall time prompt → selected worldline passing tests |
| **Incr compile ratio** | Share of evals that stayed incremental (storm still incr) |
| **Worldline waste** | Candidates evaluated vs selected — quality of scout |
| **Trajectory yield** | Valid episodes / eng-hour — flywheel health |
| **Harness canary pass** | L1/L2 promotions that survive canary |
| **Audit coverage** | Mutates with external-dep touch that carry audit_ok |
| **Replay fidelity** | Same seed+runtime → same select-best |

If KPIs improve only by shipping more Postman mail, we are measuring the wrong product.
