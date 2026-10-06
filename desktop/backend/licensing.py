"""
Bilnov Gallery Desktop Client Integration & Licensing API Client
Strictly implements the complete licensing lifecycle specified in openapi.json:

1. Public Machine-to-Machine Access (no administrator credentials required)
2. First Launch (Initial Activation) with 64-char deterministic hardware ID (device_id)
   and storage in ~/.zed_license.json
3. Verification Handshake with 30-Day Offline Grace Period (OFFLINE_GRACE)
4. Runtime Heartbeat (every 4 hours)
5. Cryptographic Anti-Tampering (HMAC-SHA256 signature and atomic disk storage)
6. Client Registration & Inquiry (/api/v1/client/profile, /api/v1/client/status)
"""

import datetime
import hashlib
import hmac
import json
import logging
import os
import platform
import subprocess
import sys
import tempfile
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import requests

from config import (
    LICENSE_FILE_PATH,
    LICENSE_SERVER_URL,
    OFFLINE_GRACE_DAYS,
)

logger = logging.getLogger("licensing")

# Secret salt for local anti-tampering verification checksum
_LOCAL_INTEGRITY_SALT = "bilnov-desktop-anti-tamper-v1-secret"

# 30-Day Free Trial Configuration
TRIAL_DAYS = 30
TRIAL_FILE_PATH = Path.home() / ".bilnov_trial.json"


def get_deterministic_device_id() -> str:
    """
    Derives a 64-character deterministic SHA-256 hardware identifier (device_id).
    Stable across reboots on the same machine.
    """
    markers = []

    # 1. Hardware MAC address
    try:
        node = uuid.getnode()
        markers.append(f"mac:{node}")
    except Exception:
        pass

    # 2. OS-specific hardware UUID
    if sys.platform == "darwin":
        try:
            out = subprocess.check_output(
                ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=3,
            )
            for line in out.splitlines():
                if "IOPlatformUUID" in line:
                    uuid_str = line.split('"')[-2]
                    markers.append(f"iouuid:{uuid_str}")
                    break
        except Exception:
            pass
    elif sys.platform.startswith("linux"):
        for p in ["/etc/machine-id", "/var/lib/dbus/machine-id"]:
            if os.path.exists(p):
                try:
                    markers.append(f"mid:{Path(p).read_text().strip()}")
                    break
                except Exception:
                    pass
    elif sys.platform == "win32":
        try:
            out = subprocess.check_output(
                ["wmic", "csproduct", "get", "UUID"],
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=3,
            )
            lines = [l.strip() for l in out.splitlines() if l.strip() and "UUID" not in l]
            if lines:
                markers.append(f"win_uuid:{lines[0]}")
        except Exception:
            pass

    # 3. System architecture and hostname fallback
    markers.append(f"arch:{platform.machine()}")
    markers.append(f"system:{platform.system()}")

    raw = "|".join(markers)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def compute_license_checksum(data: Dict[str, Any]) -> str:
    """Computes HMAC-SHA256 checksum to ensure local license storage integrity."""
    elements = [
        str(data.get("license_key", "")),
        str(data.get("device_id", "")),
        str(data.get("customer_name", "")),
        str(data.get("expires_at", "")),
        str(data.get("signature", "")),
        str(data.get("last_verified_at", "")),
    ]
    raw = ":".join(elements).encode("utf-8")
    return hmac.new(_LOCAL_INTEGRITY_SALT.encode("utf-8"), raw, hashlib.sha256).hexdigest()


_STATUS_CODE_ALIASES = {
    "OK": "ACTIVE",
    "VALID": "ACTIVE",
    "VERIFIED": "ACTIVE",
    "SUCCESS": "ACTIVE",
    "LICENSED": "ACTIVE",
    "ACTIVE_VERIFIED": "ACTIVE",
    "TRIAL_ACTIVE": "TRIAL",
    "OFFLINE": "ACTIVE_OFFLINE",
    "GRACE": "ACTIVE_OFFLINE",
    "OFFLINE_GRACE": "ACTIVE_OFFLINE",
    "NEEDS_ACTIVATE": "NEEDS_ACTIVATION",
    "PENDING_ACTIVATION": "NEEDS_ACTIVATION",
}


def normalize_status_code(raw: Any, default: str = "ACTIVE") -> str:
    """Normalizes server-provided status codes to the canonical client values."""
    code = str(raw or default).strip().upper().replace(" ", "_").replace("-", "_")
    return _STATUS_CODE_ALIASES.get(code, code)


@dataclass
class LicenseState:
    is_valid: bool = False
    status_code: str = "NEEDS_ACTIVATION"  # ACTIVE, ACTIVE_OFFLINE, EXPIRED, REVOKED, OFFLINE_EXPIRED, NEEDS_ACTIVATION
    message: str = "License requires initial activation"
    license_key: str = ""
    device_id: str = ""
    customer_name: str = ""
    customer_email: str = ""
    customer_phone: str = ""
    expires_at: Optional[str] = None
    last_verified_at: Optional[str] = None
    offline_days_remaining: int = 0
    signature: Optional[str] = None


class LicenseManager:
    """
    Manages the complete licensing lifecycle for Bilnov Gallery Desktop Client.
    """

    def __init__(self, server_url: Optional[str] = None, license_file: Optional[Path] = None):
        self.server_url = (server_url or LICENSE_SERVER_URL).rstrip("/")
        self.license_file = Path(license_file or LICENSE_FILE_PATH).expanduser()
        self.device_id = get_deterministic_device_id()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "BilnovGalleryDesktop/1.0.0"})

        self.current_state = LicenseState(device_id=self.device_id)
        self.trial_details: Dict[str, Any] = {}

    # -------------------------------------------------------------
    # Disk Storage Helpers (Atomic read/write ~/.zed_license.json)
    # -------------------------------------------------------------

    def load_local_license(self) -> Optional[Dict[str, Any]]:
        """Reads and validates ~/.zed_license.json."""
        if not self.license_file.exists():
            return None

        try:
            with open(self.license_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Drop legacy admin key field from older license files (auth is no longer required)
            data.pop("admin_key", None)

            # Anti-tampering check: verify checksum
            saved_checksum = data.get("checksum")
            calc_checksum = compute_license_checksum(data)
            if saved_checksum != calc_checksum:
                logger.warning("Local license file checksum mismatch (corrupted or tampered).")
                self._tampered_detected = True
                return None

            # Hardware binding check
            if data.get("device_id") != self.device_id:
                logger.warning("Local license bound to different hardware ID.")
                self._tampered_detected = True
                return None

            self._tampered_detected = False
            return data
        except Exception as e:
            logger.error("Failed to read local license: %s", e)
            return None

    def save_local_license(self, data: Dict[str, Any]) -> bool:
        """Atomically writes license details to ~/.zed_license.json."""
        try:
            data["device_id"] = self.device_id
            data["checksum"] = compute_license_checksum(data)

            # Atomic write via temp file
            parent_dir = self.license_file.parent
            parent_dir.mkdir(parents=True, exist_ok=True)

            fd, tmp_path = tempfile.mkstemp(dir=parent_dir, prefix=".zed_lic_tmp_")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            os.replace(tmp_path, self.license_file)
            # Ensure permissions: user read/write only
            os.chmod(self.license_file, 0o600)
            return True
        except Exception as e:
            logger.error("Failed to atomically save license file: %s", e)
            return False

    # -------------------------------------------------------------
    # 30-Day Free Trial Management
    # -------------------------------------------------------------

    def get_or_create_trial(self) -> Dict[str, Any]:
        """Reads or initializes 30-day free trial bound to hardware device_id."""
        if TRIAL_FILE_PATH.exists():
            try:
                with open(TRIAL_FILE_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("device_id") == self.device_id and "started_at" in data:
                    return data
            except Exception as e:
                logger.warning("Could not read trial file: %s", e)

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        data = {
            "device_id": self.device_id,
            "started_at": now_iso,
            "trial_days": TRIAL_DAYS,
        }
        try:
            with open(TRIAL_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.chmod(TRIAL_FILE_PATH, 0o600)
        except Exception as e:
            logger.warning("Could not persist trial file: %s", e)
        return data

    def get_network_time(self) -> Tuple[datetime.datetime, bool]:
        """
        Attempts to query network/server time via HTTP Date header.
        Returns: (datetime_utc, is_synced: bool)
        """
        import email.utils
        targets = [
            self.server_url,
            "https://bilnov-gallery.bilnov.com",
            "https://cloudflare.com",
            "https://www.google.com",
        ]
        for target in targets:
            try:
                resp = self.session.head(target, timeout=3)
                date_hdr = resp.headers.get("Date")
                if date_hdr:
                    dt = email.utils.parsedate_to_datetime(date_hdr)
                    if dt:
                        return dt.astimezone(datetime.timezone.utc), True
            except Exception:
                continue

        return datetime.datetime.now(datetime.timezone.utc), False

    def evaluate_trial_detailed(self, use_network: bool = True) -> Dict[str, Any]:
        """
        Evaluates 30-day free trial using verified network time.
        When use_network is False only the local clock is used (no blocking HTTP),
        which keeps startup instant. Returns detailed dict with days, hours,
        sync status, and formatted string.
        """
        data = self.get_or_create_trial()
        started_str = data.get("started_at", "")
        if use_network:
            now, is_net_synced = self.get_network_time()
        else:
            now, is_net_synced = datetime.datetime.now(datetime.timezone.utc), False

        try:
            started_dt = datetime.datetime.fromisoformat(started_str.replace("Z", "+00:00"))
        except Exception:
            started_dt = now

        elapsed_seconds = (now - started_dt).total_seconds()
        total_seconds = TRIAL_DAYS * 86400
        remaining_seconds = max(0.0, total_seconds - elapsed_seconds)

        days = int(remaining_seconds // 86400)
        hours = int((remaining_seconds % 86400) // 3600)
        days_left = min(TRIAL_DAYS, max(1, int(remaining_seconds / 86400) + 1)) if remaining_seconds > 0 else 0
        is_active = remaining_seconds > 0

        expiry_dt = started_dt + datetime.timedelta(days=TRIAL_DAYS)
        expiry_str = expiry_dt.strftime("%Y-%m-%d %H:%M UTC")

        if is_active:
            msg = f"30-Day Free Trial: {days} day(s), {hours} hour(s) remaining"
        else:
            msg = "30-Day Free Trial has expired. Workstation license required."

        result = {
            "is_active": is_active,
            "days_remaining": days,
            "hours_remaining": hours,
            "days_left": days_left,
            "remaining_seconds": int(remaining_seconds),
            "expires_at": expiry_str,
            "is_net_synced": is_net_synced,
            "message": msg,
            "started_at": started_str,
        }
        self.trial_details = result
        return result

    def evaluate_trial(self, use_network: bool = True) -> Tuple[bool, int, str]:
        """
        Evaluates 30-day free trial status.
        Returns: (is_active, days_remaining, message)
        """
        details = self.evaluate_trial_detailed(use_network=use_network)
        return details["is_active"], details["days_left"], details["message"]

    def bootstrap_state(self) -> LicenseState:
        """
        Synchronous first-paint state, called before the QML engine loads so a
        fresh install shows its default 30-day trial immediately instead of
        flashing "Workstation Activation Required". No network I/O here:
        verify_license() runs asynchronously right after and corrects the state
        (e.g. REVOKED when the client was deleted server-side).
        """
        local_data = self.load_local_license()

        if getattr(self, "_tampered_detected", False):
            self.current_state = LicenseState(
                is_valid=False,
                status_code="NEEDS_ACTIVATION",
                message="License file corrupted or tampered. Activation required.",
                device_id=self.device_id,
            )
            return self.current_state

        if not local_data:
            details = self.evaluate_trial_detailed(use_network=False)
            if details["is_active"]:
                self.current_state = LicenseState(
                    is_valid=True,
                    status_code="TRIAL",
                    message=details["message"],
                    device_id=self.device_id,
                    customer_name=f"Trial Workstation ({details['days_left']}d left)",
                    offline_days_remaining=details["days_left"],
                )
            else:
                self.current_state = LicenseState(
                    is_valid=False,
                    status_code="TRIAL_EXPIRED",
                    message="30-Day Free Trial has expired. Workstation license required.",
                    device_id=self.device_id,
                )
            return self.current_state

        # Licensed machine: optimistic local state; verify_license() corrects it.
        expires_str = local_data.get("expires_at")
        if expires_str:
            try:
                expires_dt = datetime.datetime.fromisoformat(expires_str.replace("Z", "+00:00"))
                if datetime.datetime.now(datetime.timezone.utc) > expires_dt:
                    self.current_state = LicenseState(
                        is_valid=False,
                        status_code="EXPIRED",
                        message="License expired. Online renewal required.",
                        license_key=local_data.get("license_key", ""),
                        device_id=self.device_id,
                    )
                    return self.current_state
            except Exception:
                pass

        self.current_state = LicenseState(
            is_valid=True,
            status_code="ACTIVE",
            message="Verifying license...",
            license_key=local_data.get("license_key", ""),
            device_id=self.device_id,
            customer_name=local_data.get("customer_name", ""),
            customer_email=local_data.get("customer_email", ""),
            customer_phone=local_data.get("customer_phone", ""),
            expires_at=local_data.get("expires_at"),
            last_verified_at=local_data.get("last_verified_at"),
            signature=local_data.get("signature"),
        )
        return self.current_state

    # -------------------------------------------------------------
    # Lifecycle Workflows
    # -------------------------------------------------------------

    def activate_license(
        self,
        license_key: str,
        name: str = "",
        email: str = "",
        phone: str = "",
        address: str = "",
    ) -> Tuple[bool, str]:
        """
        Initial Activation (POST /api/v1/license/activate)
        Binds the hardware fingerprint to the license. Customer details are optional
        (ActivateLicenseIn.customer); whenever supplied they must be complete and valid.
        """
        key = license_key.strip()
        cust_name = name.strip()
        cust_email = email.strip()
        cust_phone = phone.strip()

        # Schema Validation (license_key + device_id required, customer optional)
        if len(key) < 10:
            return False, "License key format invalid (min 10 characters)"

        payload: Dict[str, Any] = {
            "license_key": key,
            "device_id": self.device_id,
        }

        if cust_name or cust_email or cust_phone:
            # CustomerDetailsSchema requires name, email and phone whenever customer is present
            if len(cust_name) < 2:
                return False, "Full Name must be at least 2 characters"
            if len(cust_email) < 5 or "@" not in cust_email:
                return False, "Valid email address is mandatory"
            if len(cust_phone) < 6:
                return False, "Contact phone number must be at least 6 digits"
            payload["customer"] = {
                "name": cust_name,
                "email": cust_email,
                "phone": cust_phone,
                "address": address.strip(),
            }

        url = f"{self.server_url}/api/v1/license/activate"
        try:
            resp = self.session.post(url, json=payload, timeout=12)
            data = resp.json() if resp.text else {}
        except Exception as e:
            logger.error("Activation request failed: %s", e)
            return False, f"Server connection failed: {str(e)}"

        if resp.status_code == 200 and data.get("success"):
            now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
            local_record = {
                "license_key": data.get("license_key") or key,
                "device_id": self.device_id,
                "customer_name": data.get("customer_name") or cust_name,
                "customer_email": cust_email,
                "customer_phone": cust_phone,
                "expires_at": data.get("expires_at"),
                "server_time": data.get("server_time") or now_iso,
                "signature": data.get("signature"),
                "last_verified_at": now_iso,
            }
            self.save_local_license(local_record)

            server_code = data.get("status_code", "ACTIVE")
            logger.info("Activate response status_code=%r -> %r", server_code, normalize_status_code(server_code))
            self.current_state = LicenseState(
                is_valid=True,
                status_code=normalize_status_code(server_code),
                message=data.get("message", "License activated successfully"),
                license_key=key,
                device_id=self.device_id,
                customer_name=local_record["customer_name"],
                customer_email=cust_email,
                customer_phone=cust_phone,
                expires_at=data.get("expires_at"),
                last_verified_at=now_iso,
                signature=data.get("signature"),
            )
            return True, data.get("message", "License successfully activated!")
        elif resp.status_code == 401:
            msg = (
                "Licensing server returned HTTP 401 (Unauthorized). "
                "Please contact support (+213775189229 / +213796629314)."
            )
            logger.warning(msg)
            return False, msg
        else:
            msg = data.get("message") or f"Activation rejected (HTTP {resp.status_code})"
            return False, msg

    def verify_license(self) -> Tuple[bool, str]:
        """
        Verification Handshake (POST /api/v1/license/verify)
        Checks local checksum, binds to device_id, and synchronizes status with server.
        Permits 30-Day Offline Grace Period if server is unreachable.
        """
        local_data = self.load_local_license()
        if getattr(self, "_tampered_detected", False):
            self.current_state = LicenseState(
                is_valid=False,
                status_code="NEEDS_ACTIVATION",
                message="License file corrupted or tampered. Activation required.",
                device_id=self.device_id,
            )
            return False, "License corrupted"

        if not local_data:
            is_trial_active, days_left, trial_msg = self.evaluate_trial()
            if is_trial_active:
                self.current_state = LicenseState(
                    is_valid=True,
                    status_code="TRIAL",
                    message=trial_msg,
                    device_id=self.device_id,
                    customer_name=f"Trial Workstation ({days_left}d left)",
                    offline_days_remaining=days_left,
                )
                return True, trial_msg
            else:
                self.current_state = LicenseState(
                    is_valid=False,
                    status_code="TRIAL_EXPIRED",
                    message="30-Day Free Trial has expired. Workstation license required.",
                    device_id=self.device_id,
                )
                return False, "Trial expired"

        key = local_data.get("license_key", "")
        last_verified_str = local_data.get("last_verified_at", "")
        expires_at_str = local_data.get("expires_at")

        # Parse timestamps
        now = datetime.datetime.now(datetime.timezone.utc)
        last_verified_dt = None
        if last_verified_str:
            try:
                last_verified_dt = datetime.datetime.fromisoformat(last_verified_str.replace("Z", "+00:00"))
            except Exception:
                pass

        expires_dt = None
        if expires_at_str:
            try:
                expires_dt = datetime.datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
            except Exception:
                pass

        # Handshake with licensing server
        url = f"{self.server_url}/api/v1/license/verify"
        payload = {
            "license_key": key,
            "device_id": self.device_id,
        }

        try:
            resp = self.session.post(url, json=payload, timeout=10)
            data = resp.json() if resp.text else {}
            server_online = True
        except Exception as e:
            logger.info("Licensing server unreachable (%s). Entering offline grace check.", e)
            server_online = False
            data = {}

        if server_online:
            if resp.status_code == 200 and data.get("success"):
                now_iso = now.isoformat()
                local_data["expires_at"] = data.get("expires_at") or local_data.get("expires_at")
                local_data["server_time"] = data.get("server_time") or now_iso
                local_data["signature"] = data.get("signature") or local_data.get("signature")
                local_data["last_verified_at"] = now_iso
                self.save_local_license(local_data)

                server_code = data.get("status_code", "ACTIVE")
                logger.info("Verify response status_code=%r -> %r", server_code, normalize_status_code(server_code))
                self.current_state = LicenseState(
                    is_valid=True,
                    status_code=normalize_status_code(server_code),
                    message=data.get("message", "License verified successfully"),
                    license_key=key,
                    device_id=self.device_id,
                    customer_name=local_data.get("customer_name", ""),
                    customer_email=local_data.get("customer_email", ""),
                    customer_phone=local_data.get("customer_phone", ""),
                    expires_at=local_data.get("expires_at"),
                    last_verified_at=now_iso,
                    signature=local_data.get("signature"),
                )
                return True, "License verified"
            elif resp.status_code == 401:
                logger.warning("Licensing server returned HTTP 401 (Unauthorized). Entering offline grace / trial mode.")
                server_online = False
            else:
                msg = data.get("message", "License disabled or expired by administrator")
                self.current_state = LicenseState(
                    is_valid=False,
                    status_code="EXPIRED" if "expired" in msg.lower() else "REVOKED",
                    message=msg,
                    license_key=key,
                    device_id=self.device_id,
                )
                return False, msg

        # --- OFFLINE GRACE PERIOD EVALUATION ---
        if last_verified_dt:
            elapsed = (now - last_verified_dt).total_seconds()
            grace_seconds = OFFLINE_GRACE_DAYS * 86400

            # Check expiration date if available
            if expires_dt and now > expires_dt:
                self.current_state = LicenseState(
                    is_valid=False,
                    status_code="EXPIRED",
                    message="License expired. Online renewal required.",
                    license_key=key,
                    device_id=self.device_id,
                )
                return False, "License expired"

            if elapsed <= grace_seconds:
                days_left = max(0, int((grace_seconds - elapsed) / 86400))
                msg = f"Offline Grace Period: {days_left} day(s) remaining without internet."
                self.current_state = LicenseState(
                    is_valid=True,
                    status_code="ACTIVE_OFFLINE",
                    message=msg,
                    license_key=key,
                    device_id=self.device_id,
                    customer_name=local_data.get("customer_name", ""),
                    customer_email=local_data.get("customer_email", ""),
                    customer_phone=local_data.get("customer_phone", ""),
                    expires_at=local_data.get("expires_at"),
                    last_verified_at=last_verified_str,
                    offline_days_remaining=days_left,
                    signature=local_data.get("signature"),
                )
                return True, msg

        self.current_state = LicenseState(
            is_valid=False,
            status_code="OFFLINE_EXPIRED",
            message="30-Day Offline Grace Period has expired. Please connect to internet to verify license.",
            license_key=key,
            device_id=self.device_id,
        )
        return False, "Offline grace period expired"

    def heartbeat(self) -> Tuple[bool, str]:
        """
        Runtime Heartbeat (POST /api/v1/license/heartbeat)
        Background check every 4 hours. Immediately locks UI if revoked or expired.
        """
        local_data = self.load_local_license()
        if getattr(self, "_tampered_detected", False):
            self.current_state = LicenseState(
                is_valid=False,
                status_code="NEEDS_ACTIVATION",
                message="License file corrupted or tampered. Activation required.",
                device_id=self.device_id,
            )
            return False, "License corrupted"

        if not local_data:
            is_trial_active, days_left, trial_msg = self.evaluate_trial()
            if is_trial_active:
                self.current_state = LicenseState(
                    is_valid=True,
                    status_code="TRIAL",
                    message=trial_msg,
                    device_id=self.device_id,
                    customer_name=f"Trial Workstation ({days_left}d left)",
                    offline_days_remaining=days_left,
                )
                return True, trial_msg
            else:
                self.current_state = LicenseState(
                    is_valid=False,
                    status_code="TRIAL_EXPIRED",
                    message="30-Day Free Trial has expired. Workstation license required.",
                    device_id=self.device_id,
                )
                return False, "Trial expired"

        key = local_data.get("license_key", "")
        url = f"{self.server_url}/api/v1/license/heartbeat"
        payload = {
            "license_key": key,
            "device_id": self.device_id,
        }

        try:
            resp = self.session.post(url, json=payload, timeout=10)
            data = resp.json() if resp.text else {}
        except Exception as e:
            # Network failure during heartbeat: fallback to offline grace period
            logger.info("Heartbeat network timeout (%s), performing offline grace check", e)
            return self.verify_license()

        if resp.status_code == 200 and data.get("success"):
            is_active = data.get("is_active", False)
            is_expired = data.get("is_expired", False)

            if not is_active or is_expired:
                msg = "License revoked or expired by administrator."
                self.current_state = LicenseState(
                    is_valid=False,
                    status_code="EXPIRED" if is_expired else "REVOKED",
                    message=msg,
                    license_key=key,
                    device_id=self.device_id,
                )
                return False, msg

            # Update local record with latest server verification
            now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
            local_data["expires_at"] = data.get("expires_at") or local_data.get("expires_at")
            local_data["server_time"] = data.get("server_time") or now_iso
            local_data["signature"] = data.get("signature") or local_data.get("signature")
            local_data["last_verified_at"] = now_iso
            self.save_local_license(local_data)

            self.current_state = LicenseState(
                is_valid=True,
                status_code=data.get("status_code", "ACTIVE"),
                message="Heartbeat verified",
                license_key=key,
                device_id=self.device_id,
                customer_name=local_data.get("customer_name", ""),
                customer_email=local_data.get("customer_email", ""),
                customer_phone=local_data.get("customer_phone", ""),
                expires_at=local_data.get("expires_at"),
                last_verified_at=now_iso,
                signature=local_data.get("signature"),
            )
            return True, "Heartbeat OK"
        elif resp.status_code == 401:
            logger.warning("Heartbeat returned HTTP 401 (Unauthorized). Skipping revocation; checking offline grace.")
            return self.verify_license()
        else:
            msg = data.get("message", "License validation failed on heartbeat")
            self.current_state = LicenseState(
                is_valid=False,
                status_code="REVOKED",
                message=msg,
                license_key=key,
                device_id=self.device_id,
            )
            return False, msg

    # -------------------------------------------------------------
    # Client Registration & Inquiry (openapi.json)
    # -------------------------------------------------------------

    def register_client_profile(
        self,
        name: str,
        email: str,
        phone: str,
        address: str = "",
    ) -> Tuple[bool, str]:
        """
        Client Registration (POST /api/v1/client/profile)
        Creates the Customer profile so an administrator can generate and deliver
        a license key. Public machine-to-machine endpoint: no admin credentials.
        """
        cust_name = name.strip()
        cust_email = email.strip()
        cust_phone = phone.strip()

        # ClientProfileIn schema validation
        if len(cust_name) < 2:
            return False, "Full Name must be at least 2 characters"
        if len(cust_email) < 5 or "@" not in cust_email:
            return False, "Valid email address is mandatory"
        if len(cust_phone) < 6:
            return False, "Contact phone number must be at least 6 digits"

        payload: Dict[str, Any] = {
            "name": cust_name,
            "email": cust_email,
            "phone": cust_phone,
            "address": address.strip(),
            "device_id": self.device_id,
        }

        url = f"{self.server_url}/api/v1/client/profile"
        try:
            resp = self.session.post(url, json=payload, timeout=12)
            data = resp.json() if resp.text else {}
        except Exception as e:
            logger.error("Client profile registration failed: %s", e)
            return False, f"Server connection failed: {str(e)}"

        success = bool(data.get("success")) and resp.status_code == 201
        if not success:
            msg = data.get("message") or f"Registration rejected (HTTP {resp.status_code})"
            logger.warning("Client profile registration rejected: %s", msg)
            return False, msg
        return True, data.get("message") or "Profile registered. Wait for an administrator to generate your license key."

    def query_client_status(self, query: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Client Status Inquiry (GET /api/v1/client/status?query=...)
        Looks up registration and license status by device ID, email, or phone:
        PENDING_LICENSE / ACTIVE / UNBOUND / EXPIRED.
        Returns: (success, message, payload)
        """
        q = (query or "").strip()
        if not q:
            return False, "Provide an email address, phone number or device ID", {}

        url = f"{self.server_url}/api/v1/client/status"
        try:
            resp = self.session.get(url, params={"query": q}, timeout=10)
            data = resp.json() if resp.text else {}
        except Exception as e:
            logger.error("Client status inquiry failed: %s", e)
            return False, f"Server connection failed: {str(e)}", {}

        if not isinstance(data, dict):
            return False, f"Status inquiry failed (HTTP {resp.status_code})", {}

        success = bool(data.get("success"))
        if not success:
            msg = data.get("message") or f"Status inquiry failed (HTTP {resp.status_code})"
            return False, msg, data

        status_code = str(data.get("status_code") or "").upper()
        msg = data.get("message") or f"Status: {status_code}"
        return True, msg, data

    def query_status_remote(self, license_key: str) -> Optional[Dict[str, Any]]:
        """
        Administrative & Diagnostic Status Inquiry (GET /api/v1/license/status/{license_key})
        Public machine-to-machine endpoint: no administrator credentials required.
        """
        url = f"{self.server_url}/api/v1/license/status/{license_key.strip()}"
        try:
            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            logger.error("Failed to query status remotely: %s", e)
        return None


# Global singleton instance
license_manager = LicenseManager()
