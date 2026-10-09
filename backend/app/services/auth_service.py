import secrets
import hashlib
import hmac
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.config import settings
from app.models.user import User, OTPRecord, SessionRecord

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class AuthService:
    def __init__(self):
        self.secret_key = settings.SECRET_KEY.encode("utf-8")

    def _hash_otp(self, email: str, otp: str) -> str:
        """Create a keyed HMAC hash of the OTP to prevent plaintext storage."""
        message = f"{email.lower().strip()}:{otp.strip()}".encode("utf-8")
        return hmac.new(self.secret_key, message, hashlib.sha256).hexdigest()

    def generate_otp(self) -> str:
        """Generate a cryptographically secure 6-digit OTP."""
        # 100000 to 999999 inclusive
        num = secrets.randbelow(900000) + 100000
        return str(num)

    def send_smtp_email(self, to_email: str, otp: str) -> bool:
        """Send OTP email via SMTP if credentials are configured."""
        if not settings.SMTP_HOST or not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"Your Qoneqt Login Code: {otp}"
            msg["From"] = settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME
            msg["To"] = to_email

            text_content = (
                f"Welcome to Qoneqt AI Content Studio!\n\n"
                f"Your 6-digit login verification code is: {otp}\n\n"
                f"This code will expire in {settings.OTP_TTL_SECONDS // 60} minutes.\n"
                f"If you did not request this code, please ignore this email."
            )
            html_content = f"""
            <div style="font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; max-width: 520px; margin: 0 auto; padding: 24px; border: 1px solid #e5e7eb; border-radius: 12px; background: #ffffff;">
                <div style="text-align: center; margin-bottom: 24px;">
                    <h2 style="color: #111827; margin: 0; font-size: 22px; font-weight: 800;">Qoneqt AI Content Studio</h2>
                    <p style="color: #6b7280; font-size: 13px; margin: 4px 0 0 0;">From One Idea to a Publish-Ready Video</p>
                </div>
                <div style="background: #f8fafc; border-radius: 8px; padding: 20px; text-align: center; margin-bottom: 20px;">
                    <p style="color: #374151; font-size: 14px; margin: 0 0 12px 0;">Your verification code is:</p>
                    <div style="font-size: 32px; font-weight: 800; letter-spacing: 6px; color: #2563eb; padding: 8px; font-family: monospace;">{otp}</div>
                    <p style="color: #9ca3af; font-size: 12px; margin: 12px 0 0 0;">Expires in {settings.OTP_TTL_SECONDS // 60} minutes • Single-use only</p>
                </div>
                <p style="color: #6b7280; font-size: 12px; line-height: 1.5; margin: 0;">
                    If you did not request this login code, you can safely disregard this message. Never share this code with anyone.
                </p>
            </div>
            """
            msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(msg["From"], [to_email], msg.as_string())
            server.quit()
            return True
        except Exception as e:
            print(f"[AuthService] SMTP delivery error: {e}")
            return False

    def request_otp(self, db: Session, email: str) -> dict:
        """
        Validates rate limiting, creates and stores secure OTP, sends via SMTP or provides demo mode.
        """
        email_clean = email.lower().strip()
        now = utc_now()

        # Check existing active OTP for cooldown
        latest_otp = (
            db.query(OTPRecord)
            .filter(OTPRecord.email == email_clean, OTPRecord.is_used == False)
            .order_by(OTPRecord.created_at.desc())
            .first()
        )

        if latest_otp:
            # Check resend cooldown
            elapsed = (now - latest_otp.created_at.replace(tzinfo=timezone.utc)).total_seconds()
            if elapsed < settings.OTP_RESEND_COOLDOWN_SECONDS:
                remaining = int(settings.OTP_RESEND_COOLDOWN_SECONDS - elapsed)
                return {
                    "success": False,
                    "error": f"Please wait {remaining} seconds before requesting a new code.",
                    "cooldown_remaining": remaining
                }

            # Invalidate previous unused OTPs for this email
            db.query(OTPRecord).filter(
                OTPRecord.email == email_clean,
                OTPRecord.is_used == False
            ).update({"is_used": True})
            db.commit()

        # Generate new 6-digit OTP
        otp_code = self.generate_otp()
        otp_hash = self._hash_otp(email_clean, otp_code)
        expires_at = now + timedelta(seconds=settings.OTP_TTL_SECONDS)

        # Store in database
        otp_record = OTPRecord(
            email=email_clean,
            otp_hash=otp_hash,
            created_at=now,
            expires_at=expires_at,
            attempts=0,
            is_used=False
        )
        db.add(otp_record)
        db.commit()

        # Attempt SMTP delivery
        email_sent = self.send_smtp_email(email_clean, otp_code)

        # Check if development demo mode is active
        is_demo = settings.OTP_DEMO_MODE or (not email_sent and not settings.SMTP_HOST)

        response_data = {
            "success": True,
            "message": "Verification code sent to your email." if email_sent else "Verification code generated.",
            "email": email_clean,
            "cooldown_seconds": settings.OTP_RESEND_COOLDOWN_SECONDS,
            "expires_in_seconds": settings.OTP_TTL_SECONDS,
            "is_demo_mode": is_demo,
            "dev_otp": otp_code if is_demo else None,
            "demo_note": "Development OTP Demo Mode active: SMTP not configured. Use the provided demo code for local verification." if (is_demo and not email_sent) else None
        }

        if is_demo:
            print(f"[AuthService DEMO] OTP for {email_clean}: {otp_code}")

        return response_data

    def verify_otp(self, db: Session, email: str, otp_code: str) -> Tuple[bool, str, Optional[User], Optional[str], bool]:
        """
        Validates OTP, enforces attempt limits & expiry, auto-creates user if first login.
        Returns: (success, message, user, session_token, is_new_user)
        """
        email_clean = email.lower().strip()
        now = utc_now()

        # Find latest active OTP
        otp_record = (
            db.query(OTPRecord)
            .filter(OTPRecord.email == email_clean, OTPRecord.is_used == False)
            .order_by(OTPRecord.created_at.desc())
            .first()
        )

        if not otp_record:
            return False, "No active verification code found. Please request a new one.", None, None, False

        # Check expiry
        record_expiry = otp_record.expires_at
        if record_expiry.tzinfo is None:
            record_expiry = record_expiry.replace(tzinfo=timezone.utc)

        if now > record_expiry:
            otp_record.is_used = True
            db.commit()
            return False, "Verification code has expired. Please request a new code.", None, None, False

        # Check attempt limits
        if otp_record.attempts >= settings.OTP_MAX_ATTEMPTS:
            otp_record.is_used = True
            db.commit()
            return False, f"Maximum verification attempts ({settings.OTP_MAX_ATTEMPTS}) exceeded. Please request a new code.", None, None, False

        # Compare hash securely
        expected_hash = self._hash_otp(email_clean, otp_code)
        if not hmac.compare_digest(otp_record.otp_hash, expected_hash):
            otp_record.attempts += 1
            db.commit()
            remaining_attempts = max(0, settings.OTP_MAX_ATTEMPTS - otp_record.attempts)
            return False, f"Invalid verification code. {remaining_attempts} attempt(s) remaining.", None, None, False

        # Success! Mark OTP as used
        otp_record.is_used = True
        
        # Check or create user
        user = db.query(User).filter(User.email == email_clean).first()
        is_new_user = False
        if not user:
            user = User(
                email=email_clean,
                created_at=now,
                last_login_at=now,
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            is_new_user = True
        else:
            user.last_login_at = now
            db.commit()
            db.refresh(user)

        # Create session
        session_token = secrets.token_urlsafe(32)
        session_expiry = now + timedelta(hours=settings.SESSION_TTL_HOURS)
        session_record = SessionRecord(
            session_token=session_token,
            user_id=user.id,
            created_at=now,
            expires_at=session_expiry,
            is_revoked=False
        )
        db.add(session_record)
        db.commit()

        return True, "Login successful.", user, session_token, is_new_user

    def validate_session(self, db: Session, session_token: str) -> Optional[User]:
        """Validates session token and returns active User if valid."""
        if not session_token:
            return None

        now = utc_now()
        session = (
            db.query(SessionRecord)
            .filter(
                SessionRecord.session_token == session_token,
                SessionRecord.is_revoked == False
            )
            .first()
        )

        if not session:
            return None

        sess_expiry = session.expires_at
        if sess_expiry.tzinfo is None:
            sess_expiry = sess_expiry.replace(tzinfo=timezone.utc)

        if now > sess_expiry:
            session.is_revoked = True
            db.commit()
            return None

        user = db.query(User).filter(User.id == session.user_id, User.is_active == True).first()
        return user

    def logout_session(self, db: Session, session_token: str) -> bool:
        """Revokes the given session token."""
        if not session_token:
            return False

        session = db.query(SessionRecord).filter(SessionRecord.session_token == session_token).first()
        if session:
            session.is_revoked = True
            db.commit()
            return True
        return False

auth_service = AuthService()
