# BACKEND_CODE_WRITING.md — BACKEND CODING STANDARDS & ARCHITECTURE

This document establishes the official engineering standards, security rules, and architectural patterns for writing backend code in this repository.

Every backend service, AWS Lambda function, API endpoint, and data access layer MUST strictly adhere to these guidelines.

---

## 1. CORE ARCHITECTURAL PRINCIPLES

### 1.1 Clean Separation of Concerns
Never write monolithic or "spaghetti" Lambda functions where routing, validation, business logic, and DynamoDB access are tangled in a single file. Backend code follows a 3-layer architecture:

```
┌────────────────────────────────────────────────────────┐
│ 1. ADAPTER / HANDLER LAYER (lambda_handler.py)         │
│    - Parses incoming API Gateway event                 │
│    - Extracts & verifies JWT auth claims               │
│    - Validates input schema & types                    │
│    - Invokes domain service                            │
│    - Formats standardized HTTP JSON response           │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ 2. DOMAIN / BUSINESS LOGIC LAYER (services/)           │
│    - Pure business logic & RBAC validation             │
│    - State machine transitions & asset workflows       │
│    - Calculates hashes & audit events                  │
│    - Completely decoupled from HTTP / API Gateway      │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ 3. DATA ACCESS / REPOSITORY LAYER (repositories/)      │
│    - DynamoDB queries, conditional writes, updates     │
│    - Cognito administrative operations                 │
│    - Parameterized expressions                         │
└────────────────────────────────────────────────────────┘
```

### 1.2 YAGNI & Minimal Diff Discipline
- Write only what the feature ticket requires. No speculative abstractions, generic ORM frameworks, or unrequested utility wrappers.
- Prefer Python's standard library (`json`, `hashlib`, `uuid`, `datetime`, `re`) before introducing external dependencies.
- Keep function cold starts fast (<200ms) by minimizing import overhead.

---

## 2. LAMBDA HANDLER STANDARDS

### 2.1 Global Initialization (Connection Reuse)
Initialize AWS SDK clients (`boto3.resource`, `boto3.client`) **outside** the `lambda_handler` function. This enables connection reuse across warm execution environments and prevents repeated TCP/TLS handshakes.

```python
# CORRECT: Initialized globally outside the handler
import json
import os
import boto3

dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION", "ap-south-1"))
USERS_TABLE = os.environ.get("USERS_TABLE", "SIH-Users")
table = dynamodb.Table(USERS_TABLE)

def lambda_handler(event, context):
    # Process request
    ...
```

### 2.2 Standardized JSON Response Envelope
Every API endpoint MUST return a consistent JSON response envelope. Never return raw Python dictionaries or strings.

```python
def make_response(status_code: int, message: str, data=None, error_code=None):
    """
    Standard HTTP response envelope for API Gateway v2.
    """
    body = {
        "success": 200 <= status_code < 300,
        "message": message
    }
    if data is not None:
        body["data"] = data
    if error_code is not None:
        body["error"] = {
            "code": error_code,
            "message": message
        }
        
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "http://localhost:5173",
            "Access-Control-Allow-Headers": "authorization,content-type",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS"
        },
        "body": json.dumps(body, default=str)
    }
```

### 2.3 HTTP Status Code Discipline
Use precise HTTP status codes:
- **`200 OK`**: Successful query or update.
- **`201 Created`**: New resource (user, asset, audit event) created.
- **`400 Bad Request`**: Missing field, invalid format, schema violation.
- **`401 Unauthorized`**: Missing, expired, or invalid JWT token.
- **`403 Forbidden`**: Valid token, but user lacks role/permission (RBAC failure).
- **`404 Not Found`**: Target resource (userId, assetId) does not exist.
- **`409 Conflict`**: Duplicate ID, state transition conflict, conditional write failed.
- **`500 Internal Error`**: Unhandled exception (log details internally, return sanitized message).

---

## 3. SECURITY & AUTHORIZATION (OWASP SERVERLESS)

### 3.1 Backend as the Authoritative Security Boundary
- The frontend UI check (`if (role === 'Admin') showButton()`) is strictly cosmetic for UX.
- **Every backend request MUST authenticate the caller and verify authorization independently.**
- Never trust client-supplied user IDs, roles, or claims in the request body. Always extract the identity from the verified JWT authorizer context:

```python
# CORRECT: Extract identity from authorizer claims
def extract_caller_identity(event):
    authorizer = event.get("requestContext", {}).get("authorizer", {})
    claims = authorizer.get("jwt", {}).get("claims", {})
    
    username = claims.get("username") or claims.get("cognito:username") or claims.get("sub")
    email = claims.get("email")
    
    if not username:
        return None
    return {"username": username, "email": email}
```

### 3.2 Role-Based Access Control (RBAC)
The platform defines 4 standard roles:
1. **`Admin`**: Full management (create users, assign roles, view system audits, manage assets).
2. **`Manager`**: Asset creation, assignment, verification, and transfers within assigned scope.
3. **`Auditor`**: Read-only access to assets, audit logs, and compliance verification.
4. **`User`**: End-user access to owned or assigned assets.

Every protected action must query the caller's authoritative role from `SIH-Users` and enforce permissions before executing domain logic.

### 3.3 Zero Secrets in Source Code
- Never hardcode API keys, database credentials, AWS access keys, or private keys.
- Reference secrets using environment variables or AWS Secrets Manager.
- In logs and error messages, redact sensitive data (passwords, tokens, keys) with `[REDACTED]`.

---

## 4. DYNAMODB DATA ACCESS PATTERNS

### 4.1 Strict Injection Prevention (Parameterized Expressions)
Never concatenate strings into DynamoDB expressions. Always use `ExpressionAttributeNames` and `ExpressionAttributeValues`:

```python
# CORRECT: Parameterized Expression
table.update_item(
    Key={"assetId": asset_id},
    UpdateExpression="SET #st = :new_status, #up = :updated_at",
    ExpressionAttributeNames={
        "#st": "status",
        "#up": "updatedAt"
    },
    ExpressionAttributeValues={
        ":new_status": "TRANSFERRED",
        ":updated_at": current_timestamp
    }
)
```

### 4.2 Avoid Table Scans in Production Routes
- Table scans (`table.scan()`) examine every item in the table, degrading linearly with data size and increasing AWS read costs.
- **Rules:**
  - For single-item lookup: Use `table.get_item(Key={...})`.
  - For multi-item queries: Use `table.query(KeyConditionExpression=...)` with partition keys or Global Secondary Indexes (GSIs).
  - Use `scan()` only in controlled administrative exports or migration scripts, never on hot API request paths.

### 4.3 Race Condition Prevention (Conditional Writes)
Prevent overwrite conflicts and duplicate creations using `ConditionExpression`:

```python
# Prevent duplicate resource creation:
table.put_item(
    Item=asset_record,
    ConditionExpression="attribute_not_exists(assetId)"
)

# Prevent invalid state transitions:
table.update_item(
    Key={"assetId": asset_id},
    UpdateExpression="SET #st = :transferred",
    ConditionExpression="#st = :active",
    ExpressionAttributeNames={"#st": "status"},
    ExpressionAttributeValues={
        ":transferred": "TRANSFERRED",
        ":active": "ACTIVE"
    }
)
```

---

## 5. AUDIT TRAIL & TAMPER-EVIDENCE PATTERNS

Every state mutation (asset creation, transfer, role change, status update) MUST generate an immutable audit record in `SIH-AuditEvents`.

### 5.1 Audit Event Schema
Each audit record must contain:
```json
{
  "eventId": "evt_01J8X9...",
  "timestamp": "2026-09-27T12:00:00.000Z",
  "actorId": "USR-ADMIN-001",
  "actorRole": "Admin",
  "action": "ASSET_TRANSFER",
  "resourceType": "ASSET",
  "resourceId": "AST-1002",
  "details": {
    "fromUser": "USR-004",
    "toUser": "USR-005",
    "reason": "Department reassignment"
  },
  "payloadHash": "sha256_hash_of_details",
  "ipAddress": "192.168.1.1"
}
```

---

## 6. INPUT VALIDATION & ERROR HANDLING

### 6.1 Fail Fast at the Boundary
Validate all inputs before calling any domain service or database:
1. Parse JSON safely (catch `json.JSONDecodeError`).
2. Check for required fields.
3. Validate data types and string lengths.
4. Validate email formats using regex.
5. Validate password complexity (minimum 8 chars, 1 uppercase, 1 lowercase, 1 digit).
6. Validate enum values against defined sets (`ALLOWED_ROLES`, `ALLOWED_STATUSES`).

### 6.2 Defensive Exception Handling
Do not let unhandled exceptions crash Lambda silently. Catch specific exceptions first (`ClientError`, `KeyError`, `ValueError`), and fallback to a global error handler that returns clean `500` JSON while logging the full traceback to CloudWatch.

```python
from botocore.exceptions import ClientError

try:
    # Business logic
    ...
except ValueError as e:
    return make_response(400, str(e), error_code="VALIDATION_ERROR")
except ClientError as e:
    code = e.response.get("Error", {}).get("Code")
    if code == "ConditionalCheckFailedException":
        return make_response(409, "Resource already exists or invalid state", error_code="CONFLICT")
    # Log unexpected AWS error
    print(f"AWS ClientError: {e}")
    return make_response(500, "Internal database error", error_code="DATABASE_ERROR")
except Exception as e:
    print(f"Unhandled exception: {e}")
    return make_response(500, "Internal server error", error_code="INTERNAL_SERVER_ERROR")
```

---

## 7. AWS COST & PERFORMANCE DISCIPLINE ($20 BUDGET)

To protect the hard $20 AWS account limit:
1. **Memory & Timeout Tuning:** Default Lambda memory to 128 MB or 256 MB. Keep timeouts small (3 to 10 seconds).
2. **On-Demand Billing:** Keep DynamoDB tables set to `PAY_PER_REQUEST` so idle tables cost $0.
3. **No Polling Loops:** Never write Lambda code that sleeps, loops indefinitely, or polls long-running tasks synchronously.
4. **Log Retention:** Set CloudWatch log group retention to 7 or 14 days to prevent log storage accumulation.

---

## 8. LOCAL TESTING BEFORE DEPLOYMENT

Backend code must be tested locally before any AWS deployment.

### 8.1 Unit Testing Contract
For every backend endpoint or service function, write tests covering:
1. **Happy Path:** Valid input returns expected status (200/201) and payload.
2. **Missing Input:** Missing required field returns `400 Bad Request`.
3. **Malformed Input:** Non-JSON or invalid types return `400 Bad Request`.
4. **Unauthenticated:** Missing JWT claims returns `401 Unauthorized`.
5. **Unauthorized (RBAC):** Non-admin attempting admin operation returns `403 Forbidden`.
6. **Nonexistent Resource:** Updating missing ID returns `404 Not Found`.
7. **Conflict/Duplicate:** Duplicate primary key returns `409 Conflict`.
8. **Downstream Failure:** Database error returns clean `500 Internal Error`.

Never claim code is tested unless negative test cases pass.
