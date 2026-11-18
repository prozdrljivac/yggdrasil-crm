# Project Instructions

## Purpose

YggdrasilCRM is a production CRM for Huginn & Muninn.

## Product Planning and Design

- Use the [YggdrasilCRM project in Linear](https://linear.app/huginn-and-muninn/project/yggdrasilcrm-3616337fa948) for product tracking, issues, and project documents, including MVP scope, specs, and ADRs.
- Use the Linear MCP to access the project. Do not create a parallel project tracking system in the repository.
- Create all MVP interface designs in the [MVP Design Figma file](https://www.figma.com/design/DcKlKAAgEIXfh5mfx29L6T/MVP-Design).
- Use FigJam for technical graphs, state diagrams, and architecture diagrams, including context, container, component, and code diagrams. Store these in the [designated Figma folder](https://www.figma.com/files/folder/693495145).
- Draft and agree on content in chat before publishing it to these shared systems.
- During MVP scope definition, do not start implementation without explicit user approval.

## Security Model

- Treat all source code and repository history as public. The application must remain secure when an attacker knows its implementation.
- Do not rely on hidden URLs, client-side checks, or undocumented behavior for security.
- Treat security as a design requirement, not a final review step. Do not claim that the application is free of vulnerabilities.

## Code Readability and Simplicity

- Code must be simple and easy to read. Passing tests alone is not enough.
- Keep each function focused on one clear job. Keep the main flow easy to follow.
- When a function mixes workflow with detailed checks or processing, extract small, clearly named helpers where this makes the code easier to understand.
- Use clear names, named limits, and simple control flow. Avoid unnecessary nesting.
- Do not split code merely to make functions shorter. Avoid needless helpers, layers, and abstractions.
- Prefer clear code over comments or documentation that repeat what the code does. Keep explanations for non-obvious reasons and constraints.
- Before requesting review, check changed code for readability and simplicity. Refactor with tests green and rerun relevant tests after each material change.

## Commit Policy

- All work must be reviewed and accepted by the user before it is committed.
- Do not create a Git commit unless the user has explicitly approved the current changes and asked for them to be committed.
- After making changes, provide a short, simple and clear summary of what changed and why.
- If review feedback requires further changes, leave those changes uncommitted until they are also reviewed and accepted.
