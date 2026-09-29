# FRONTEND & BACKEND AUDIT REPORT

**Project:** Blockchain-Based Secure Platform for Identity, Access Control, and Digital Asset Management  
**Problem Statement ID:** SIH26125 (Smart India Hackathon 2026)  
**Organization:** Bharat Electronics Limited (BEL), Ministry of Defence  
**Target Architecture:** AWS Serverless (Cognito + API Gateway v2 + Lambda + DynamoDB + Cryptographic Hash Ledger)  
**Audit Date:** September 27, 2026  
**Auditor:** Antigravity Autonomous Agent  

---

## 1. EXECUTIVE SUMMARY

An exhaustive audit of both the local codebase (`c:\Users\kunji\NODE`) and the live deployed AWS cloud backend (`ap-south-1`) was conducted against the official requirements of **Bharat Electronics Limited (BEL)** Problem Statement **SIH26125**.

### Current Maturity Level: **Early Prototype / Skeleton (~15% Complete)**
- **What is working:** The AWS serverless plumbing is sound. An AWS Cognito User Pool, API Gateway v2 HTTP API, Python 3.14 Lambda function, and 3 DynamoDB On-Demand tables exist and communicate with basic JWT authorizer protection.
- **Critical Gaps:**
  1. **Backend Route Coverage:** The Lambda backend and API Gateway currently only implement **1 route (`POST /users`)**. All digital asset endpoints (`/assets`), transfer endpoints, audit queries (`/audit`), and blockchain verification endpoints are **missing**.
  2. **Frontend UI/UX:** The frontend (`sih-frontend`) is a single unstyled prototype file (`App.jsx`). Assets and Audit sections are static text placeholders. There is no role-based view switching, no data tables, no search/filters, and no cryptographic verification tools.
  3. **Problem Statement Compliance (BEL Requirements):** The core defense requirements—Attribute-Based Access Control (ABAC) with security clearance levels, asset provenance lifecycle, cryptographic hash chaining, and tamper-evident proof generation—are not yet implemented.

---

## 2. BACKEND AUDIT (AWS & LOCAL RUNTIME)

### 2.1 Deployed AWS Infrastructure (`ap-south-1`)

| Component | Resource ID / Name | Deployed State | Assessment & Gaps |
| :--- | :--- | :--- | :--- |
| **Compute** | `SIH-Backend` (`arn:aws:lambda:ap-south-1:830021126767:function:SIH-Backend`) | Python 3.14, 128 MB RAM, 3s timeout | **Single-action handler only.** Implements only `POST /users` (user creation with Admin check). Missing router for asset lifecycle, transfers, audits, and blockchain verification. |
| **API Gateway** | `SIH-API` (`hpm91xi4me`) | HTTP API v2, Stage `$default` | **Only 1 route exists (`POST /users`).** Missing routes: `GET /users`, `POST /assets`, `GET /assets`, `GET /assets/{id}`, `PUT /assets/{id}/transfer`, `GET /audit`, `POST /verify`. |
| **Authorizer** | `SIH-Cognito-Authorizer` (`bv35ne`) | JWT Authorizer on `POST /users` | **Sound.** Correctly verifies Cognito JWT issuer and audience (`4q91i6ioggdl51s0hduhmihhm`). Needs to be applied to all future protected routes. |
| **Database: Users** | `SIH-Users` | DynamoDB `PAY_PER_REQUEST`, PK: `userId` | **8 items present.** Stores basic profile (`name`, `email`, `role`, `cognitoUsername`). Lacks defense security clearance levels (`TOP_SECRET`, `SECRET`, `CONFIDENTIAL`, `RESTRICTED`) and unit/department metadata. |
| **Database: Assets** | `SIH-Assets` | DynamoDB `PAY_PER_REQUEST`, PK: `assetId` | **0 items present.** Table exists but has no records, no API routes to read/write, and schema lacks clearance attributes and blockchain transaction anchors. |
| **Database: Audits** | `SIH-AuditEvents` | DynamoDB `PAY_PER_REQUEST`, PK: `eventId` | **0 items present.** Table exists but no backend logic writes to it yet. Lacks hash-chain link (`prevHash`) for cryptographic tamper-proofing. |
| **Identity Pool** | `User pool - vasfpl` (`ap-south-1_k75nvoGAc`) | Cognito User Pool | **Active.** 5 users registered. Lacks custom attributes for security clearance and military/defense division. |
| **Logging** | `/aws/lambda/SIH-Backend` | CloudWatch Log Group | **Active (14 KB stored).** Basic print statements; needs structured JSON logs for auditability. |

### 2.2 Deep Code Audit: `SIH-Backend` (`lambda_function.py`)
- **Strengths:**
  - Extracts caller identity from JWT authorizer context (`event['requestContext']['authorizer']['jwt']['claims']`).
  - Verifies caller role in DynamoDB before permitting user creation.
  - Implements strong password validation (uppercase, lowercase, special characters, minimum 8 characters).
  - Uses `boto3.resource` and `boto3.client` globally outside handler.
- **Defects & Limitations:**
  - **No Dispatch / Routing Router:** The entire `lambda_handler` assumes any request is a user creation request. A multi-route router is needed to support the full REST API.
  - **Table Scan in Caller Lookup:** Line 69 uses `table.scan(FilterExpression="cognitoUsername = :username")`. In DynamoDB, scanning the entire table for every API request is inefficient, slow, and incurs linear read costs. A Global Secondary Index (GSI) on `cognitoUsername` or key lookup is required.
  - **Missing Exception Granularity:** Does not handle specific `botocore.exceptions.ClientError` (such as `UsernameExistsException` from Cognito or `ConditionalCheckFailedException` from DynamoDB).
  - **Zero Audit Trail Generation:** When an Admin creates a user, no audit record is written to `SIH-AuditEvents`.

---

## 3. FRONTEND AUDIT (`sih-frontend`)

### 3.1 Architecture & Setup
- **Framework:** React 19.2 + Vite 8.3 + AWS Amplify SDK 6.22.
- **Component Structure:** Monolithic. The entire UI is written inside a single 300-line file ([App.jsx](file:///c:/Users/kunji/NODE/sih-frontend/src/App.jsx)).
- **State Management:** Local React `useState` hooks only. No persistent session context or role-based permission state.

### 3.2 Feature Completeness Assessment

| Feature Area | BEL Problem Statement Requirement | Current Implementation Status | Evaluation |
| :--- | :--- | :--- | :--- |
| **Authentication** | Secure sign-in with MFA and role verification | Basic Amplify `signInWithRedirect` / Cognito Hosted UI | **Partial (40%).** Login works, but token storage and automatic refresh handling are rudimentary. |
| **User Management** | User directory, role assignment, status tracking | Create user form only (`POST /users`) | **Incomplete (25%).** Can submit new user form, but cannot list users, view user profiles, deactivate accounts, or inspect assigned roles. |
| **Access Control (ABAC/RBAC)** | Dynamic clearance checks (Admin, Manager, Auditor, User) | Hardcoded `<select>` dropdown with 4 roles | **Cosmetic (15%).** The frontend does not adapt its view based on the logged-in user's role. An Auditor sees the same empty screen as an Admin. |
| **Digital Asset Management** | Register, categorize, assign, transfer, and decommission defense digital assets | Placeholder text only (`<h3>Digital Assets</h3>`) | **Missing (0%).** No asset registration form, no asset inventory list, no custody transfer workflow, no QR/barcode generation. |
| **Blockchain / Provenance** | Immutable proof of authenticity, hash anchoring, tamper verification | Placeholder text only (`<h3>Audit Trail</h3>`) | **Missing (0%).** No cryptographic hashing of asset contents, no on-chain/hash-chain verification UI. |
| **Audit Log Explorer** | Searchable, chronological, tamper-evident log of all system events | None | **Missing (0%).** No audit trail table, no filter by user/asset/action, no export. |
| **UI/UX Aesthetics** | Premium, high-trust defense portal UI | Raw unstyled HTML inputs with browser defaults | **Unacceptable (10%).** Lacks responsive layouts, modern design tokens, interactive feedback, and status indicators. |

---

## 4. GAP ANALYSIS AGAINST BEL PROBLEM STATEMENT (SIH26125)

The Bharat Electronics Limited (BEL) problem statement requires solving 3 interconnected challenges:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   BEL SIH26125 CORE PILLARS                            │
├────────────────────┬────────────────────┬──────────────────────────────┤
│ 1. IDENTITY &      │ 2. DYNAMIC ACCESS  │ 3. DIGITAL ASSET             │
│    AUTHENTICATION  │    CONTROL         │    MANAGEMENT & PROVENANCE   │
├────────────────────┼────────────────────┼──────────────────────────────┤
│ - Zero Trust       │ - Multi-level      │ - Asset registry & custody   │
│ - Decentralized ID │   security         │ - Chained cryptographic      │
│   (DID / VC)       │   clearance        │   hashes (SHA-256 Merkle)    │
│ - Cognito + MFA    │ - RBAC + ABAC      │ - Lifecycle state machine    │
│ - Non-repudiation  │ - Policy engine    │ - Tamper-evident audit trail │
└────────────────────┴────────────────────┴──────────────────────────────┘
```

### Gap 1: Digital Asset Lifecycle
- **Required:** Defence assets (technical schematics, firmware binaries, encryption keys, military hardware configs) must transition through controlled states: `DRAFT` → `REGISTERED` → `ASSIGNED` → `IN_TRANSIT` → `MAINTENANCE` → `DECOMMISSIONED`.
- **Current State:** Zero asset models or endpoints exist.

### Gap 2: Tamper-Evident Cryptographic Hash Chaining
- **Required:** Every audit log and asset transaction must be mathematically chained so that modifying a database row breaks the cryptographic chain (blockchain proof-of-authenticity).
- **Current State:** `SIH-AuditEvents` is completely unpopulated.

### Gap 3: Defense Security Clearances (ABAC)
- **Required:** An asset classified as `TOP_SECRET` must only be accessible to a user who possesses `clearanceLevel >= TOP_SECRET` AND belongs to the matching unit/division.
- **Current State:** Only simple role strings (`Admin`, `Manager`, `Auditor`, `User`) exist with no clearance attributes.

---

## 5. REMEDIATION STRATEGY & WORKFLOW DISCIPLINE

Per [WORKFLOW.md](file:///c:/Users/kunji/NODE/WORKFLOW.md) and [BACKEND_CODE_WRITING.md](file:///c:/Users/kunji/NODE/BACKEND_CODE_WRITING.md):

1. **Local Repository Source of Truth:**
   All backend code will be organized in a modular `c:\Users\kunji\NODE\backend\` directory with clean separation (handler, services, repositories, tests).
2. **Local Testing First:**
   Every new endpoint and domain logic service will be written and tested locally with automated Python unit tests before touching AWS.
3. **Minimal, Reversible AWS Deployments:**
   Deployments to Lambda and API Gateway will only update the zip package and add the missing routes, preserving the existing working infrastructure in `ap-south-1`.
4. **Hard $20 Budget Adherence:**
   Zero EC2 instances or continuous servers. Everything remains pure serverless (API Gateway v2 + Lambda + DynamoDB On-Demand + Cognito free tier), costing $0 when idle.
