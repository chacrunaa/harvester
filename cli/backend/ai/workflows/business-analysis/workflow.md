# Workflow: business-analysis

Reusable workflow for producing a business-analysis package for any project.

This workflow should be treated as a reusable template, not a project-specific
copy.

## Flow

```text
input materials
  -> context completeness check
  -> clarifying questions
  -> business context
  -> main analysis package
  -> domain analysis
  -> final analytical conclusion
```

## Main Package

1. Product brief
2. Target audience
3. Competitive analysis
4. Business-functional requirements
5. Market size
6. Business model
7. Value proposition
8. Unit economics
9. Product metrics
10. Financial model
11. MVP definition
12. CustDev plan
13. Market insights
14. Python analytics pipeline, when source data exists

## Reuse Plan

Move detailed instruction packs into:

```text
ai/skills/business-analysis/
```

Keep project materials and outputs in the target project.
