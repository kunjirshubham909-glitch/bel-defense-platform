# BLUEPRINT.md: DEFENSE-GRADE IMPLEMENTATION BLUEPRINT (BEL SIH26125)

**Problem Statement ID:** SIH26125 (Smart India Hackathon 2026 — Round 2)  
**Organization:** Bharat Electronics Limited (BEL), Ministry of Defence  
**Theme:** Blockchain & Cybersecurity  
**Platform Title:** Tactical Defense Digital Asset Provenance & Zero-Trust Access Platform  
**Target Completion:** Single-Day High-Velocity Hackathon Sprint (6–8 Hours Execution)  
**Architecture:** Hexagonal Architecture (Ports & Adapters) + PASETO v4 + Argon2id + Lightweight Merkle Verification (LMV)  
**Runtime:** AWS Serverless (`ap-south-1`) with $20 Hard Budget Ceiling & Hybrid Kong Gateway Readiness  

---

## 1. STRATEGIC ARCHITECTURE & AUDIT FLAW RESOLUTION MATRIX

This blueprint systematically eliminates all **28 Critical, High, and Medium Flaws** identified in the Defense Platform Audit Report ([FRONTEND_BACKEND_AUDIT.md](file:///c:/Users/kunji/NODE/FRONTEND_BACKEND_AUDIT.md)) to elevate the system from a fragile 12% prototype into an enterprise, competition-winning defense product.

### Flaw-to-Phase Traceability Matrix

| Flaw ID | Component | Severity | Root Vulnerability | Blueprint Phase Resolution |
|:--------|:----------|:---------|:-------------------|:---------------------------|
| **FLA-001** | Frontend | CRITICAL | Hardcoded API Gateway endpoint URL | **Phase 4**: Injected via `import.meta.env.VITE_API_URL` with `.env` and fallback configuration |
| **FLA-002** | Frontend | CRITICAL | 300-line monolithic `App.jsx` component | **Phase 4**: Decomposed into modular components (`Navbar`, `AdminView`, `ManagerView`, `AuditorView`, `CustodianView`, `LMVVerifierWidget`, `api.js`) |
| **FLA-003** | Frontend | HIGH | Bearer token logged in console; unsafe handling | **Phase 4**: Centralized in `api.js`, sanitized log output, zero token leakage |
| **FLA-004** | Frontend | HIGH | Zero role-based UI rendering | **Phase 4**: Dynamic view routing based on user clearance level and role matrix |
| **FLA-005** | Frontend | HIGH | Dead static `<h3>` placeholders for Assets & Audit | **Phase 4**: Interactive Asset Inventory table, Register Asset modal, Custody Transfer wizard, and Chronological Audit Explorer |
| **FLA-006** | Frontend | MEDIUM | Hardcoded localhost OAuth redirects | **Phase 4**: Configurable redirect URI mapping via Vite env |
| **FLA-007** | Frontend | MEDIUM | Missing frontend build verification & quality scripts | **Phase 4**: Quality validation gates with `npm run build` and lint verification |
| **FLA-008** | Backend | CRITICAL | DynamoDB `table.scan()` on user creation ($O(N)$ cost/latency) | **Phase 3**: Replaced with GSI `query()` on `cognitoUsername` and `ConditionExpression` |
| **FLA-009** | Backend | CRITICAL | Single-route backend bottleneck (only `POST /users`) | **Phase 3**: Clean multi-route dispatcher supporting 7 endpoints (`/users`, `/assets`, `/transfer`, `/audit`, `/verify`) |
| **FLA-010** | Backend | CRITICAL | Zero audit logging to `SIH-AuditEvents` on state change | **Phase 1, 2, 3**: Automated hash-chained audit logging triggered on every state mutation |
| **FLA-011** | Backend | HIGH | Missing exception handling (`ClientError`, duplicate keys) | **Phase 3**: Comprehensive `try/except` mapping to standard HTTP status codes (`400`, `401`, `403`, `404`, `409`, `500`) |
| **FLA-012** | Backend | HIGH | No server-side input validation | **Phase 1, 3**: Strict validation boundary enforcing clearance levels, email format, and enum whitelists |
| **FLA-013** | Backend | HIGH | Monolithic Lambda violating Hexagonal Architecture | **Phase 1**: Clean separation into `domain/`, `ports/`, `services/`, and `adapters/` |
| **FLA-014** | Backend | HIGH | JWT authorizer configured on single route only | **Phase 3, 5**: Uniform authorization layer across all protected API routes |
| **FLA-015** | Database | CRITICAL | Missing defense clearance attributes in `SIH-Users` | **Phase 1, 3**: Full schema support for `clearanceLevel` (0-4), `unit`, and `compartments` |
| **FLA-016** | Database | HIGH | Role strings insufficient for defense ABAC | **Phase 1**: Policy engine evaluating `clearanceLevel >= asset.clearanceLevel` and unit compartmentalization |
| **FLA-017** | Database | CRITICAL | `SIH-Assets` table empty; schema lacks fingerprint & states | **Phase 1, 3**: Complete `DefenseAsset` domain model with SHA-256 fingerprint, state machine, and custody chain |
| **FLA-018** | Database | CRITICAL | `SIH-AuditEvents` lacks `prevHash` (zero tamper-evidence) | **Phase 2**: Cryptographic SHA-256 block-hash chaining ($H_n = \text{SHA256}(H_{n-1} + \dots)$) |
| **FLA-019** | Database | HIGH | Missing LMV Merkle root anchor | **Phase 2**: Binary Merkle Tree generation and light-client cryptographic inclusion proof engine |
| **FLA-020** | Compliance | CRITICAL | Simple role checks fail BEL defense ABAC requirements | **Phase 1**: Real-time ABAC clearance evaluator with multi-level hierarchical enforcement |
| **FLA-021** | Compliance | CRITICAL | No PASETO v4 or Argon2id implementation | **Phase 2**: PASETO v4.local authenticated encryption tokens and Argon2id key derivation adapters |
| **FLA-022** | Compliance | CRITICAL | No live tamper-verification engine | **Phase 2, 4**: Live LMV Verifier widget displaying green `100% VERIFIED` or red alert on simulated tampering |
| **FLA-023** | Compliance | HIGH | Custody transfers vulnerable to bearer token hijacking | **Phase 2, 3**: Tamper-proof PASETO transfer tickets binding asset, sender, recipient, and expiration |
| **FLA-024** | Budget | HIGH | Table scans risking the $20 AWS account limit | **Phase 3**: Strict $O(1)$ key lookups and GSI queries; zero full-table scans |
| **FLA-025** | Budget | MEDIUM | Infinite CloudWatch log retention risks storage cost | **Phase 5**: CloudWatch retention explicitly bounded to 7 days |
| **FLA-026** | Budget | MEDIUM | No request/response payload limits | **Phase 3**: Strict 1MB JSON payload limit enforced at API Gateway/handler |
| **FLA-027** | Architecture | CRITICAL | No local backend code in repository (AWS drift) | **Phase 1**: Local `backend/` established as single source of truth |
| **FLA-028** | Architecture | HIGH | Zero automated unit tests in repository | **Phase 1, 2, 3**: Comprehensive automated test suites (`test_domain_core.py`, `test_cryptography.py`, `test_router.py`) |

---

## 2. 5-PHASE EXECUTION ROADMAP (6–8 HOUR SPRINT)

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                           SIH 2026 DEFENSE PLATFORM IMPLEMENTATION ROADMAP                      │
├───────────────┬──────────────┬──────────────────────────────────┬───────────────────────────────┤
│ PHASE         │ ESTIMATE     │ DELIVERABLES                     │ ACCEPTANCE GATE               │
├───────────────┼──────────────┼──────────────────────────────────┼───────────────────────────────┤
│ Phase 1       │ 1.5 - 2.0 h  │ Pure Hexagonal Domain Core,      │ 100% Local Unit Tests Pass    │
│               │              │ ABAC Policy Engine, State        │ (0 Failures, 0 Cloud Calls)   │
│               │              │ Machine, In-Memory Adapters      │                               │
├───────────────┼──────────────┼──────────────────────────────────┼───────────────────────────────┤
│ Phase 2       │ 1.0 - 1.5 h  │ Cryptographic Hash Chain, LMV    │ Mathematical Tamper Detection │
│               │              │ Merkle Engine, PASETO v4 Tokens, │ Test Pass (Altered 1-byte     │
│               │              │ Argon2id Derivation              │ triggers instant red alert)   │
├───────────────┼──────────────┼──────────────────────────────────┼───────────────────────────────┤
│ Phase 3       │ 1.0 - 1.5 h  │ DynamoDB Adapter (GSI queries),  │ Local HTTP Dispatcher Test    │
│               │              │ Multi-Route Lambda Router,       │ (All 7 endpoints pass with    │
│               │              │ Standardized JSON Envelopes      │ standardized JSON envelopes)  │
├───────────────┼──────────────┼──────────────────────────────────┼───────────────────────────────┤
│ Phase 4       │ 2.0 - 2.5 h  │ Tactical Command Center UI,      │ Vite React Build Passes       │
│               │              │ 4 Role Views (Admin, Manager,    │ (Clean bundle, 0 lint errors, │
│               │              │ Auditor, Custodian), LMV Widget  │ smooth interactive switching) │
├───────────────┼──────────────┼──────────────────────────────────┼───────────────────────────────┤
│ Phase 5       │ 1.0 h        │ AWS Lambda Deploy (ap-south-1),  │ Live Cloud End-to-End Demo    │
│               │              │ API Gateway Routes, Cognito Auth,│ Verified; $0 Cost Overage     │
│               │              │ End-to-End Browser Verification  │ ($20 Budget Intact)           │
└───────────────┴──────────────┴──────────────────────────────────┴───────────────────────────────┘
```

---

## PHASE 1: HEXAGONAL DOMAIN CORE & IN-MEMORY OFFLINE TESTING

### 1.1 Goal
Create the pure Python domain core inside `backend/` with **zero external cloud dependencies**. Enforce defense-grade domain invariants, the 5-tier clearance hierarchy, the armed forces branch compartmentalization, the asset state machine, and in-memory mock adapters for instantaneous local testing.

### 1.2 Domain Entities & Specifications (`backend/domain/entities.py`)
- **ClearanceLevel (IntEnum):**
  - `UNCLASSIFIED = 0` (Public / Base Level)
  - `RESTRICTED = 1` (Operational Support)
  - `CONFIDENTIAL = 2` (Command Level)
  - `SECRET = 3` (Field Officer / Tactical)
  - `TOP_SECRET = 4` (Strategic Command / BEL Labs)
- **MilitaryUnit (StrEnum):**
  - `ARMY = "Army"`
  - `NAVY = "Navy"`
  - `AIR_FORCE = "AirForce"`
  - `BEL_LABS = "BEL_Labs"`
- **AssetState (StrEnum):**
  - `DRAFT` $\to$ `REGISTERED` $\to$ `ASSIGNED` $\to$ `IN_TRANSIT` $\to$ `IN_INSPECTION` $\to$ `DECOMMISSIONED`
- **User Entity:**
  ```python
  @dataclass
  class User:
      userId: str
      name: str
      email: str
      role: str # "Admin", "Manager", "Auditor", "User"
      clearanceLevel: ClearanceLevel
      unit: MilitaryUnit
      compartments: list[str] # e.g. ["PROJECT_BRAHMOS", "DRONE_RADAR"]
      cognitoUsername: str
      status: str = "ACTIVE"
  ```
- **DefenseAsset Entity:**
  ```python
  @dataclass
  class DefenseAsset:
      assetId: str
      name: str
      assetType: str # "RADAR_FIRMWARE", "TACTICAL_DRONE", "CRYPTO_KEY", "SCHEMATIC"
      classification: ClearanceLevel
      unit: MilitaryUnit
      compartment: str
      custodianId: str
      state: AssetState
      contentHash: str # SHA-256 content digest
      custodyChain: list[dict] # [{ "holderId": str, "timestamp": str, "txType": str }]
      metadata: dict = field(default_factory=dict)
  ```
- **AuditRecord Entity:**
  ```python
  @dataclass
  class AuditRecord:
      eventId: str
      timestamp: str
      actorId: str
      actorRole: str
      action: str # "USER_CREATE", "ASSET_REGISTER", "CUSTODY_TRANSFER", "CLEARANCE_OVERRIDE"
      resourceType: str
      resourceId: str
      prevHash: str
      currentHash: str
      payloadHash: str
  ```

### 1.3 State Machine Engine (`backend/domain/state_machine.py`)
- Enforces valid state transitions:
  - `DRAFT` $\to$ `REGISTERED` (via asset registration with SHA-256 fingerprint)
  - `REGISTERED` $\to$ `ASSIGNED` (initial custodian allocation)
  - `ASSIGNED` $\to$ `IN_TRANSIT` (transfer initiated with transfer ticket)
  - `IN_TRANSIT` $\to$ `ASSIGNED` (custody accepted by recipient)
  - `ASSIGNED` $\to$ `IN_INSPECTION` (auditor custody audit)
  - `IN_INSPECTION` $\to$ `ASSIGNED` (passed inspection)
  - Any state $\to$ `DECOMMISSIONED` (Admin only; terminal state)
- Illegal transitions raise `InvalidStateTransitionError`.

### 1.4 ABAC Clearance Evaluator (`backend/services/user_service.py` & `asset_service.py`)
- **Access Rule:**
  $$\text{canAccess}(\text{user}, \text{asset}) \iff (\text{user.clearanceLevel} \ge \text{asset.classification}) \land (\text{user.unit} == \text{asset.unit} \lor \text{asset.compartment} \in \text{user.compartments} \lor \text{user.role} == \text{"Admin"})$$
- Returns detailed authorization decision: `{"allowed": bool, "reason": str}`.

### 1.5 Port Definitions (`backend/ports/`)
- `inbound.py`: `IUserService`, `IAssetService`, `IAuditService`, `IVerificationService`.
- `outbound.py`: `IUserRepository`, `IAssetRepository`, `IAuditLedger`, `ITokenService`, `IPasswordHasher`.

### 1.6 In-Memory Adapter (`backend/adapters/in_memory_repo.py`)
- Fully implements `IUserRepository`, `IAssetRepository`, and `IAuditLedger` using Python native dictionaries, allowing local tests to run in milliseconds.

### 1.7 Phase 1 Acceptance Gate
Run:
```bash
python -m unittest discover -s backend/tests -p "test_domain_core.py"
```
**Gate Requirement:** 100% test pass rate with zero mock failures.

---

## PHASE 2: CRYPTOGRAPHIC HASH CHAIN & LMV VERIFICATION ENGINE

### 2.1 Goal
Implement defense-grade cryptography matching BEL's **`SecureLedger`** architecture:
1. **SHA-256 Audit Block-Hash Chaining**: Every state mutation records an immutable chained block.
2. **Lightweight Merkle Verification (LMV)**: Light clients can verify proof of inclusion in $O(\log N)$ steps without downloading the full ledger.
3. **PASETO v4.local Tokens**: Authenticated encryption (`XChaCha20-Poly1305`) for transfer tickets, avoiding JWT vulnerabilities.
4. **Argon2id Key Derivation**: Defense passphrase protection.

### 2.2 Hash-Chaining Formula (`backend/domain/merkle_engine.py`)
Each audit event block is cryptographically bound to the previous block:
$$\text{payloadHash} = \text{SHA256}(\text{actorId} \parallel \text{action} \parallel \text{resourceId} \parallel \text{details\_json})$$
$$\text{currentHash} = \text{SHA256}(\text{prevHash} \parallel \text{timestamp} \parallel \text{payloadHash})$$
Genesis block uses $\text{prevHash} = \text{"0" \times 64}$.

### 2.3 Binary Merkle Tree Engine
- Takes an array of audit record `currentHash`es.
- Builds binary Merkle tree:
  $$\text{parent} = \text{SHA256}(\text{left} \parallel \text{right})$$
  (if odd number of nodes, duplicates last node).
- Computes 32-byte hexadecimal **Merkle Root**.
- Generates inclusion proof path for any given `eventId`:
  $$\text{proof} = [(\text{siblingHash}_1, \text{direction}_1), (\text{siblingHash}_2, \text{direction}_2), \dots]$$
- Light client verifies inclusion in $O(\log N)$ by computing hashes up to the root.

### 2.4 Tamper-Detection Engine (`backend/services/verification_service.py`)
- `verify_ledger()`: Re-computes hashes from Genesis to Head.
  - If all match: Returns `{"verified": True, "total_blocks": N, "merkle_root": str}`.
  - If any row's payload, timestamp, or `prevHash` has been modified: Returns `{"verified": False, "compromised_block": eventId, "expected_hash": str, "actual_hash": str}`.

### 2.5 PASETO v4 Transfer Tickets (`backend/adapters/paseto_adapter.py`)
- Emits secure transfer ticket for custody handoff:
  ```json
  {
    "v": "v4.local",
    "payload": {
      "ticketId": "TKT-829104",
      "assetId": "AST-1049",
      "fromCustodian": "USR-002",
      "toCustodian": "USR-004",
      "exp": 1727440000,
      "nonce": "a9b3c4d5e6f7"
    }
  }
  ```
- Recipient validates ticket integrity before custody is transferred in DynamoDB.

### 2.6 Phase 2 Acceptance Gate
Run:
```bash
python -m unittest discover -s backend/tests -p "test_cryptography.py"
```
**Gate Requirement:**
1. Valid ledger verifies to `True` with Merkle root generated.
2. Altered block (even 1 altered byte in payload) triggers `False` and pinpoints the corrupted `eventId`.

---

## PHASE 3: DYNAMODB ADAPTER & MULTI-ROUTE LAMBDA ROUTER

### 3.1 Goal
Connect the pure domain core to AWS serverless infrastructure using concrete adapters, eliminating DynamoDB table scans, handling race conditions, and dispatching all 7 API endpoints via a single resilient Lambda handler.

### 3.2 DynamoDB Access Patterns (`backend/adapters/dynamodb_repo.py`)

#### Table: `SIH-Users` (PK: `userId`)
- **Query Optimization (Fixing FLA-008 & FLA-024):**
  - Add GSI: `cognitoUsername-index` (PK: `cognitoUsername`).
  - Lookup by Cognito username uses `query(IndexName='cognitoUsername-index')` $\to O(1)$ RCU consumption.
  - User creation uses `PutItem` with `ConditionExpression: attribute_not_exists(userId)`.

#### Table: `SIH-Assets` (PK: `assetId`)
- **Race Condition Prevention:**
  - `PutItem` or `UpdateItem` with:
    `ConditionExpression: attribute_not_exists(assetId) OR #state = :expectedState`
  - Prevents double-transfer or unauthorized state mutation.

#### Table: `SIH-AuditEvents` (PK: `eventId`)
- **Chained Write:**
  - Retrieves latest `currentHash` (or Genesis if empty).
  - Calculates new block hash.
  - Atomic `PutItem` appending new chained record.

### 3.3 Multi-Route HTTP Dispatcher (`backend/lambda_function.py`)
Routes API Gateway v2 HTTP requests:

| Method & Route | Function & Port Call | Clearance / Auth Rule |
|:---------------|:---------------------|:----------------------|
| `POST /users` | `UserService.create_user()` | Admin role only |
| `GET /users` | `UserService.list_users()` | Admin or Manager role |
| `POST /assets` | `AssetService.register_asset()` | Manager or Admin role |
| `GET /assets` | `AssetService.list_assets()` | Filtered by caller's clearance (ABAC) |
| `GET /assets/{id}` | `AssetService.get_asset()` | Enforces `caller.clearance >= asset.classification` |
| `PUT /assets/{id}/transfer` | `AssetService.transfer_custody()` | Validates PASETO ticket + clearance |
| `GET /audit` | `AuditService.get_ledger()` | Auditor, Manager, or Admin |
| `POST /verify` | `VerificationService.verify_ledger()` | Public / All Roles (Auditor primary) |

### 3.4 Standardized Response Envelope
All routes strictly return:
```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": { ... }
}
```
Or on error:
```json
{
  "success": false,
  "message": "Security clearance level insufficient.",
  "error": {
    "code": "CLEARANCE_DENIED",
    "details": "Caller clearance (CONFIDENTIAL) cannot access TOP_SECRET asset."
  }
}
```

### 3.5 Phase 3 Acceptance Gate
Run:
```bash
python -m unittest discover -s backend/tests -p "test_router.py"
```
**Gate Requirement:** Local simulation of API Gateway v2 events for all 7 routes returns correct HTTP status codes (`200`, `201`, `400`, `403`, `404`, `409`).

---

## PHASE 4: HIGH-TRUST DEFENSE COMMAND CENTER (FRONTEND UI)

### 4.1 Goal
Deconstruct the monolithic `sih-frontend/src/App.jsx` into a modular, military-grade tactical operations dashboard. Render dedicated command views based on user role and clearance, and integrate the live LMV Merkle Verifier widget.

### 4.2 Modular Component Architecture (`sih-frontend/src/`)
```text
sih-frontend/src/
├── main.jsx                     # Vite entry point
├── App.jsx                      # Root controller & view switch
├── index.css                    # Tactical dark-mode theme & tokens
├── services/
│   └── api.js                   # Axios/fetch client with VITE_API_URL & Bearer auth
└── components/
    ├── Navbar.jsx               # Military branch badges, clearance pill, logout
    ├── AdminView.jsx            # Personnel directory, clearance assign, create user modal
    ├── ManagerView.jsx          # Asset inventory grid, register asset modal, custody transfer
    ├── AuditorView.jsx          # Chronological audit ledger, block inspector, search filters
    ├── CustodianView.jsx        # "My Assigned Assets", accept custody modal, asset viewer
    └── LMVVerifierWidget.jsx    # Interactive Merkle verification with animated tamper test
```

### 4.3 Visual Design System
- **Theme:** High-contrast Tactical Defense Dark Mode (`#0a0e17` background, `#121b2a` cards).
- **Accents:**
  - BEL Navy Blue: `#1e3a8a`
  - Radar Emerald (System Active / Verified): `#10b981`
  - Alert Crimson (Tamper Alert / Clearance Breach): `#ef4444`
  - Top Secret Gold: `#f59e0b`
- **Clearance Badges:**
  - `TOP_SECRET`: Purple gradient badge with lock icon.
  - `SECRET`: Red badge.
  - `CONFIDENTIAL`: Amber badge.
  - `RESTRICTED`: Blue badge.
  - `UNCLASSIFIED`: Slate badge.

### 4.4 Live LMV Verifier Widget Features
1. **"Verify Ledger Integrity" Button:** Calls `POST /verify`, displays computed Merkle Root, block height, and timestamp. Shows animated green pulse indicator: `LEDGER INTEGRITY: 100% VERIFIED`.
2. **"Simulate Tamper Attack" (Demo Mode):** Simulates modifying a byte in block #3. The widget runs local verification, turns red, emits alert sound/flash, and displays:
   `TAMPER DETECTED AT BLOCK EVT-003! HASH MISMATCH. MERKLE PROOF REJECTED.`

### 4.5 Phase 4 Acceptance Gate
Run:
```bash
npm --prefix sih-frontend run build
```
**Gate Requirement:** Clean Vite production build with 0 TypeScript/JSX errors.

---

## PHASE 5: AWS CLOUD DEPLOYMENT & LIVE END-TO-END VERIFICATION

### 5.1 Goal
Deploy the validated local backend to AWS Lambda (`SIH-Backend`) in `ap-south-1`, register all missing API Gateway routes with the Cognito Authorizer, and perform live end-to-end testing from the browser under the strict $20 account ceiling.

### 5.2 Deployment Steps
1. **Package Backend:**
   Compress `backend/` into `lambda.zip`.
2. **Update Lambda Function:**
   ```bash
   aws lambda update-function-code \
     --function-name SIH-Backend \
     --zip-file fileb://lambda.zip \
     --region ap-south-1
   ```
3. **Configure API Gateway Routes (`SIH-API` / `hpm91xi4me`):**
   - Create route `GET /users` with authorizer `bv35ne`.
   - Create route `POST /assets` with authorizer `bv35ne`.
   - Create route `GET /assets` with authorizer `bv35ne`.
   - Create route `GET /assets/{id}` with authorizer `bv35ne`.
   - Create route `PUT /assets/{id}/transfer` with authorizer `bv35ne`.
   - Create route `GET /audit` with authorizer `bv35ne`.
   - Create route `POST /verify` (public or authorized).
4. **Set CloudWatch Log Retention:**
   ```bash
   aws logs put-retention-policy \
     --log-group-name /aws/lambda/SIH-Backend \
     --retention-in-days 7
   ```
5. **Update Frontend Environment:**
   Set `VITE_API_URL=https://hpm91xi4me.execute-api.ap-south-1.amazonaws.com` in `sih-frontend/.env`.

### 5.3 Phase 5 Acceptance Gate
Execute the live end-to-end browser demo on `http://localhost:5173`. Confirm 0 AWS billing breaches.

---

## 3. PROMPTS FOR NVIDIA NEMOTRON IN CLINE (READY TO COPY & EXECUTE)

Copy and execute these prompts one by one in Cline (in **Act mode**) to build each phase systematically:

### 📋 NEMOTRON PROMPT: PHASE 1 (Execute First)
```text
Execute Phase 1 of BLUEPRINT.md:
1. Create the backend/ directory structure:
   - backend/domain/entities.py
   - backend/domain/state_machine.py
   - backend/ports/inbound.py
   - backend/ports/outbound.py
   - backend/adapters/in_memory_repo.py
   - backend/services/user_service.py
   - backend/services/asset_service.py
   - backend/tests/test_domain_core.py
2. In backend/domain/entities.py, implement User, DefenseAsset, AuditRecord, ClearanceLevel (0-4), MilitaryUnit, and AssetState per BLUEPRINT.md §1.2.
3. In backend/domain/state_machine.py, implement the legal state transitions and InvalidStateTransitionError per §1.3.
4. In backend/ports/, define the abstract interfaces for inbound use cases and outbound repositories.
5. In backend/adapters/in_memory_repo.py, implement dictionary-backed repositories for users, assets, and audit records.
6. In backend/services/, implement UserService and AssetService with the ABAC clearance evaluator rule:
   canAccess = (user.clearanceLevel >= asset.classification) and (user.unit == asset.unit or asset.compartment in user.compartments or user.role == "Admin").
7. In backend/tests/test_domain_core.py, write comprehensive unit tests verifying:
   - User creation and validation.
   - Asset state machine transitions (legal vs illegal).
   - ABAC clearance allowance and denial (CONFIDENTIAL user denied TOP_SECRET asset).
8. Run the tests using:
   python -m unittest discover -s backend/tests -p "test_domain_core.py"
Verify that all unit tests pass with 100% success. Do not touch AWS or the frontend yet.
```

### 📋 NEMOTRON PROMPT: PHASE 2 (Execute Second)
```text
Execute Phase 2 of BLUEPRINT.md:
1. Create backend/domain/merkle_engine.py implementing:
   - SHA-256 block-hash chaining: eventHash = SHA256(prevHash + timestamp + payloadHash).
   - Binary Merkle Tree generator calculating the 32-byte hexadecimal Merkle root.
   - Light-client Merkle inclusion proof generator and proof verifier in O(log N).
2. Create backend/services/verification_service.py implementing verify_ledger(events):
   - Traverses blocks from Genesis (prevHash = "0"*64) to head.
   - Detects if any row's payload, timestamp, or prevHash was tampered with, returning the exact corrupted eventId.
3. Create backend/adapters/paseto_adapter.py implementing:
   - PASETO v4.local custody transfer ticket issuer with XChaCha20-Poly1305 encryption.
   - Ticket verification method checking expiry and recipient.
4. Create backend/adapters/argon2_adapter.py implementing Argon2id key derivation for defense credentials.
5. Create backend/tests/test_cryptography.py verifying:
   - Clean audit chain generates valid Merkle root and returns verified = True.
   - Modifying a single character in an audit block causes verify_ledger() to immediately fail and pinpoint the compromised block.
   - PASETO transfer ticket signing and verification.
6. Run the tests:
   python -m unittest discover -s backend/tests -p "test_cryptography.py"
Ensure all tests pass with 0 failures before stopping.
```

### 📋 NEMOTRON PROMPT: PHASE 3 (Execute Third)
```text
Execute Phase 3 of BLUEPRINT.md:
1. Create backend/adapters/dynamodb_repo.py implementing concrete DynamoDB access for:
   - SIH-Users: Use query() on GSI cognitoUsername-index to prevent table scans (resolving FLA-008 & FLA-024). Use ConditionExpression: attribute_not_exists(userId) on writes.
   - SIH-Assets: PutItem and UpdateItem with ConditionExpression for state-machine concurrency.
   - SIH-AuditEvents: Atomic append of hash-chained blocks with prevHash linkage.
2. Create backend/lambda_function.py implementing the API Gateway v2 HTTP router:
   - Route POST /users, GET /users
   - Route POST /assets, GET /assets, GET /assets/{id}, PUT /assets/{id}/transfer
   - Route GET /audit, POST /verify
   - Extract caller claims safely from requestContext.authorizer.jwt.claims.
   - Ensure all responses use the standardized envelope:
     {"success": bool, "message": str, "data": ...} or {"success": false, "message": str, "error": {"code": str, "message": str}}.
   - Handle exceptions cleanly (ConditionalCheckFailedException -> 409, ResourceNotFoundException -> 404, etc.).
3. Create backend/tests/test_router.py simulating API Gateway v2 events locally for all 7 routes.
4. Run the tests:
   python -m unittest discover -s backend/tests -p "test_router.py"
Ensure all simulated routes pass with expected HTTP status codes.
```

### 📋 NEMOTRON PROMPT: PHASE 4 (Execute Fourth)
```text
Execute Phase 4 of BLUEPRINT.md:
1. Refactor sih-frontend/src/ from a monolithic App.jsx into modular tactical components:
   - src/services/api.js: Centralized Axios/fetch client using import.meta.env.VITE_API_URL and attaching Cognito Bearer tokens safely.
   - src/components/Navbar.jsx: BEL defense branding, user name, military branch badge (Army, Navy, AirForce, BEL_Labs), clearance pill (TOP_SECRET, SECRET, etc.), and logout.
   - src/components/AdminView.jsx: Personnel directory, clearance assignment, add user modal.
   - src/components/ManagerView.jsx: Defense asset inventory grid, register asset modal (with SHA-256 content hashing), and initiate custody transfer modal.
   - src/components/AuditorView.jsx: Chronological audit trail table, block hash inspector, event filtering.
   - src/components/CustodianView.jsx: "My Assigned Assets", accept pending transfer with PASETO ticket validation.
   - src/components/LMVVerifierWidget.jsx: Interactive Merkle proof verifier with green "VERIFIED" pulse and "Simulate Tamper Attack" demo button showing instant red alert.
   - src/App.jsx: Clean router displaying appropriate command view based on authenticated user's role and clearance.
2. Apply high-contrast tactical defense styling in src/index.css (dark navy #0a0e17, emerald badges, radar grid accents).
3. Ensure sih-frontend/.env contains VITE_API_URL configuration.
4. Test the frontend build:
   npm --prefix sih-frontend run build
Verify that the build completes with 0 errors.
```

### 📋 NEMOTRON PROMPT: PHASE 5 (Execute Fifth)
```text
Execute Phase 5 of BLUEPRINT.md:
1. Package the backend/ directory into lambda.zip.
2. Deploy the code to AWS Lambda function SIH-Backend in ap-south-1 using the AWS CLI or AWS MCP tool:
   aws lambda update-function-code --function-name SIH-Backend --zip-file fileb://lambda.zip --region ap-south-1
3. Configure API Gateway SIH-API (hpm91xi4me):
   - Add routes: GET /users, POST /assets, GET /assets, GET /assets/{id}, PUT /assets/{id}/transfer, GET /audit, POST /verify.
   - Attach SIH-Cognito-Authorizer (bv35ne) to protected endpoints.
4. Set CloudWatch log retention for /aws/lambda/SIH-Backend to 7 days.
5. Launch the local frontend development server (npm --prefix sih-frontend run dev).
6. Verify the live end-to-end integration:
   - Admin login & clearance inspection.
   - Register a TOP_SECRET asset.
   - Verify audit block hash chain creation in SIH-AuditEvents.
   - Run live LMV verification widget.
7. Confirm that AWS spending remains within the strict $20 account budget ceiling.
```

---

## 4. SIH ROUND 2 WINNING DEMO SCRIPT FOR JUDGES

Execute this exact 4-step sequence during the live presentation to amaze the BEL and SIH evaluation panel:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              SIH ROUND 2 LIVE DEMO SCRIPT                              │
├───────┬──────────────────────────┬─────────────────────────────────────────────────────┤
│ STEP  │ ACTION                   │ WHAT THE JUDGES SEE & WHY IT WINS                   │
├───────┼──────────────────────────┼─────────────────────────────────────────────────────┤
│ 1     │ Login as Platform Admin  │ - Top navigation shows BEL Defense crest & badge.   │
│       │ (Col. Rajesh / BEL Labs) │ - Clearance Pill displays TOP_SECRET (Gold).        │
│       │                          │ - Admin Directory reveals all defense personnel     │
│       │                          │   across Army, Navy, Air Force, and BEL Labs.       │
├───────┼──────────────────────────┼─────────────────────────────────────────────────────┤
│ 2     │ Register Defense Asset   │ - Manager registers "BrahMos-II Guidance Firmware". │
│       │ & Initiate PASETO Ticket │ - System computes SHA-256 fingerprint on upload.    │
│       │                          │ - Assigns classification: TOP_SECRET (Army).        │
│       │                          │ - Issues encrypted PASETO v4 custody transfer ticket│
│       │                          │   to Major Vikram (Army Strategic Command).         │
├───────┼──────────────────────────┼─────────────────────────────────────────────────────┤
│ 3     │ Demonstrate ABAC Defense │ - Switch login context to Warrant Officer Sharma    │
│       │ Clearance Violation      │   (Clearance: CONFIDENTIAL).                        │
│       │                          │ - Attempt to open BrahMos-II schematic.             │
│       │                          │ - Screen flashes Crimson Shield:                    │
│       │                          │   "403 SECURITY CLEARANCE DENIED: Required          │
│       │                          │   TOP_SECRET, Current CONFIDENTIAL. Access Logged." │
├───────┼──────────────────────────┼─────────────────────────────────────────────────────┤
│ 4     │ Live LMV Blockchain      │ - Auditor opens LMV Verifier Widget.                │
│       │ Tamper-Evidence Test     │ - Clicks "Verify Ledger Integrity" -> Green pulse:  │
│       │ (The Winning Move)       │   "LEDGER INTEGRITY 100% VERIFIED (Merkle Root OK)".│
│       │                          │ - Auditor clicks "Simulate Attack" -> Widget flips  │
│       │                          │   to Red Alert: "TAMPER DETECTED AT BLOCK EVT-003!   │
│       │                          │   HASH MISMATCH PINPOINTED IN O(log N) TIME."       │
└───────┴──────────────────────────┴─────────────────────────────────────────────────────┘
```
