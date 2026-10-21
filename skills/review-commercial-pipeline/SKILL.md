---
name: review-commercial-pipeline
description: Review a bounded commercial pipeline against campaign criteria, write evidence-backed assessments to a configured CRM sheet, and verify each write before reporting completion.
---
# Review a commercial pipeline

Read the campaign and source leads. Use qualify-lead for the authoritative business criteria. Select a literal source excerpt for an extractive summary, identify conflict with structured fields and propose one next action in Portuguese. The runtime checks the quote and applies a conservative review gate to budget ambiguities. Never silently replace a budget or infer contact consent.

Use record_assessment only for IDs returned by read_leads. A conflicting message requires human clarification; it does not authorize changing source fields. Read back every written assessment with verify_record. Finish is available only when all records are verified and refreshes those checks.

A failed or ambiguous connector write stops the run. Inspect the actual row before attempting recovery. Approval, sending and deletion are outside this skill's tools and scope.
