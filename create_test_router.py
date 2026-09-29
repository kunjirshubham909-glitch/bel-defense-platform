import pathlib
code = '''"""
Local API Gateway Event Simulator and Router Tests.

Tests the Lambda router with simulated API Gateway v2 HTTP events.
"""

import unittest
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional
def create_apigw_event(
    method: str,
    path: str,
    body: Optional[Dict[str, Any]] = None,
    claims: Optional[Dict[str, Any]] = None,
    path_params: Optional[Dict[str, str]] = None,
    query_params: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Construct authentic API Gateway v2 HTTP event dictionary."""
    event = {
        "version": "2.0",
        "routeKey": f"{method} {path}",
        "rawPath": path,
        "rawQueryString": "",
        "headers": {"content-type": "application/json"},
        "queryStringParameters": {},
        "requestContext": {
            "accountId": "123456789012",
            "apiId": "test-api",
            "http": {"method": method, "path": method, "protocol": "HTTP/1.1", "sourceIp": "127.0.0.1"},
            "requestId": "test-request-id",
            "routeKey": f"{method} {path}",
            "stage": "test",
            "time": datetime.now(timezone.utc).strftime("%d/%b/%Y:%H:%M:%S %z"),
            "timeEpoch": int(datetime.now(timezone.utc).timestamp() * 1000),
        },
        "pathParameters": {},
        "isBase64Encoded": False,
    }
    
    if body is not None:
        event["body"] = json.dumps(body)
    
    if claims is not None:
        event["requestContext"]["authorizer"] = {"jwt": {"claims": claims}}
    
    return event


class TestLambdaRouter(unittest.TestCase):
    """Test Lambda router with simulated API Gateway events."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        os.environ['LOCAL_TEST'] = 'true'
        
        import importlib
        import backend.lambda_function as lambda_module
        importlib.reload(lambda_module)
        cls.lambda_handler = lambda_module.lambda_handler
        
        cls.user_repo = InMemoryUserRepository()
        cls.asset_repo = InMemoryAssetRepository()
        cls.audit_ledger = InMemoryAuditLedger()
        
        cls.admin = User(
            userId="admin1", name="Admin", email="admin@mil.gov",
            role=UserRole.ADMIN, clearanceLevel=ClearanceLevel.TOP_SECRET,
            unit=MilitaryUnit.ARMY, cognitoUsername="admin@mil.gov"
        )
        cls.manager = User(
            userId="mgr1", name="Manager", email="mgr@army.mil",
            role=UserRole.MANAGER, clearanceLevel=ClearanceLevel.SECRET,
            unit=MilitaryUnit.ARMY, cognitoUsername="mgr@army.mil"
        )
        cls.user = User(
            userId="u1", name="User1", email="u1@army.mil",
            role=UserRole.USER, clearanceLevel=ClearanceLevel.SECRET,
            unit=MilitaryUnit.ARMY, cognitoUsername="u1@army.mil"
        )
        cls.auditor = User(
            userId="aud1", name="Auditor", email="aud1@mil.gov",
            role=UserRole.AUDITOR, clearanceLevel=ClearanceLevel.SECRET,
            unit=MilitaryUnit.ARMY, cognitoUsername="aud1@mil.gov"
        )
        cls.navy_user = User(
            userId="n1", name="Navy User", email="n1@navy.mil",
            role=UserRole.USER, clearanceLevel=ClearanceLevel.SECRET,
            unit=MilitaryUnit.NAVY, cognitoUsername="n1@navy.mil"
        )
        
        for u in [cls.admin, cls.manager, cls.user, cls.auditor, cls.navy_user]:
            cls.user_repo.save(u)
        
        cls.user_service = UserService(cls.user_repo, cls.audit_ledger)
        cls.asset_service = AssetService(cls.asset_repo, cls.user_repo, cls.audit_ledger)
        
        cls.asset = cls.asset_service.register_asset(cls.manager, {
            "assetId": "radar_firmware_v1",
            "name": "Radar Firmware v1",
            "assetType": "Software",
            "classification": "SECRET",
            "unit": "ARMY",
            "compartment": "PROJECT_RADAR",
            "custodianId": "u1",
        })
        
        cls.paseto = PASETOAdapter()
        cls.master_key = b"0" * 32

    def _make_admin_claims(self) -> Dict[str, Any]:
        return {"sub": "admin1", "email": "admin@mil.gov", "custom:role": "Admin", "custom:clearanceLevel": "TOP_SECRET", "custom:unit": "ARMY", "custom:compartments": ""}

    def _make_manager_claims(self) -> Dict[str, Any]:
        return {"sub": "mgr1", "email": "mgr@army.mil", "custom:role": "Manager", "custom:clearanceLevel": "SECRET", "custom:unit": "ARMY", "custom:compartments": ""}

    def _make_user_claims(self) -> Dict[str, Any]:
        return {"sub": "u1", "email": "u1@army.mil", "custom:role": "User", "custom:clearanceLevel": "SECRET", "custom:unit": "ARMY", "custom:compartments": ""}

    def _make_auditor_claims(self) -> Dict[str, Any]:
        return {"sub": "aud1", "email": "aud1@mil.gov", "custom:role": "Auditor", "custom:clearanceLevel": "SECRET", "custom:unit": "ARMY", "custom:compartments": ""}

    def _make_navy_claims(self) -> Dict[str, Any]:
        return {"sub": "n1", "email": "n1@navy.mil", "custom:role": "User", "custom:clearanceLevel": "SECRET", "custom:unit": "NAVY", "custom:compartments": ""}

# Set local test mode before importing services
os.environ['LOCAL_TEST'] = 'true'

from backend.domain.entities import User, DefenseAsset, ClearanceLevel, MilitaryUnit, AssetState, UserRole
from backend.adapters.in_memory_repo import InMemoryUserRepository, InMemoryAssetRepository, InMemoryAuditLedger
from backend.services.user_service import UserService
from backend.services.asset_service import AssetService
from backend.services.verification_service import VerificationService
from backend.adapters.paseto_adapter import PASETOAdapter
'''