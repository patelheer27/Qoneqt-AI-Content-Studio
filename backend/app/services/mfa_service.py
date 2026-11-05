import secrets
import hashlib
import hmac
import io
import time
import base64
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
import pyotp
import qrcode
from cryptography.fernet import Fernet, InvalidToken

from app.config import settings
from app.models.user import User, RecoveryCode, SessionRecord
from app.models.security import SecurityLog

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class MFAService:
    def __init__(self):
        self.secret_key = settings.SECRET_KEY.encode("utf-8")
        
        # Initialize Fernet encryption for TOTP secrets at rest
        # Securely derives a standard 32-byte urlsafe base64 key from system secrets
        if settings.TOTP_ENCRYPTION_KEY:
            try:
                self.fernet = Fernet(settings.TOTP_ENCRYPTION_KEY.encode("utf-8"))
            except Exception:
                derived = base64.urlsafe_b64encode(hashlib.sha256((settings.SECRET_KEY + "_totp_fernet").encode()).digest())
                self.fernet = Fernet(derived)
        else:
            derived = base64.urlsafe_b64encode(hashlib.sha256((settings.SECRET_KEY + "_totp_fernet").encode()).digest())
            self.fernet = Fernet(derived)

    # --------------------------------------------------------------------------
    # Cryptographic at-rest encryption for TOTP secrets (Py_SecureVault concept)
    # --------------------------------------------------------------------------
    def encrypt_secret(self, secret: str) -> str:
        """Encrypt base32 TOTP secret before storing in SQLite database."""
        return self.fernet.encrypt(secret.strip().encode("utf-8")).decode("utf-8")

    def decrypt_secret(self, encrypted_secret: str) -> Optional[str]:
        """Decrypt base32 TOTP secret from SQLite database."""
        try:
            return self.fernet.decrypt(encrypted_secret.encode("utf-8")).decode("utf-8")
        except (InvalidToken, Exception) as e:
            print(f"[MFAService] Decryption failed: {e}")
            return None

    def _hash_recovery_code(self, code: str) -> str:
        """Create a salted HMAC-SHA256 hash of a recovery code."""
        cleaned = code.replace("-", "").replace(" ", "").strip().upper()
        return hmac.new(self.secret_key, cleaned.encode("utf-8"), hashlib.sha256).hexdigest()

    # --------------------------------------------------------------------------
    # Enrollment & Key Provisioning
    # --------------------------------------------------------------------------
    def generate_secret(self) -> str:
        """Generate a cryptographically random 160-bit (32 character) Base32 secret."""
        return pyotp.random_base32()

    def format_pretty_secret(self, secret: str) -> str:
        """Format 32-char secret into human-readable 4-character chunks: XXXX XXXX..."""
        clean = secret.replace(" ", "").strip().upper()
        return " ".join(clean[i:i + 4] for i in range(0, len(clean), 4))

    def generate_provisioning_uri(self, secret: str, email: str) -> str:
        """Generate standard RFC 6238 otpauth:// URI for authenticator apps."""
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=email, issuer_name=settings.TOTP_ISSUER)

    def generate_qr_data_uri(self, uri: str) -> str:
        """Generate Base64 PNG Data URI of the QR code for instant display."""
        img = qrcode.make(uri, box_size=6, border=2)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("utf-8")

    def setup_mfa(self, db: Session, user: User) -> dict:
        """
        Initializes MFA setup for user by generating and storing an encrypted secret.
        Returns QR code Data URI, pretty secret key, and provisioning metadata.
        """
        # Generate new base32 secret
        raw_secret = self.generate_secret()
        enc_secret = self.encrypt_secret(raw_secret)

        user.totp_secret_enc = enc_secret
        db.commit()

        uri = self.generate_provisioning_uri(raw_secret, user.email)
        qr_data_uri = self.generate_qr_data_uri(uri)
        pretty = self.format_pretty_secret(raw_secret)

        # Log audit event
        self._log_security_event(db, user.id, "mfa_setup_initiated", {
            "email": user.email,
            "issuer": settings.TOTP_ISSUER
        })

        return {
            "secret": pretty,
            "raw_secret": raw_secret,
            "qr_code": qr_data_uri,
            "issuer": settings.TOTP_ISSUER,
            "email": user.email
        }

    # --------------------------------------------------------------------------
    # Verification & Replay Protection (Py_SecureVault concept)
    # --------------------------------------------------------------------------
    def verify_totp(self, secret: str, code: str, last_step: Optional[int]) -> Tuple[bool, Optional[int], str]:
        """
        Verifies a 6-digit TOTP code against the secret.
        Accepts +/- 1 time step (30 seconds) for clock drift.
        Enforces replay protection: rejects if step <= last_step.
        Returns: (success, step, error_reason)
        """
        code = (code or "").replace(" ", "").strip()
        if len(code) != 6 or not code.isdigit():
            return False, None, "Code must be a 6-digit numeric string."

        totp = pyotp.TOTP(secret)
        current_step = int(time.time()) // 30

        # Check current and adjacent steps for clock drift tolerance (+/- 30 seconds)
        for step in (current_step - 1, current_step, current_step + 1):
            if hmac.compare_digest(totp.at(step * 30), code):
                if last_step is not None and step <= last_step:
                    return False, None, "Code was already used. Please wait for the next 30-second code."
                return True, step, "ok"

        return False, None, "Invalid verification code. Please check your authenticator clock."

    def confirm_mfa_setup(self, db: Session, user: User, code: str) -> Tuple[bool, str, List[str]]:
        """
        Verifies initial TOTP code to confirm enrollment, sets mfa_enabled=True,
        and generates 8 single-use recovery codes.
        """
        if user.mfa_enabled:
            return False, "Multi-Factor Authentication is already active for this account.", []

        if not user.totp_secret_enc:
            return False, "MFA setup was not initiated. Please request setup first.", []

        raw_secret = self.decrypt_secret(user.totp_secret_enc)
        if not raw_secret:
            return False, "Failed to decrypt TOTP secret. Please try setup again.", []

        success, step, reason = self.verify_totp(raw_secret, code, user.last_totp_step)
        if not success:
            return False, reason, []

        # Mark MFA enabled and record last time step
        user.mfa_enabled = True
        user.last_totp_step = step
        user.failed_attempts = 0
        user.locked_until = None
        db.commit()

        # Generate 8 single-use recovery codes
        recovery_codes = self.generate_recovery_codes(db, user.id)

        self._log_security_event(db, user.id, "mfa_enrolled", {
            "email": user.email,
            "recovery_codes_count": len(recovery_codes)
        })

        return True, "Multi-Factor Authentication enabled successfully.", recovery_codes

    # --------------------------------------------------------------------------
    # Single-Use Recovery Codes (Py_SecureVault concept)
    # --------------------------------------------------------------------------
    def generate_recovery_codes(self, db: Session, user_id: int, count: int = 8) -> List[str]:
        """
        Generates N single-use recovery codes in XXXXX-XXXXX format.
        Hashes each code with salted HMAC-SHA256 before storing in DB.
        Returns the plaintext list to display once to the user.
        """
        # Invalidate existing unused recovery codes
        db.query(RecoveryCode).filter(RecoveryCode.user_id == user_id).delete()
        db.commit()

        plain_codes = []
        for _ in range(count):
            token = secrets.token_hex(5).upper() # 10 hex characters
            formatted_code = f"{token[:5]}-{token[5:]}"
            plain_codes.append(formatted_code)

            code_hash = self._hash_recovery_code(formatted_code)
            rec = RecoveryCode(
                user_id=user_id,
                code_hash=code_hash,
                created_at=utc_now(),
                used_at=None
            )
            db.add(rec)

        db.commit()
        return plain_codes

    def use_recovery_code(self, db: Session, user_id: int, input_code: str) -> bool:
        """
        Validates and burns a single-use recovery code.
        Returns True if code is valid and unused; marks used_at.
        """
        if not input_code:
            return False

        expected_hash = self._hash_recovery_code(input_code)
        
        # Find unused codes for user
        active_codes = (
            db.query(RecoveryCode)
            .filter(RecoveryCode.user_id == user_id, RecoveryCode.used_at == None)
            .all()
        )

        for rec in active_codes:
            if hmac.compare_digest(rec.code_hash, expected_hash):
                rec.used_at = utc_now()
                db.commit()
                self._log_security_event(db, user_id, "mfa_recovery_code_used", {
                    "code_id": rec.id
                })
                return True

        return False

    def count_remaining_recovery_codes(self, db: Session, user_id: int) -> int:
        """Count active unused recovery codes for a user."""
        return (
            db.query(RecoveryCode)
            .filter(RecoveryCode.user_id == user_id, RecoveryCode.used_at == None)
            .count()
        )

    # --------------------------------------------------------------------------
    # Account Lockout & Brute-Force Defense (Py_SecureVault concept)
    # --------------------------------------------------------------------------
    def is_locked(self, user: User) -> Tuple[bool, int]:
        """
        Checks if account is locked out from too many failed attempts.
        Returns (is_locked, remaining_minutes).
        """
        if not user.locked_until:
            return False, 0

        locked_until = user.locked_until
        if locked_until.tzinfo is None:
            locked_until = locked_until.replace(tzinfo=timezone.utc)

        now = utc_now()
        if locked_until > now:
            remaining_seconds = (locked_until - now).total_seconds()
            mins = max(1, int(remaining_seconds // 60) + 1)
            return True, mins

        # Lockout expired
        return False, 0

    def register_failure(self, db: Session, user: User, stage: str = "MFA") -> Tuple[bool, int]:
        """
        Increments failed attempt counter.
        Locks account for MFA_LOCKOUT_MINUTES if max attempts reached.
        """
        user.failed_attempts = (user.failed_attempts or 0) + 1
        is_locked_now = False
        lockout_mins = 0

        if user.failed_attempts >= settings.MFA_MAX_FAILED_ATTEMPTS:
            user.locked_until = utc_now() + timedelta(minutes=settings.MFA_LOCKOUT_MINUTES)
            user.failed_attempts = 0
            is_locked_now = True
            lockout_mins = settings.MFA_LOCKOUT_MINUTES
            self._log_security_event(db, user.id, "mfa_account_locked", {
                "stage": stage,
                "lockout_minutes": lockout_mins,
                "email": user.email
            })

        db.commit()
        return is_locked_now, lockout_mins

    def reset_failures(self, db: Session, user: User):
        """Reset failed attempt counters upon successful authentication."""
        user.failed_attempts = 0
        user.locked_until = None
        db.commit()

    # --------------------------------------------------------------------------
    # Pending MFA Login Tokens (Factor 1 -> Factor 2 handoff)
    # --------------------------------------------------------------------------
    def create_pending_mfa_token(self, user_id: int, email: str) -> str:
        """
        Creates a signed, tamper-proof temporary token valid for 5 minutes.
        Issued when Factor 1 (OTP) succeeds and Factor 2 (MFA) is required.
        """
        expiry = int(time.time()) + settings.MFA_PENDING_TTL_SECONDS
        nonce = secrets.token_hex(16)
        payload = f"{user_id}:{email}:{expiry}:{nonce}"
        signature = hmac.new(self.secret_key, payload.encode("utf-8"), hashlib.sha256).hexdigest()
        raw_token = f"{payload}:{signature}"
        return base64.urlsafe_b64encode(raw_token.encode("utf-8")).decode("utf-8")

    def verify_pending_mfa_token(self, db: Session, token: str) -> Tuple[bool, Optional[User], str]:
        """
        Validates signed pending MFA token.
        Ensures signature integrity and expiry window.
        """
        if not token:
            return False, None, "MFA token is required."

        try:
            raw = base64.urlsafe_b64decode(token.encode("utf-8")).decode("utf-8")
            parts = raw.split(":")
            if len(parts) != 5:
                return False, None, "Malformed MFA token."

            user_id_str, email, expiry_str, nonce, signature = parts
            user_id = int(user_id_str)
            expiry = int(expiry_str)

            # Check expiration
            if time.time() > expiry:
                return False, None, "MFA authentication session has expired. Please log in again."

            # Verify HMAC signature
            payload = f"{user_id}:{email}:{expiry}:{nonce}"
            expected_sig = hmac.new(self.secret_key, payload.encode("utf-8"), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(signature, expected_sig):
                return False, None, "Invalid or tampered MFA token."

            user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
            if not user:
                return False, None, "User account not found."

            return True, user, "ok"
        except Exception as e:
            return False, None, f"Token validation error: {str(e)}"

    # --------------------------------------------------------------------------
    # Complete MFA Verification during Login
    # --------------------------------------------------------------------------
    def verify_login_mfa(
        self,
        db: Session,
        mfa_token: str,
        code: str,
        method: str = "totp"
    ) -> Tuple[bool, str, Optional[User], Optional[str]]:
        """
        Verifies Factor 2 (TOTP code or Recovery Code) using the pending MFA token.
        Upon success: clears failures, issues full session token, logs success.
        Upon failure: increments failed attempts and enforces account lockout.
        Returns: (success, message, user, session_token)
        """
        # Validate pending token
        valid, user, err = self.verify_pending_mfa_token(db, mfa_token)
        if not valid or not user:
            return False, err, None, None

        # Check account lockout
        locked, mins = self.is_locked(user)
        if locked:
            return False, f"Account temporarily locked after too many failed attempts. Try again in ~{mins} min.", None, None

        ok = False
        detail = ""

        if method == "recovery":
            ok = self.use_recovery_code(db, user.id, code)
            detail = "recovery code used"
            if not ok:
                err_msg = "Invalid or already-used recovery code."
        else: # Default: TOTP RFC 6238
            if not user.totp_secret_enc:
                return False, "MFA is not configured for this account.", None, None

            raw_secret = self.decrypt_secret(user.totp_secret_enc)
            if not raw_secret:
                return False, "Internal error reading MFA configuration.", None, None

            success, step, reason = self.verify_totp(raw_secret, code, user.last_totp_step)
            if success:
                user.last_totp_step = step
                db.commit()
                ok = True
                detail = "TOTP code verified (replay checked)"
            else:
                err_msg = reason

        if ok:
            # Authentication successful! Reset brute force counters
            self.reset_failures(db, user)
            user.last_login_at = utc_now()
            db.commit()

            # Issue permanent session token
            session_token = secrets.token_urlsafe(32)
            session_expiry = utc_now() + timedelta(hours=settings.SESSION_TTL_HOURS)
            session_record = SessionRecord(
                session_token=session_token,
                user_id=user.id,
                created_at=utc_now(),
                expires_at=session_expiry,
                is_revoked=False
            )
            db.add(session_record)
            db.commit()

            self._log_security_event(db, user.id, "mfa_login_success", {
                "method": method,
                "detail": detail
            })

            return True, "Multi-Factor Authentication verified successfully.", user, session_token

        # Failure: register attempt and check for lockout
        locked_now, lock_mins = self.register_failure(db, user, stage="MFA")
        self._log_security_event(db, user.id, "mfa_login_failed", {
            "method": method,
            "reason": err_msg,
            "failed_attempts": user.failed_attempts,
            "locked_out": locked_now
        })

        if locked_now:
            return False, f"Account temporarily locked after {settings.MFA_MAX_FAILED_ATTEMPTS} failed attempts. Try again in {lock_mins} minutes.", None, None

        remaining = max(0, settings.MFA_MAX_FAILED_ATTEMPTS - user.failed_attempts)
        return False, f"{err_msg} ({remaining} attempts remaining before account lockout)", None, None

    # --------------------------------------------------------------------------
    # Disable MFA
    # --------------------------------------------------------------------------
    def disable_mfa(self, db: Session, user: User, code: str, method: str = "totp") -> Tuple[bool, str]:
        """
        Disables MFA for an authenticated user after validating their TOTP or recovery code.
        """
        if not user.mfa_enabled:
            return False, "MFA is not currently enabled for this account."

        # Validate code before allowing disable
        verified = False
        if method == "recovery":
            verified = self.use_recovery_code(db, user.id, code)
        else:
            raw_secret = self.decrypt_secret(user.totp_secret_enc) if user.totp_secret_enc else None
            if raw_secret:
                success, _, _ = self.verify_totp(raw_secret, code, None)
                verified = success

        if not verified:
            return False, "Invalid authentication code. MFA was not disabled."

        user.mfa_enabled = False
        user.totp_secret_enc = None
        user.last_totp_step = None
        user.failed_attempts = 0
        user.locked_until = None

        # Delete remaining recovery codes
        db.query(RecoveryCode).filter(RecoveryCode.user_id == user.id).delete()
        db.commit()

        self._log_security_event(db, user.id, "mfa_disabled", {
            "email": user.email
        })

        return True, "Multi-Factor Authentication has been disabled."

    # --------------------------------------------------------------------------
    # Internal Security Event Logger
    # --------------------------------------------------------------------------
    def _log_security_event(self, db: Session, user_id: Optional[int], event_type: str, details: dict):
        try:
            log_entry = SecurityLog(
                user_id=user_id,
                event_type=event_type,
                details=details,
                created_at=utc_now()
            )
            db.add(log_entry)
            db.commit()
        except Exception as e:
            print(f"[MFAService] Audit log error: {e}")

mfa_service = MFAService()
