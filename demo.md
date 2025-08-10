# Hackathon Demo: Backstage MCP Server (4-minute live demo)

Purpose: Demonstrate an MCP server that connects to Backstage’s Software Catalog to pull API/component context (OpenAPI specs, ownership, versions, relations) so an AI agent can guide and automate migration of dependent services when a new API version is released.

Outcome: In 4 minutes, show how a developer uses an MCP-enabled assistant to (a) discover a breaking Payments API v2, (b) fetch/diff v1→v2 from Backstage, (c) generate/apply a minimal migration for one service (checkout-service), and (d) kick off follow-up work for another dependent service (subscriptions-service).

---

## Cast and Demo Environment

- Roles
  - Presenter (developer of a service that depends on Payments API)
  - MCP-enabled assistant (using the Backstage MCP server). In this Cline. 
  - Backstage Software Catalog (source of truth for APIs and components)

- Entities in Backstage
  - API: Payments API (v1 deprecated, v2 current)
  - Components:
    - checkout-service (Node/TypeScript)
    - subscriptions-service (Python/FastAPI)
  - Relations:
    - checkout-service and subscriptions-service depend on Payments API

- MCP Server Capabilities (for demo narrative)
  - Discover entities: list APIs/components, filter by relations/annotations
  - Fetch API specs: get OpenAPI for a specific API/version
  - Map dependents: find which components depend on a given API

- Scenario Data (breaking changes to showcase)
  - Path/base change:
    - POST /payments → POST /v2/payments
    - GET /payments/{id} → GET /v2/payments/{paymentId}
  - Required header added for idempotency on POST:
    - Idempotency-Key (string)
  - Request/response schema changes:
    - request amountCents (integer) → amount (number, 2 decimal places)
    - response status → state (enum narrowed: pending, authorized, captured, failed)
  - Deprecation metadata in Backstage for v1 and lifecycle info (owner, system, team)

---

## Minute-by-minute Script (4:00)

00:00–00:30 — Set the Stage
- Show the Backstage Catalog page for Payments API.
  - Point out: Two versions visible, v1 (deprecated) and v2 (current), with a deprecation date banner. **Highlight what a common scenario this is and the negative effects that legacy code has on operational efficiency**. 
  - The API entity has links to OpenAPI definitions for both versions, ownership, and dependents.
- Transition: “We’ll migrate checkout-service to Payments API v2 in under 3 minutes using our Backstage MCP server.”

00:30–01:15 — Show the Problem
- Open checkout-service repo (a small Node/TS snippet visible) in Visual Studio Code with Cline installed.
  - Show a v1 call: POST /payments with body containing amountCents and no Idempotency-Key header; and GET /payments/{id} to poll status.
- Run a quick test or curl that hits the v1 endpoint(s).
  - Display a response header warning (e.g., Deprecation: true).
- Transition: “Let’s ask the MCP-enabled assistant what changed in v2 and what we need to do.”

01:15–02:30 — Use MCP + Backstage Context
- Prompt the assistant to discover and diff from Backstage:
  ```
  Using Backstage, locate the Payments API, fetch OpenAPI v1 and v2, and produce a developer-friendly diff highlighting breaking changes that affect checkout-service.
  ```
- Assistant calls the MCP server:
  - Finds Payments API entity, pulls OpenAPI v1 and v2.
  - Produces a concise diff summary:
    - Path changes: /payments → /v2/payments; /payments/{id} → /v2/payments/{paymentId}
    - Required header on POST: Idempotency-Key (string)
    - Request field: amountCents (integer) → amount (number with 2 decimals)
    - Response field: status → state (enum narrowed)
- Optional: Show it also lists dependents and confirms checkout-service and subscriptions-service are impacted.

02:30–03:30 — Generate and Apply Migration for checkout-service
- Prompt the assistant:
  ```
  Propose a minimal safe patch for checkout-service to adopt Payments API v2. Include:
  - Update endpoints: /payments → /v2/payments and /payments/{id} → /v2/payments/{paymentId}
  - Add Idempotency-Key header for POST (read from ENV or generated UUID)
  - Map request field amountCents → amount (convert integer cents → decimal string)
  - Map response status → state
  Generate a PR title and body referencing the Backstage API entity and the v1→v2 diff.
  ```
- Assistant returns:
  - A small patch/diff (1–3 files) with code changes and a brief unit test or contract test update.
  - PR text with links to the Backstage entity and summary of changes/breaking notes.
- Apply the patch (pre-baked branch is fine). Show tests quickly running green or a small smoke test.
- Transition: “checkout-service is done; now let’s address other dependents.”

03:30–04:00 — Plan for subscriptions-service and Broadcast
- Prompt the assistant:
  ```
  From Backstage, list all components that depend on Payments API v1 and open issues for the remaining one(s) with a migration checklist and links to the v2 spec and diff.
  ```
- Assistant returns:
  - Dependents list (e.g., subscriptions-service).
  - Ready-to-open issue text per dependent with checklist and references to Backstage and OpenAPI v2.
- Close: Emphasize platform impact: Backstage + MCP gives API/platform teams a programmatic, organization-wide way to coordinate migrations with real context.

---

## What to Prepare Ahead of Time (Minimal Setup)

- Backstage data (can be local or static YAMLs committed to the demo repo)
  - API: Payments API entity with:
    - spec.type: openapi
    - spec.definition: two references (v1 and v2), or two API entities with version annotations
    - lifecycle: v1 deprecated, v2 current
    - owner/team/system annotations
  - Components:
    - checkout-service and subscriptions-service with relations indicating dependency on Payments API
- OpenAPI specs
  - v1 and v2 files reflecting the breaking changes listed above
- Repos (lightweight)
  - checkout-service (Node/TS)
    - Has a simple function creating a payment via POST /payments (v1) with amountCents; a small test
    - Branch ready for applying the automated patch (or pre-created PR for backup)
  - subscriptions-service (Python/FastAPI)
    - Similar v1 usage for recurring payments, no changes applied during the live demo
- Assistant integration
  - MCP server configured in the assistant’s settings pointing at the local Backstage instance or static YAML catalog
  - API tokens/permissions if the assistant will open issues/PRs in a real VCS (optional; pre-baked PRs/issues acceptable)
- Offline-friendly fallback
  - Keep copies of Backstage entity YAML and OpenAPI specs in the repo
  - If Backstage UI/network is flaky, show YAML files and proceed; MCP server can read from file URLs

---

## Talking Points (while actions run)

- “All context is sourced from Backstage—ownership, versions, dependents, and OpenAPI definitions—so migrations are consistent and auditable.”
- “The MCP server turns the catalog into tools: list dependents, fetch specs, diff versions, propose code patches, and create work items.”
- “This scales across teams: API owners can broadcast changes and generate migration plans per dependent automatically.”
- "Legacy code creates a drag on operational efficiency and slows down innovation and the generation of business value."

---

## Example Snippets (Appendix)

Example Backstage API entity (Payments API v2):
```yaml
apiVersion: backstage.io/v1alpha1
kind: API
metadata:
  name: payments-api
  description: Payments domain API
  annotations:
    backstage.io/owner: team-payments
    demo/version: v2
spec:
  type: openapi
  lifecycle: production
  owner: team-payments
  definition: ./apis/payments-v2.yaml
```

Example Backstage Component entity (checkout-service):
```yaml
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: checkout-service
  annotations:
    backstage.io/owner: team-checkout
spec:
  type: service
  lifecycle: production
  owner: team-checkout
  system: commerce
  dependsOn:
    - api:default/payments-api
```

OpenAPI v1 (excerpt):
```yaml
openapi: 3.0.3
info:
  title: Payments API
  version: 1.0.0
paths:
  /payments:
    post:
      summary: Create payment
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                amountCents: { type: integer }
                currency: { type: string }
      responses:
        "201":
          description: Created
          content:
            application/json:
              schema:
                type: object
                properties:
                  id: { type: string }
                  status: { type: string }
  /payments/{id}:
    get:
      summary: Get payment
      parameters:
        - in: path
          name: id
          required: true
          schema: { type: string }
      responses:
        "200":
          description: OK
```

OpenAPI v2 (excerpt with breaking changes):
```yaml
openapi: 3.0.3
info:
  title: Payments API
  version: 2.0.0
paths:
  /v2/payments:
    post:
      summary: Create payment
      parameters:
        - in: header
          name: Idempotency-Key
          required: true
          schema: { type: string }
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                amount:
                  type: number
                  format: decimal
                currency:
                  type: string
      responses:
        "201":
          description: Created
          content:
            application/json:
              schema:
                type: object
                properties:
                  paymentId: { type: string }
                  state:
                    type: string
                    enum: [pending, authorized, captured, failed]
  /v2/payments/{paymentId}:
    get:
      summary: Get payment
      parameters:
        - in: path
          name: paymentId
          required: true
          schema: { type: string }
      responses:
        "200":
          description: OK
```

Example assistant prompts (for the live demo):
```
Using Backstage, locate the Payments API, fetch v1 and v2 OpenAPI, and summarize the breaking changes relevant to checkout-service.
```
```
Generate a minimal patch for checkout-service to adopt v2:
- POST /payments → POST /v2/payments
- Add Idempotency-Key header (value from ENV or generated UUID)
- amountCents (int) → amount (decimal string); update any math and tests
- GET /payments/{id} → GET /v2/payments/{paymentId}
- Map response status → state
Return a diff and a PR title/body referencing the Backstage API entity.
```
```
List all components that depend on Payments API v1 and prepare an issue per component with a migration checklist and links to the v2 spec and diff.
```

---

## Success Criteria (What judges will see)

- Clear linkage from Backstage catalog → assistant context → concrete developer actions.
- A crisp v1→v2 diff surfaced by the assistant in seconds for Payments API.
- A small, believable code change applied to checkout-service and verified.
- Evidence of scalable coordination: generated PR for subscriptions-service with proper references.
