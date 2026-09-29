# BACKEND_FRONTEND_INTEGRATION.md: ZERO-TRUST DEFENSE INTEGRATION SPECIFICATION

**System:** BEL Tactical Defense Platform  
**Problem Statement:** SIH26125 (Smart India Hackathon 2026)  
**Organization:** Bharat Electronics Limited (BEL), Ministry of Defence  
**Security Standards:** OWASP API Security Top 10 (2023) | NIST SP 800-207 Zero Trust | DoD Zero Trust Architecture | Bell-LaPadula MLS  
**Binding Level:** MANDATORY GOVERNING DIRECTIVE FOR ALL FRONTEND & BACKEND IMPLEMENTATIONS  

## 1. THE ZERO-TRUST DEFENSE INTEGRATION MANIFESTO

> ### ⚠️ THE SOVEREIGN ARCHITECTURAL PRINCIPLE:
> **The Frontend is an untrusted, hostile presentation surface. The Backend is the sovereign cryptographic fortress.**
> 
> 1. Any code executing inside a user's browser, network tab, or DevTools can be inspected, hijacked, reversed, or manipulated by an adversary.
> 2. **Client-side checks are for User Experience (UX) ONLY. They have ZERO security value.**
> 3. The Backend is the **sole Policy Enforcement Point (PEP)** and **Policy Decision Point (PDP)**. It never trusts any claim, state, clearance, or role sent directly by the frontend without server-side cryptographic verification.
> 4. The Frontend can **NEVER directly access backend databases (DynamoDB), cloud IAM credentials, master encryption keys, or internal private microservices**. All communication must transit a strictly governed API Gateway.

---

## 2. OWASP API SECURITY TOP 10 (2023) THREAT MATRIX & DEFENSE MITIGATIONS

| OWASP Vulnerability | Tactical Defense Threat | Architecture Mitigation in This Platform |
|:--------------------|:------------------------|:-----------------------------------------|
| **API1:2023 Broken Object Level Authorization (BOLA / IDOR)** | An attacker with `CONFIDENTIAL` clearance accesses a `TOP_SECRET` radar schematic by guessing or fetching `GET /assets/AST-TOPSECRET-001`. | **Authoritative Server-Side ABAC**: Backend evaluates $Caller.Clearance \ge Asset.Classification$. Even if the frontend exposes an asset ID, the backend rejects unauthorized access with `403 CLEARANCE_DENIED` and logs a high-priority audit block. |
| **API2:2023 Broken Authentication** | Token forgery, replay attacks, or bearer token hijacking during tactical handoffs. | **Cognito JWT Validation + PASETO v4 Transfer Tickets**: API Gateway validates RS256 signatures with AWS Cognito. Asset transfers use tamper-proof, encrypted PASETO `v4.local` tokens with expiration and nonce binding. |
| **API3:2023 Broken Object Property Level Authorization (BOPLA)** | Mass-assignment attacks where a user injects `"role": "Admin"` or `"clearanceLevel": 4` in a JSON request body. | **Explicit Whitelist Schema Validation**: The backend ignores client-provided security attributes. Roles and clearances can only be modified by authenticated Administrators through dedicated endpoints. |
| **API4:2023 Unrestricted Resource Consumption** | Large payload Denial-of-Service (DoS) attacks attempting to exhaust Lambda memory and blow the $20 budget limit. | **Payload & Concurrency Bounding**: API Gateway enforces a strict 1MB JSON payload ceiling. Lambda timeout bounded to 10 seconds. DynamoDB uses $O(1)$ query lookups; table scans are prohibited. |
| **API5:2023 Broken Function Level Authorization (BFLA)** | A regular soldier or manager sends `POST /users` to create military accounts. | **Role-Enforced Inbound Ports**: Inbound use cases check `actor.role == UserRole.ADMIN` at the service boundary before executing logic. Unauthorized callers receive `403 FORBIDDEN`. |
| **API6:2023 Unrestricted Access to Sensitive Business Flows** | Bypassing asset verification or skipping state machine stages (e.g. jumping from `DRAFT` directly to `ASSIGNED` without registration or fingerprinting). | **Formal State Machine Engine**: The `StateMachine` strictly enforces atomic legal transitions. Illegal state jumps raise `InvalidStateTransitionError` returning `409 CONFLICT`. |
| **API7:2023 Server Side Request Forgery (SSRF)** | Injecting malicious external URLs into asset download or firmware fetch requests. | **No Outbound Network Fetching**: Backend Lambda operates in an isolated environment with zero outbound HTTP calls to unapproved external endpoints. |
| **API8:2023 Security Misconfiguration** | Leaking stack traces, verbose internal errors, DynamoDB table names, or wildcard CORS headers (`*`). | **Standardized JSON Envelope & Sanitized Errors**: Backend maps all internal exceptions (`ClientError`, `KeyError`) to sanitized HTTP codes and envelopes. CORS is strictly restricted to trusted origins. |
| **API9:2023 Improper Inventory Management** | Zombie or undocumented endpoints leaking legacy logic. | **Single Consolidated Router**: All 7 approved endpoints are documented in `docs/API_SPECIFICATION.md` and routed through a single verified dispatcher in `lambda_function.py`. |
| **API10:2023 Unsafe Consumption of APIs** | Trusting data from third-party services without validation. | **Strict Hexagonal Port Validation**: All data crossing the adapter boundary is validated by dataclass constructors and regex checks before reaching the domain. |

---

## 3. THE "IRON CURTAIN": WHAT BACKEND NEVER SENDS TO FRONTEND

To guarantee defense confidentiality, the backend enforces an **Iron Curtain** between internal system state and external client serialization:

```
┌────────────────────────────────────────────────────────────────────────┐
│                      THE DEFENSE IRON CURTAIN                          │
├──────────────────────────────────┬─────────────────────────────────────┤
│ ⛔ NEVER EXPOSED TO FRONTEND     │ ✅ SAFE DATA PERMITTED ON FRONTEND   │
├──────────────────────────────────┼─────────────────────────────────────┤
│ 1. PASETO Symmetric Master Keys  │ 1. Encrypted PASETO Ticket String   │
│ 2. Argon2id / Password Hashes    │ 2. Sanitized User Profile (No Hash) │
│ 3. AWS IAM Role ARNs or Secrets  │ 3. Military Branch & Clearance Pill │
│ 4. Internal Database Table Names │ 4. Filtered Defense Asset Metadata  │
│ 5. Full Raw Unredacted Top-Secret│ 5. Computed SHA-256 Fingerprint     │
│    Metadata to Unauthorized Users│ 6. Public Merkle Root & Proof Path  │
│ 6. Python Tracebacks/Stack Traces│ 7. Standardized Error Message & Code│
│ 7. Private Infrastructure IP/VPC │ 8. Chronological Audit Record List  │
└──────────────────────────────────┴─────────────────────────────────────┘
```

### Data Redaction Rules:
1. **Asset List Redaction (BOLA Prevention):**
   When `GET /assets` is called, the backend runs ABAC evaluation for each asset against the caller's clearance. If caller clearance is lower than the asset's classification, the asset is **completely excluded** from the response array.
2. **Asset Detail Redaction:**
   When `GET /assets/{id}` is called:
   - If clearance is insufficient: **HTTP 403 Forbidden** is returned. Zero metadata, zero fingerprints, zero descriptions are leaked.
3. **Error Redaction:**
   Never return `{"error": "boto3.exceptions.DynamoDbClientError: ResourceNotFoundException in table SIH-Assets..."}`.  
   Always return `{"success": false, "message": "Asset not found.", "error": {"code": "NOT_FOUND"}}`.

---

## 4. SECURE INTEGRATION TOPOLOGY & NETWORK BOUNDARY

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       HOSTILE BROWSER ENVIRONMENT                           │
│  [ React Frontend (sih-frontend) ]                                         │
│  - Presentation & Form State Only                                           │
│  - Stores Cognito ID/Access Token in Memory (never localStorage)            │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       │ HTTPS (TLS 1.3 Strict)
                                       │ Authorization: Bearer <Cognito_JWT>
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                 POLICY ENFORCEMENT POINT (PEP): API GATEWAY                 │
│  - Enforces AWS Cognito JWT Signature Validation (RS256)                   │
│  - Enforces 1MB Payload Size Ceiling & Rate Throttling                     │
│  - Validates CORS Headers (Restricted Origin, No Wildcards)                 │
│  - Injects Verified Caller Claims into Event Context                        │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       │ Verified Event + Claims Context
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                 POLICY DECISION POINT (PDP): BACKEND CORE                   │
│  [ Lambda Inbound Adapter (lambda_function.py) ]                            │
│  - Extracts caller identity: sub, username, role, clearance, unit          │
│                                      │                                      │
│                                      ▼                                      │
│  [ Application Services & Domain Core (Hexagonal Fortress) ]                │
│  - Evaluates ABAC Policy Matrix (Clearance + Unit + Compartments)           │
│  - Validates State Machine Transitions                                      │
│  - Computes Cryptographic Hash-Chain (SHA-256)                              │
│  - Emits Immutable Audit Blocks to SIH-AuditEvents                          │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│               INTERNAL STORAGE (ZERO DIRECT FRONTEND ACCESS)                │
│  - DynamoDB: SIH-Users, SIH-Assets, SIH-AuditEvents (Private Access Only)   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. STANDARD SECURE INTEGRATION PROTOCOL

### 5.1 Request Header Standard
Every API request originating from `sih-frontend` must pass through the centralized API client (`src/services/api.js`) with the following headers:

```http
GET /assets HTTP/1.1
Host: hpm91xi4me.execute-api.ap-south-1.amazonaws.com
Authorization: Bearer eyJraWQiOiJ... (AWS Cognito Access Token)
Content-Type: application/json
Accept: application/json
X-Client-Version: 2.0.0-defense
X-Request-ID: req-7b8f9e1a-4d2c
```

### 5.2 Response Envelope Contract
The frontend MUST always parse responses through this strict envelope:

#### Successful Transaction:
```json
{
  "success": true,
  "message": "Asset registered with cryptographic fingerprint.",
  "data": {
    "assetId": "AST-BEL-9041",
    "name": "BrahMos-II Tactical Guidance Firmware v4.2",
    "classification": "TOP_SECRET",
    "state": "REGISTERED",
    "contentHash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "custodianId": "USR-BEL-001"
  }
}
```

#### Denied / Error Transaction:
```json
{
  "success": false,
  "message": "Security clearance level insufficient to access this asset.",
  "error": {
    "code": "CLEARANCE_DENIED",
    "details": "Caller clearance (CONFIDENTIAL) cannot access TOP_SECRET asset."
  }
}
```

---

## 6. FRONTEND IMPLEMENTATION RULES (`sih-frontend/`)

1. **Centralized API Client Only:**
   - All network calls must pass through `sih-frontend/src/services/api.js`.
   - Never call `fetch()` or `axios()` directly inside React component files.
   - Inject `VITE_API_URL` dynamically from environment (`import.meta.env.VITE_API_URL`).
2. **Token Security:**
   - Retrieve access token at runtime via Amplify `fetchAuthSession()`.
   - NEVER persist raw tokens in `localStorage` or `sessionStorage` (vulnerable to XSS extraction).
   - NEVER log bearer tokens to `console.log()` or browser debuggers.
3. **Graceful Handling of Security Denials:**
   - When the backend returns `403 CLEARANCE_DENIED`, the frontend must trigger a tactical security banner:
     `"🛡️ ACCESS RESTRICTED: Security clearance level insufficient for this classified resource. Access attempt has been cryptographically logged."`
4. **Role-Based Views are Presentation Only:**
   - The frontend renders `<AdminView>`, `<ManagerView>`, `<AuditorView>`, or `<CustodianView>` based on user attributes for ease of use, but relies 100% on the backend to enforce operational permissions.

---

## 7. BACKEND IMPLEMENTATION RULES (`backend/`)

1. **Fail-Fast Boundary Validation:**
   - Every route in `lambda_function.py` must validate the incoming request body against expected schema before calling application services.
   - Reject malformed payloads immediately with `400 BAD_REQUEST`.
2. **Authoritative Identity Extraction:**
   - Do NOT trust client-supplied `"callerId"` or `"role"` in the JSON body.
   - Extract the caller's identity strictly from:
     ```python
     claims = event.get('requestContext', {}).get('authorizer', {}).get('jwt', {}).get('claims', {})
     caller_username = claims.get('username') or claims.get('cognito:username')
     caller_email = claims.get('email')
     ```
   - Query the verified user record from `SIH-Users` using the verified `caller_username`.
3. **Non-Bypassable ABAC Evaluation:**
   - In `AssetService`, every access to an asset must invoke `can_access(caller, asset)`.
   - If `can_access` returns `False`, the backend MUST:
     1. Record an audit block: `action="SECURITY_CLEARANCE_DENIED"`.
     2. Raise `PermissionError(reason)`.
4. **Non-Repudiation on State Mutations:**
   - Every successful state-changing endpoint (`POST /users`, `POST /assets`, `PUT /assets/{id}/transfer`, `PUT /assets/{id}/decommission`) MUST write an immutable chained audit block to `SIH-AuditEvents` in the same transaction.

---

## 8. BINDING FOR CLINE & NEMOTRON

When writing frontend components in Phase 4 or wiring backend adapters in Phase 3:
- Cline and NVIDIA Nemotron **MUST** adhere to the security boundaries, data redaction tables, and API contracts defined in this document.
- Never write frontend code that assumes direct database access.
- Never write backend code that blindly trusts client-provided identity parameters.
