---
name: linear-tickets
description: Create, rewrite, or review YggdrasilCRM Linear tickets in plain language for all stakeholders. Use when drafting issue titles, descriptions, or success criteria. Focus on what is needed and why it matters, not implementation details.
---

# Linear tickets

## Purpose

Write tickets that stakeholders can understand without reading code. Explain the needed change, who benefits, and why it matters. Use this standard for features, bugs, research, and internal improvements.

Follow the repository's planning rules in `AGENTS.md`. Use the Linear MCP and the YggdrasilCRM project for issues and project documents. Verify the project's team in Linear; do not assume a team or change issue status without approval.

Draft ticket content in chat and get explicit user approval before creating or updating issues. Link relevant specs and ADRs in Linear, interface designs in the designated Figma file, and technical diagrams in FigJam. Do not create a parallel ticket list in the repository.

## Writing rules

- Keep each ticket focused on one clear outcome. Split unrelated outcomes into separate tickets.
- Use simple English, short sentences, and concrete terms. Explain necessary technical terms.
- Name the people affected when known: Huginn & Muninn staff, operators, maintainers, or other confirmed stakeholders. Do not assume every ticket is an end-user feature.
- Write a short title that names the needed outcome. Avoid vague titles such as "Improve the CRM" and solution-first titles such as "Add a Redis cache."
- Describe what must change and why it matters. Do not prescribe files, classes, database tables, libraries, endpoints, algorithms, or coding steps.
- Include a technical constraint only when it is a confirmed requirement needed to understand or accept the outcome. State the constraint without turning it into an implementation plan.
- Keep implementation notes in linked technical material or progress comments, not in the ticket's requirements.
- Use observable success criteria. Describe results that a stakeholder can check, not development activities such as "write tests" or "refactor the service."
- Do not invent impact, metrics, deadlines, affected groups, or requirements. Ask a focused question when missing information changes the scope or purpose. Label unresolved points as open questions.
- Keep the description short. Use only the detail needed for a shared understanding. Do not force an "As a..., I want..., so that..." sentence.

## Default format

Use this structure. Usually, one or two sentences per section and two to four success criteria are enough. These are guides, not quotas.

```markdown
## What
[The needed change or outcome, and who it affects.]

## Why
[The current problem or opportunity, and the value of addressing it.]

## Success criteria
- [An observable result.]
- [Another result needed to accept the work.]
```

Add an **Open questions** or **Out of scope** section only when needed. Do not add empty sections or repeat the same information in each section.

For bugs, include the observed and expected behavior in **What**. Add short reproduction steps only when known and useful. Reproduction steps describe the problem, not how to fix it.

For research, state the question or decision to resolve. Success means useful evidence and a clear recommendation, not a predetermined implementation.

## Example: staff outcome

These examples show the writing style. They are not approved MVP requirements.

Title: **Help staff find the right customer record**

```markdown
## What
Staff can find a customer record by the customer's name.

## Why
Staff need to find the right record before reviewing or updating customer information.

## Success criteria
- Staff can find an existing customer by name.
- When no customer matches, staff see a clear message.
```

## Example: internal outcome

Title: **Help operators identify failed customer imports**

```markdown
## What
Operators can identify which customer imports failed and when the failures happened.

## Why
Operators need this information to investigate missing customer records without manually checking every source.

## Success criteria
- Operators can distinguish failed imports from successful imports.
- Each failure identifies the affected source and the time of the attempt.
```

## Before saving

1. Read the matching issue and check for duplicates before creating a new one.
2. Check that the title and description explain the outcome and value to someone outside engineering.
3. Remove implementation instructions, unsupported claims, and repeated text.
4. Check that success criteria cover the requested scope without adding new requirements.
5. Get explicit approval for the content and destination before saving. Use the YggdrasilCRM project and its verified team. For updates, preserve unrelated content and metadata. Do not guess an assignee, priority, deadline, or status.
6. Share the issue link and flag any open questions. Do not claim an issue was saved if Linear is unavailable.
