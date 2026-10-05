"""
Comprehensive tests for Bilnov Gallery licensing lifecycle, openapi.json compliance,
./data reading, and protection guarantees.
"""

import datetime
import hashlib
import hmac
import http.server
import json
import os
import shutil
import socketserver
import tempfile
import threading
import unittest
from pathlib import Path

from config import DATA_DIR
from desktop.backend.library import LibraryManager
from desktop.backend.licensing import (
    LicenseManager,
    LicenseState,
    compute_license_checksum,
    get_deterministic_device_id,
)


class MockLicenseServerHandler(http.server.BaseHTTPRequestHandler):
    """Simulates OpenAPI endpoints defined in openapi.json."""

    revoked = False
    expired = False

    def log_message(self, format, *args):
        # Silence HTTP server logs during tests
        return

    def do_POST(self):
        content_len = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(content_len).decode("utf-8")) if content_len > 0 else {}

        if self.path == "/api/v1/license/activate":
            cust = body.get("customer", {})
            key = body.get("license_key", "")
            dev_id = body.get("device_id", "")

            # Validate openapi schema constraints
            if len(key) < 10 or len(cust.get("name", "")) < 2 or "@" not in cust.get("email", ""):
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": False,
                    "status_code": "INVALID_PAYLOAD",
                    "message": "Validation failed",
                    "server_time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                }).encode("utf-8"))
                return

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
            exp_iso = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)).isoformat()
            self.wfile.write(json.dumps({
                "success": True,
                "status_code": "ACTIVE",
                "message": "License bound and activated successfully",
                "license_key": key,
                "device_id": dev_id,
                "expires_at": exp_iso,
                "server_time": now_iso,
                "customer_name": cust.get("name"),
                "signature": "mock-hmac-sha256-signature-xyz",
            }).encode("utf-8"))

        elif self.path == "/api/v1/license/verify":
            key = body.get("license_key", "")
            dev_id = body.get("device_id", "")

            if self.__class__.revoked:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": False,
                    "status_code": "REVOKED",
                    "message": "License has been revoked by platform administrator",
                    "server_time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                }).encode("utf-8"))
                return

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
            exp_iso = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)).isoformat()
            self.wfile.write(json.dumps({
                "success": True,
                "status_code": "ACTIVE",
                "message": "License verified",
                "license_key": key,
                "device_id": dev_id,
                "expires_at": exp_iso,
                "server_time": now_iso,
                "signature": "mock-hmac-sha256-signature-xyz",
            }).encode("utf-8"))

        elif self.path == "/api/v1/license/heartbeat":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
            is_active = not self.__class__.revoked
            is_exp = self.__class__.expired
            self.wfile.write(json.dumps({
                "success": is_active and not is_exp,
                "status_code": "ACTIVE" if (is_active and not is_exp) else "INACTIVE",
                "is_active": is_active,
                "is_expired": is_exp,
                "expires_at": (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)).isoformat(),
                "server_time": now_iso,
                "signature": "mock-hmac-sha256-signature-xyz",
            }).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        if self.path.startswith("/api/v1/license/status/"):
            key = self.path.split("/")[-1]
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "license_key": key,
                "is_active": not self.__class__.revoked,
                "is_expired": self.__class__.expired,
                "is_bound": True,
                "expires_at": (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)).isoformat(),
                "status_display": "Active" if not self.__class__.revoked else "Revoked",
            }).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()


class TestBilnovGallery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Start local mock license server
        cls.server = socketserver.TCPServer(("127.0.0.1", 0), MockLicenseServerHandler)
        cls.port = cls.server.server_address[1]
        cls.server_thread = threading.Thread(target=cls.server.serve_forever)
        cls.server_thread.daemon = True
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        MockLicenseServerHandler.revoked = False
        MockLicenseServerHandler.expired = False
        self.tmp_dir = Path(tempfile.mkdtemp(prefix="bilnov_test_"))
        self.license_file = self.tmp_dir / ".zed_license.json"
        self.server_url = f"http://127.0.0.1:{self.port}"
        self.lic = LicenseManager(server_url=self.server_url, license_file=self.license_file)

    def tearDown(self):
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)

    # -------------------------------------------------------------
    # 1. Device ID & Integrity Tests
    # -------------------------------------------------------------

    def test_deterministic_device_id(self):
        dev1 = get_deterministic_device_id()
        dev2 = get_deterministic_device_id()
        self.assertEqual(len(dev1), 64, "Device ID must be 64-char SHA-256")
        self.assertEqual(dev1, dev2, "Device ID must be deterministic across calls")

    def test_initial_state_needs_activation(self):
        self.assertFalse(self.license_file.exists())
        ok, msg = self.lic.verify_license()
        self.assertFalse(ok)
        self.assertEqual(self.lic.current_state.status_code, "NEEDS_ACTIVATION")

    # -------------------------------------------------------------
    # 2. Input Validation (openapi.json constraints)
    # -------------------------------------------------------------

    def test_activation_schema_validation(self):
        # Short key (< 10)
        ok, msg = self.lic.activate_license("ZED-123", "Alice", "alice@example.com", "1234567")
        self.assertFalse(ok)
        self.assertIn("License key", msg)

        # Short name (< 2)
        ok, msg = self.lic.activate_license("ZED-1234-5678-9012", "A", "alice@example.com", "1234567")
        self.assertFalse(ok)
        self.assertIn("Full Name", msg)

        # Invalid email
        ok, msg = self.lic.activate_license("ZED-1234-5678-9012", "Alice", "bademail", "1234567")
        self.assertFalse(ok)
        self.assertIn("email", msg)

        # Short phone (< 6)
        ok, msg = self.lic.activate_license("ZED-1234-5678-9012", "Alice", "alice@example.com", "123")
        self.assertFalse(ok)
        self.assertIn("phone", msg)

    # -------------------------------------------------------------
    # 3. Successful Activation & Verification Workflow
    # -------------------------------------------------------------

    def test_successful_activation_and_verification(self):
        # 1. Activate
        ok, msg = self.lic.activate_license(
            "ZED-ABCD-1234-EFGH",
            "John Doe",
            "john@bilnov.com",
            "+15551234567",
            "123 Main St",
        )
        self.assertTrue(ok)
        self.assertTrue(self.license_file.exists())
        self.assertTrue(self.lic.current_state.is_valid)
        self.assertEqual(self.lic.current_state.status_code, "ACTIVE")
        self.assertEqual(self.lic.current_state.customer_name, "John Doe")

        # Verify atomic file contents
        with open(self.license_file, "r") as f:
            data = json.load(f)
        self.assertEqual(data["license_key"], "ZED-ABCD-1234-EFGH")
        self.assertIn("checksum", data)

        # 2. Subsequent Verification Handshake
        lic2 = LicenseManager(server_url=self.server_url, license_file=self.license_file)
        ok2, msg2 = lic2.verify_license()
        self.assertTrue(ok2)
        self.assertEqual(lic2.current_state.status_code, "ACTIVE")

    # -------------------------------------------------------------
    # 4. 7-Day Offline Grace Period
    # -------------------------------------------------------------

    def test_offline_grace_period(self):
        # First activate
        self.lic.activate_license("ZED-ABCD-1234-EFGH", "John Doe", "john@bilnov.com", "+15551234567")

        # Simulate unreachable server
        offline_lic = LicenseManager(server_url="http://127.0.0.1:9999", license_file=self.license_file)
        ok, msg = offline_lic.verify_license()
        self.assertTrue(ok, "Within 7 days offline grace, verification must succeed")
        self.assertEqual(offline_lic.current_state.status_code, "ACTIVE_OFFLINE")
        self.assertGreaterEqual(offline_lic.current_state.offline_days_remaining, 6)

        # Simulate expired offline grace (> 7 days)
        with open(self.license_file, "r") as f:
            data = json.load(f)
        past_time = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=8)).isoformat()
        data["last_verified_at"] = past_time
        data["checksum"] = compute_license_checksum(data)
        with open(self.license_file, "w") as f:
            json.dump(data, f)

        ok_expired, msg_expired = offline_lic.verify_license()
        self.assertFalse(ok_expired, "After 7 days offline, verification must fail")
        self.assertEqual(offline_lic.current_state.status_code, "OFFLINE_EXPIRED")

    # -------------------------------------------------------------
    # 5. Heartbeat & Revocation
    # -------------------------------------------------------------

    def test_heartbeat_revocation(self):
        self.lic.activate_license("ZED-ABCD-1234-EFGH", "John Doe", "john@bilnov.com", "+15551234567")
        self.assertTrue(self.lic.current_state.is_valid)

        # Heartbeat OK
        ok, msg = self.lic.heartbeat()
        self.assertTrue(ok)
        self.assertEqual(self.lic.current_state.status_code, "ACTIVE")

        # Administrator revokes license on dashboard
        MockLicenseServerHandler.revoked = True
        ok_revoked, msg_revoked = self.lic.heartbeat()
        self.assertFalse(ok_revoked)
        self.assertEqual(self.lic.current_state.status_code, "REVOKED")
        self.assertFalse(self.lic.current_state.is_valid)

    # -------------------------------------------------------------
    # 6. Anti-Tampering Checks
    # -------------------------------------------------------------

    def test_tamper_detection(self):
        self.lic.activate_license("ZED-ABCD-1234-EFGH", "John Doe", "john@bilnov.com", "+15551234567")

        # Manually alter license file without updating checksum
        with open(self.license_file, "r") as f:
            data = json.load(f)
        data["customer_name"] = "Hacker"
        with open(self.license_file, "w") as f:
            json.dump(data, f)

        tampered_lic = LicenseManager(server_url=self.server_url, license_file=self.license_file)
        self.assertIsNone(tampered_lic.load_local_license())
        ok, msg = tampered_lic.verify_license()
        self.assertFalse(ok)
        self.assertEqual(tampered_lic.current_state.status_code, "NEEDS_ACTIVATION")

    # -------------------------------------------------------------
    # 7. Library Scanning ./data & Safety
    # -------------------------------------------------------------

    def test_library_manager_reads_data_folder(self):
        test_data_dir = self.tmp_dir / "data"
        test_data_dir.mkdir()

        # Create sample category / subcategory / article
        art_dir = test_data_dir / "Living Room" / "Sofas" / "Modern_Velvet_Sofa"
        art_dir.mkdir(parents=True)
        (art_dir / "preview_1.jpg").write_bytes(b"fake_image_data")
        (art_dir / "preview_2.png").write_bytes(b"fake_image_data_2")

        model_dir = art_dir / "model"
        model_dir.mkdir()
        (model_dir / "sofa.skp").write_bytes(b"fake_skp_data_12345")

        mgr = LibraryManager(base_dir=test_data_dir)
        res = mgr.scan_library()

        self.assertEqual(len(res["items"]), 1)
        item = res["items"][0]
        self.assertEqual(item["category"], "Living Room")
        self.assertEqual(item["subcategory"], "Sofas")
        self.assertEqual(item["title"], "Modern Velvet Sofa")
        self.assertTrue(item["has_model"])
        self.assertEqual(item["model_filename"], "sofa.skp")
        self.assertEqual(item["images_count"], 2)

    def test_data_folder_operations(self):
        """Verify delete_item and create_bundle_zip operate on ./data when protection is removed."""
        test_data_dir = self.tmp_dir / "data_ops"
        test_data_dir.mkdir()
        art_dir = test_data_dir / "CategoryA" / "SubA" / "ArticleA"
        art_dir.mkdir(parents=True)
        (art_dir / "file.txt").write_text("sample content")

        mgr = LibraryManager(base_dir=test_data_dir)
        zip_res = mgr.create_bundle_zip("CategoryA/SubA/ArticleA")
        self.assertIsNotNone(zip_res)
        self.assertTrue(zip_res.exists())

        del_ok = mgr.delete_item("CategoryA/SubA/ArticleA")
        self.assertTrue(del_ok)
        self.assertFalse(art_dir.exists())


if __name__ == "__main__":
    unittest.main()
