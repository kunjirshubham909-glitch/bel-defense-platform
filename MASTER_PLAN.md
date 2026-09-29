# MASTER PLAN: BEL SECURE PLATFORM FOR IDENTITY, ACCESS CONTROL & DIGITAL ASSET MANAGEMENT

**Problem Statement ID:** SIH26125 (Smart India Hackathon 2026)  
**Organization:** Bharat Electronics Limited (BEL), Ministry of Defence  
**Theme:** Blockchain & Cybersecurity  
**Category:** Software  
**Document Version:** 2.0.0 (Hexagonal Architecture & Defense Cryptography Edition)  
**Target Completion:** Hackathon-Winning Enterprise Prototype (1-Day Execution Plan)  

---

## 1. PROJECT VISION & OBJECTIVES

Bharat Electronics Limited (BEL) requires a tamper-proof, defense-grade platform that eliminates the single points of failure, insider threats, and vulnerability to cyberattacks inherent in traditional centralized identity and asset management systems.

This project delivers a **hybrid decentralized architecture** inspired by BEL's official **`SecureLedger`** and **`SecureDoc`** platforms, combining:
1. **Hexagonal Architecture (Ports & Adapters):** Complete isolation of defense business logic from external frameworks, cloud services, and databases, enabling 100% offline local testability and seamless cloud deployment.
2. **Advanced Cryptography (PASETO v4 + Argon2id):** Defense-grade, modern tokenization eliminating JWT algorithm confusion attacks, paired with Argon2id memory-hard key derivation.
3. **Zero-Trust Identity & ABAC Clearance Matrix:** Multi-level military security clearances (`TOP_SECRET`, `SECRET`, `CONFIDENTIAL`, `RESTRICTED`, `UNCLASSIFIED`) and armed forces unit partitioning (Army / Navy / Air Force / BEL Labs).
4. **Lightweight Merkle Verification (LMV):** Cryptographic hash-chaining and Merkle root anchoring in DynamoDB (`SIH-AuditEvents`), allowing light clients and tactical edge devices to verify audit integrity without downloading the full ledger.
5. **Zero-Cost Serverless Resilience:** Built on AWS serverless technologies (`ap-south-1`) maintaining high availability with $0 idle cost to strictly obey the account's $20 budget limit, with hybrid support for on-premise **Kong Gateway**.

---

## 2. HEXAGONAL ARCHITECTURE (PORTS & ADAPTERS)

To ensure high maintainability, bulletproof security, and local-first development without vendor lock-in, the backend is strictly modeled around **Hexagonal Architecture**:

```
                  ┌─────────────────────────────────────────────────────────┐
                  │                 INBOUND DRIVING PORTS                   │
                  │   - IUserService (User management, clearance, RBAC)     │
                  │   - IAssetService (Lifecycle, registration, transfer)   │
                  │   - IAuditService (Chained audit logging & compliance)  │
                  │   - IVerificationService (LMV Merkle proof verifier)    │
                  └────────────────────────────┬────────────────────────────┘
                                               │
                                               ▼
┌───────────────────────┐         ┌─────────────────────────┐         ┌────────────────────────┐
│   INBOUND ADAPTERS    │         │      HEXAGON CORE       │         │    OUTBOUND ADAPTERS   │
│                       │         │     (DOMAIN LOGIC)      │         │                        │
│ 1. AWS Lambda Adapter ├────────►│ - Defense Asset Entity  │├───────►│ 1. DynamoDB Adapter    │
│    (API Gateway v2)   │         │ - Security Clearance    ││        │    (SIH-Users, Assets, │
│                       │         │   Evaluator (ABAC)      ││        │     AuditEvents)       │
│ 2. Kong Gateway /     │         │ - State Machine Engine  ││        │                        │
│    REST Controller    ├────────►│ - Hash Chain & LMV Tree │├───────►│ 2. PASETO / JWT        │
│                       │         │ - Audit Record Entity   ││        │    Token Adapter       │
│ 3. Local CLI / Test   │         │                         ││        │                        │
│    Runner Adapter     ├────────►│                         │├───────►│ 3. Argon2id Hasher     │
│    (Pytest / Script)  │         │                         ││        │    Adapter             │
│                       │         │                         ││        │                        │
│                       │         │                         │├───────►│ 4. In-Memory Mock      │
│                       │         │                         ││        │    Adapter (Local Test)│
└───────────────────────┘         └─────────────────────────┘         └────────────────────────┘
                                               ▲
                                               │
                  ┌────────────────────────────┴────────────────────────────┐
                  │                 OUTBOUND DRIVEN PORTS                   │
                  │   - IUserRepository (Persist & retrieve users/roles)    │
                  │   - IAssetRepository (Persist & query defense assets)   │
                  │   - IAuditLedger (Append-only hash-chained storage)     │
                  │   - ITokenService (Sign & verify PASETO / JWT tokens)   │
                  │   - IPasswordHasher (Argon2id key derivation)           │
                  └─────────────────────────────────────────────────────────┘
```

### Directory Structure of `backend/`:
```text
backend/
├── domain/                    # Pure Domain (Zero External Dependencies)
│   ├── entities.py            # User, Asset, AuditRecord, ClearanceLevel
│   ├── state_machine.py       # Defense asset lifecycle states & transitions
│   └── crypto_engine.py       # SHA-256 fingerprinting & Merkle calculations
├── ports/                     # Interface Contracts (Python Abstract Base Classes)
│   ├── inbound.py             # Driving interfaces (Use Cases)
│   └── outbound.py            # Driven interfaces (Repositories, Token, Hash)
├── services/                  # Application Services (Implements Inbound Ports)
│   ├── user_service.py        # User & clearance logic
│   ├── asset_service.py       # Asset registration & custody transfer logic
│   ├── audit_service.py       # Chained ledger creation & event queries
│   └── verification_service.py# LMV Merkle proof verification logic
├── adapters/                  # Concrete Implementations (Implements Outbound Ports)
│   ├── dynamodb_repository.py # AWS DynamoDB implementation
│   ├── in_memory_repository.py# Zero-dependency mock for instant local tests
│   ├── paseto_adapter.py      # PASETO v4 + JWT fallback token adapter
│   └── argon2_adapter.py      # Argon2id password & key derivation adapter
├── lambda_function.py         # Inbound Adapter: AWS Lambda & API Gateway Router
└── tests/                     # Automated Unit & Negative Test Suite
    ├── test_domain.py         # Tests state machine & clearance logic
    ├── test_crypto.py         # Tests LMV Merkle proofs & hash-chain integrity
    ├── test_services.py       # Tests business logic with in-memory adapters
    └── test_router.py         # Tests HTTP status codes (200, 400, 401, 403, 409)
```

---

## 3. ADVANCED DEFENSE CRYPTOGRAPHY & SECURITY

### 3.1 PASETO (v4) vs. JWT
Traditional JWT (JSON Web Tokens) suffer from critical vulnerabilities highlighted in defense audits:
- **Algorithm Confusion Attacks:** Attackers can alter the token header (`alg: "none"` or swapping RS256 for HS256) to bypass verification.
- **Header Malleability:** Unauthenticated headers permit tampering.
- **Unencrypted Payloads:** Base64-encoded JWTs leak sensitive military clearance or role claims over the wire.

**The Solution: PASETO v4 (Platform-Agnostic Security Tokens)**
- **No Algorithm Negotiation:** The token format dictates the cipher suite (`v4.local` uses `XChaCha20-Poly1305`, `v4.public` uses `Ed25519`).
- **Encrypted Local Tokens:** `v4.local` provides authenticated symmetric encryption. Claims cannot be inspected even if intercepted.
- **Dual Support in Our Hexagonal Design:**
  - For standard web login: AWS Cognito JWT authorizer remains the public edge boundary.
  - For defense asset custody tickets & transfer authorizations: The backend generates and validates tamper-proof **PASETO v4** tokens.

### 3.2 Argon2id Key Derivation
- Winner of the Password Hashing Competition (PHC).
- Memory-hard algorithm providing optimal resistance against GPU, FPGA, and custom ASIC cracking hardware.
- Used in our `Argon2Adapter` for credential verification and deriving local encryption keys from defense passphrases.

### 3.3 LMV (Lightweight Merkle Verification) Engine
To provide blockchain-grade non-repudiation without heavy infrastructure:
1. **Hash-Chained Audit Ledger (`SIH-AuditEvents`):**
   $$\text{eventHash}_n = \text{SHA256}(\text{prevHash}_{n-1} + \text{timestamp} + \text{actorId} + \text{action} + \text{resourceId} + \text{payloadHash})$$
2. **Merkle Root Anchoring:**
   Audit blocks and asset states are bundled into Merkle trees. Light clients (e.g. frontline military tablets or auditor laptops) need only the 32-byte Merkle Root to verify cryptographic inclusion proofs (LMV) in logarithmic time $O(\log N)$.
3. **Instant Tamper Detection:**
   If an adversary modifies any row directly in DynamoDB, the LMV verifier detects the broken hash link immediately and identifies the exact compromised block.

---

## 4. API GATEWAY & KONG STRATEGY

| Deployment Scenario | Gateway Solution | Capabilities |
| :--- | :--- | :--- |
| **AWS Cloud (Current)** | **Amazon API Gateway v2 (HTTP API)** | Pure serverless, $0 idle cost, built-in Cognito JWT authorizer, CORS handling for local dev. |
| **On-Premise Defense (BEL)** | **Kong Gateway (Open-Source / Enterprise)** | Cloud-native, high-throughput reverse proxy deployed at military base data centers. Supports Kong PASETO plugin, mutual TLS (mTLS), and strict zero-trust network boundaries. |

---

## 5. SECURITY CLEARANCE & ABAC ACCESS MATRIX

Aligned with Bharat Electronics Limited's defense operational structure:

| Security Clearance | Description | Military Division / Unit | Permitted Asset Classifications |
| :--- | :--- | :--- | :--- |
| **Level 4: TOP_SECRET** | Highest strategic defense assets | Strategic Forces Command, BEL Labs R&D | Top Secret, Secret, Confidential, Restricted, Unclassified |
| **Level 3: SECRET** | Tactical equipment & communications | Indian Army, Indian Navy, Indian Air Force | Secret, Confidential, Restricted, Unclassified |
| **Level 2: CONFIDENTIAL** | Technical manuals, maintenance logs | Defense Base Workshops, Depots | Confidential, Restricted, Unclassified |
| **Level 1: RESTRICTED** | Internal personnel equipment | All Military Units, PSUs | Restricted, Unclassified |
| **Level 0: UNCLASSIFIED** | Public & standard materials | General Personnel | Unclassified only |

### Dynamic ABAC Clearance Evaluation:
```python
def can_access_asset(user: User, asset: DefenseAsset, action: str) -> bool:
    # 1. Admin Override for System Audits
    if user.role == "Admin" and action in ["VIEW", "AUDIT"]:
        return True
    # 2. Clearance Level Gate
    if user.clearance_level < asset.classification_level:
        return False
    # 3. Unit / Division Compartmentalization
    if asset.unit != "ALL" and user.unit != asset.unit:
        return False
    # 4. Decommissioned Protection
    if asset.status == "DECOMMISSIONED" and action != "AUDIT_VIEW":
        return False
    return True
```

---

## 6. ASSET LIFECYCLE STATE MACHINE

Every defense asset transitions through deterministic, auditable states:

```
[DRAFT]
   │
   ▼ (Admin/Manager registers asset, hashes payload)
[REGISTERED]
   │
   ▼ (Assigned to Custodian with matching clearance)
[ASSIGNED]
   │
   ├──► (Custody Transfer initiated) ──► [IN_TRANSIT] ──► (Recipient Confirms) ──► [ASSIGNED]
   │
   ├──► (Maintenance & Calibration) ──► [IN_INSPECTION] ──► (Passes Audit) ──► [ASSIGNED]
   │
   ▼ (Decommissioning authorized by Admin + Auditor)
[DECOMMISSIONED] (Terminal immutable state)
```

---

## 7. 1-DAY SPRINT EXECUTION ROADMAP (TODAY)

```
┌────────────────────────────────────────────────────────────────────────┐
│                  TOTAL TIME: 6 - 8 HOURS SPRINT TODAY                  │
├─────────────────────────┬──────────────┬───────────────────────────────┤
│ Sprint Module           │ Duration     │ Deliverables                  │
├─────────────────────────┼──────────────┼───────────────────────────────┤
│ Block 1: Hexagonal Core │ 2.0 Hours    │ - domain/ (entities, crypto)  │
│    & In-Memory Testing  │              │ - ports/ (inbound, outbound)  │
│                         │              │ - services/ (user, asset, LMV)│
│                         │              │ - 100% passing local tests    │
├─────────────────────────┼──────────────┼───────────────────────────────┤
│ Block 2: Outbound       │ 1.5 Hours    │ - dynamodb_repository.py      │
│    Adapters & Crypto    │              │ - paseto_adapter.py (PASETO)  │
│                         │              │ - argon2_adapter.py (Argon2id)│
│                         │              │ - LMV Merkle engine           │
├─────────────────────────┼──────────────┼───────────────────────────────┤
│ Block 3: Defense Portal │ 2.5 Hours    │ - React 19 Defense UI overhaul│
│    (Frontend UI)        │              │ - 4 Role-based command views  │
│                         │              │ - Interactive LMV verifier    │
│                         │              │ - Dark defense design system  │
├─────────────────────────┼──────────────┼───────────────────────────────┤
│ Block 4: AWS Lambda     │ 1.0 Hour     │ - Package backend/ to zip     │
│    Deploy & API Routes  │              │ - Update SIH-Backend (Mumbai) │
│                         │              │ - Register API Gateway routes │
│                         │              │ - End-to-end cloud test       │
├─────────────────────────┼──────────────┼───────────────────────────────┤
│ Block 5: Live Pitch &   │ 0.5 Hours    │ - Seed BEL defense assets     │
│    Demo Script          │              │ - Rehearse live tamper demo   │
└─────────────────────────┴──────────────┴───────────────────────────────┘
```

---

## 8. HACKATHON-WINNING DEMO SCENARIO FOR BEL JUDGES

1. **Defense Command Center Login (45s):**
   Log in as `Platform Administrator`. Display military branch badges, security clearance indicator (`TOP_SECRET`), and active personnel directory.
2. **Asset Registration & LMV Cryptographic Fingerprint (45s):**
   Register a new defense asset: *Radar Signal Processor Firmware v4.2* (`TOP_SECRET`). Backend generates its SHA-256 fingerprint, creates an immutable chained block in `SIH-AuditEvents`, and issues a verifiable asset ticket.
3. **ABAC Security Clearance Violation Rejection (45s):**
   Switch context to a user with `CONFIDENTIAL` clearance attempting to view or transfer the `TOP_SECRET` asset. Backend instantly returns `403 Forbidden: Security Clearance Insufficient` and writes a `SECURITY_ALERT` entry into the ledger.
4. **Live Cryptographic Tamper-Evidence Test (60s):**
   Demonstrate the **LMV Verifier**. Show green status: `LEDGER INTEGRITY: 100% VERIFIED`. Simulate an attacker altering a record: the cryptographic hash verification fails instantly, displaying a red alert and pinpointing the exact compromised block.
