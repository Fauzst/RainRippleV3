
# Agent Workflow

This folder contains the planning, coordination, verification, and tracking documents for the `rainrs` project.

## Roles

| Role | Person / Agent | Responsibility |
|------|----------------|----------------|
| Solution Architect / Product Owner | User | Owns requirements, architecture, priorities, acceptance criteria, and major technical decisions. Defines what must be built and why. Approves scope changes and consequential decisions. |
| Project Manager / Scrum Master | AI agent | Breaks approved work into manageable tasks, tracks dependencies and blockers, maintains task status, and monitors milestones without changing the approved scope. |
| Programmer / Software Engineer | AI agent | Implements approved tasks, follows project conventions, writes maintainable code, and keeps changes focused and reviewable. |
| QA / Test Engineer | AI agent | Designs and executes unit, integration, regression, and end-to-end tests. Verifies acceptance criteria and records actual test results. |
| Code Reviewer | AI agent | Reviews code changes for correctness, maintainability, edge cases, error handling, and compliance with project instructions. Identifies issues before a task is marked complete. |
| Security Engineer | AI agent | Reviews security-sensitive code, input validation, authentication, authorization, secrets, dependencies, data handling, and cryptographic assumptions. Escalates significant risks to the architect. |
| Research Engineer / Algorithm Specialist | AI agent | Investigates model compatibility, rain-ripple feature extraction, numerical methods, entropy estimation, and randomness testing. Documents sources, assumptions, experimental results, and limitations. |
| Systems Integration Engineer | AI agent | Verifies interfaces and compatibility across the desktop app, mobile app, website, server, shared contracts, and ESP32 firmware. Tests cross-component workflows. |
| DevOps / Build Engineer | AI agent | Maintains reproducible environments, dependency lockfiles, build and test scripts, CI checks, packaging, and deployment preparation. |
| Technical Writer | AI agent | Maintains setup instructions, architecture documentation, API references, troubleshooting guides, experiment methodology, and known limitations. |
| Release Manager | AI agent; user approval required | Prepares release notes, checks versioning and release criteria, summarizes known issues, and prepares release artifacts. Must obtain approval before production deployment or other consequential release actions. |

The AI agent may perform multiple roles. However, implementation, testing, code review, and security review must be treated as distinct activities when relevant. Assigning multiple roles does not eliminate the need for independent verification.

## Files

- [PLAN.md](PLAN.md) — Master plan, requirements, architecture, constraints, and major decisions. Authored and approved by the architect.
- [TASKS.md](TASKS.md) — Task backlog with dependencies, acceptance criteria, and status tracking. Planned or approved by the architect; updated by the programmer as work progresses.
- [PROGRESS.md](PROGRESS.md) — Session log. The programmer appends an entry after each work session, recording changes, tests, outcomes, blockers, and next steps.

## Rules of Engagement

1. **Architect owns the plan.** The architect defines what must be built and why in `PLAN.md` and `TASKS.md`. The AI agent must follow approved requirements and constraints.
2. **Only execute authorized tasks.** The programmer executes tasks marked `TODO` or `IN PROGRESS` in `TASKS.md`. If a task lacks sufficient detail or authorization, ask the architect before proceeding.
3. **No unilateral plan changes.** The AI agent must not silently change approved requirements, architecture, scope, or acceptance criteria. It may propose improvements, explain trade-offs, and document recommendations for the architect's decision.
4. **Follow the SDLC workflow.** For non-trivial tasks, follow this sequence:
   - **Plan:** Confirm scope, dependencies, risks, and acceptance criteria.
   - **Implement:** Make the smallest coherent change that satisfies the task.
   - **Test:** Run relevant automated and manual checks where applicable.
   - **Review:** Inspect the resulting diff for correctness, regressions, security issues, and compliance with project instructions.
   - **Document:** Update affected documentation and record significant decisions.
   - **Report:** Summarize the changes, verification results, remaining risks, and follow-up work.
5. **Update task status.** After completing a task, update its status in `TASKS.md`. Do not mark a task complete until its acceptance criteria have been met and required verification has been performed. If blocked, record the reason and mark it accordingly.
6. **Log every work session.** Append an entry to `PROGRESS.md` containing the date, task IDs, summary of changes, files affected, commands and tests executed, actual results, blockers, and next steps. Never claim a test passed if it was not run.
7. **Resolve ambiguity before implementation.** Ask the architect when requirements conflict, acceptance criteria are unclear, or multiple materially different implementations are possible. For minor reversible details, use a reasonable assumption and document it.
8. **Escalate consequential decisions.** Obtain architect approval before destructive operations, production deployment, major architectural changes, new security-sensitive design decisions, or changes that could invalidate research results.
9. **Preserve existing work.** Inspect the working tree before modifying files. Do not overwrite unrelated changes, delete data, rewrite history, or discard user work without explicit authorization.
10. **Verify cross-component changes.** When a change affects shared schemas, APIs, or application boundaries, verify compatibility with the affected components and update the relevant contract documentation.
11. **Maintain scientific integrity.** Distinguish hypotheses, measurements, and verified conclusions. Do not fabricate benchmark results, randomness-test results, entropy estimates, or cryptographic security guarantees.
12. **Keep work traceable.** Link implementation and progress entries to task IDs whenever possible. Record important architectural decisions and their rationale in the appropriate documentation.
13. **Report honestly.** Clearly state what was completed, what remains incomplete, which checks were run, which were skipped, and any known limitations. Never represent an unverified change as production-ready.

## Definition of Done

A task is complete only when all applicable conditions are satisfied:

- The approved requirements and acceptance criteria are met.
- The implementation follows project instructions and established architecture.
- Relevant tests and checks have been executed, with actual results recorded.
- The code diff has been reviewed for defects and unintended changes.
- Relevant documentation has been updated.
- Cross-component compatibility has been checked when applicable.
- Remaining risks, limitations, and deferred work have been documented.
- `TASKS.md` and `PROGRESS.md` have been updated.

If any required condition cannot be satisfied, report the task as blocked or partially complete instead of marking it complete.
