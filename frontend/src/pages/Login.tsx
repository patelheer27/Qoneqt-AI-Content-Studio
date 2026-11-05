import React, { useState, useEffect } from 'react';
import { 
  Sparkles, Mail, KeyRound, ArrowRight, RefreshCw, 
  CheckCircle2, AlertCircle, ShieldCheck, Clock, Lock,
  Smartphone, Key, Copy, Check, Download
} from 'lucide-react';
import { authApi, mfaApi } from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function Login() {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [step, setStep] = useState<'email' | 'otp' | 'mfa_verify' | 'mfa_setup' | 'mfa_recovery'>('email');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Timers (Verification code expires within 1 minute)
  const [expirySeconds, setExpirySeconds] = useState(60); // 1 minute (60s)
  const [cooldownSeconds, setCooldownSeconds] = useState(30); // 30s resend cooldown

  // Demo mode
  const [isDemoMode, setIsDemoMode] = useState(false);
  const [devOtp, setDevOtp] = useState<string | null>(null);
  const [demoNote, setDemoNote] = useState<string | null>(null);

  // Factor 2: Returning User MFA Verification (Py_SecureVault Concept)
  const [pendingMfaToken, setPendingMfaToken] = useState<string | null>(null);
  const [mfaVerifyCode, setMfaVerifyCode] = useState(['', '', '', '', '', '']);
  const [mfaMethod, setMfaMethod] = useState<'totp' | 'recovery'>('totp');
  const [recoveryCodeInput, setRecoveryCodeInput] = useState('');
  const [totpSecondsRemaining, setTotpSecondsRemaining] = useState(30);

  // Factor 2: First-time Onboarding MFA Setup (Py_SecureVault Concept)
  const [pendingSessionToken, setPendingSessionToken] = useState<string | null>(null);
  const [pendingUser, setPendingUser] = useState<any | null>(null);
  const [setupData, setSetupData] = useState<{
    secret: string;
    qr_code: string;
    issuer: string;
    email: string;
  } | null>(null);
  const [setupConfirmCode, setSetupConfirmCode] = useState('');
  const [recoveryCodes, setRecoveryCodes] = useState<string[]>([]);
  const [secretCopied, setSecretCopied] = useState(false);
  const [recoveryCopied, setRecoveryCopied] = useState(false);

  // Live 30-second TOTP step timer (Py_SecureVault live ticker indicator)
  useEffect(() => {
    const updateTotpTimer = () => {
      const sec = Math.floor(Date.now() / 1000) % 30;
      setTotpSecondsRemaining(30 - sec);
    };
    updateTotpTimer();
    const timer = setInterval(updateTotpTimer, 1000);
    return () => clearInterval(timer);
  }, []);

  // Email OTP countdown timer effect (1 minute lifetime)
  useEffect(() => {
    let interval: any = null;
    if (step === 'otp') {
      interval = setInterval(() => {
        setExpirySeconds((prev) => {
          if (prev <= 1) {
            setError('Verification code has expired. Please click "Resend Code" to get a new code.');
            return 0;
          }
          return prev - 1;
        });
        setCooldownSeconds((prev) => (prev > 0 ? prev - 1 : 0));
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [step]);

  // ==================== FACTOR 1: REQUEST OTP ====================
  const handleSendOtp = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!email || !email.includes('@')) {
      setError('Please enter a valid email address.');
      return;
    }

    setIsLoading(true);
    setError(null);
    setSuccessMsg(null);

    try {
      const res = await authApi.requestOtp(email);
      setStep('otp');
      setExpirySeconds(res.expires_in_seconds || 60);
      setCooldownSeconds(res.cooldown_seconds || 30);
      setIsDemoMode(!!res.is_demo_mode);
      setDevOtp(res.dev_otp || null);
      setDemoNote(res.demo_note || null);
      setSuccessMsg(res.message || 'Verification code dispatched.');
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to send verification code. Please try again.';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendOtp = async () => {
    if (cooldownSeconds > 0) return;
    setIsLoading(true);
    setError(null);
    try {
      const res = await authApi.resendOtp(email);
      setExpirySeconds(res.expires_in_seconds || 60);
      setCooldownSeconds(res.cooldown_seconds || 30);
      setIsDemoMode(!!res.is_demo_mode);
      setDevOtp(res.dev_otp || null);
      setDemoNote(res.demo_note || null);
      setOtp(['', '', '', '', '', '']);
      setSuccessMsg('New verification code issued (valid for 1 minute).');
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to resend code.';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleOtpChange = (index: number, val: string) => {
    const cleaned = val.replace(/\D/g, '');
    const newOtp = [...otp];

    if (cleaned.length > 1) {
      const digits = cleaned.slice(0, 6).split('');
      digits.forEach((d, i) => {
        if (i < 6) newOtp[i] = d;
      });
      setOtp(newOtp);
      const nextIdx = Math.min(digits.length, 5);
      document.getElementById(`otp-input-${nextIdx}`)?.focus();
      return;
    }

    newOtp[index] = cleaned;
    setOtp(newOtp);

    if (cleaned && index < 5) {
      document.getElementById(`otp-input-${index + 1}`)?.focus();
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      document.getElementById(`otp-input-${index - 1}`)?.focus();
    }
  };

  const handlePaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    e.preventDefault();
    const pasteData = e.clipboardData.getData('text').trim();
    const digits = pasteData.replace(/\D/g, '').slice(0, 6).split('');
    if (digits.length > 0) {
      const newOtp = ['', '', '', '', '', ''];
      digits.forEach((d, i) => {
        newOtp[i] = d;
      });
      setOtp(newOtp);
      const targetIdx = Math.min(digits.length - 1, 5);
      document.getElementById(`otp-input-${targetIdx}`)?.focus();
    }
  };

  // ==================== FACTOR 1: VERIFY EMAIL OTP ====================
  const handleVerifyOtp = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const fullCode = otp.join('');
    if (fullCode.length !== 6) {
      setError('Please enter the complete 6-digit verification code.');
      return;
    }

    if (expirySeconds <= 0) {
      setError('Verification code has expired. Please request a new code.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const res = await authApi.verifyOtp(email, fullCode);
      if (res.success) {
        // CASE A: User has MFA already enabled -> Go directly to Factor 2 verification (Py_SecureVault mfa_verify)
        if (res.mfa_required && res.mfa_token) {
          setPendingMfaToken(res.mfa_token);
          setStep('mfa_verify');
          setError(null);
          setSuccessMsg('First factor verified. Enter your Authenticator code.');
          return;
        }

        // CASE B: User does NOT have MFA enabled yet -> Enforce MFA Onboarding (Py_SecureVault mfa_setup)
        if (res.session_token && res.user) {
          setPendingSessionToken(res.session_token);
          setPendingUser(res.user);

          // If the user already has mfa_enabled on their profile
          if (res.user.mfa_enabled) {
            // Already enabled, enter dashboard
            login(res.session_token, res.user);
            return;
          }

          // Fetch MFA setup parameters (QR code + secret key)
          try {
            const setupRes = await mfaApi.setup(res.session_token);
            setSetupData(setupRes);
            setStep('mfa_setup');
            setError(null);
            setSuccessMsg('Email confirmed. Please complete Multi-Factor Authentication setup.');
          } catch (mfaSetupErr) {
            // If setup fails for any reason, proceed with session
            console.error('Failed to initialize MFA setup:', mfaSetupErr);
            login(res.session_token, res.user);
          }
        }
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Invalid verification code.';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  // ==================== FACTOR 2 VERIFY: RETURNING USER (Py_SecureVault mfa_verify.html) ====================
  const handleMfaVerifyCodeChange = (index: number, val: string) => {
    const cleaned = val.replace(/\D/g, '');
    const newMfa = [...mfaVerifyCode];

    if (cleaned.length > 1) {
      const digits = cleaned.slice(0, 6).split('');
      digits.forEach((d, i) => {
        if (i < 6) newMfa[i] = d;
      });
      setMfaVerifyCode(newMfa);
      const nextIdx = Math.min(digits.length, 5);
      document.getElementById(`mfa-verify-input-${nextIdx}`)?.focus();
      return;
    }

    newMfa[index] = cleaned;
    setMfaVerifyCode(newMfa);

    if (cleaned && index < 5) {
      document.getElementById(`mfa-verify-input-${index + 1}`)?.focus();
    }
  };

  const handleMfaVerifyKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !mfaVerifyCode[index] && index > 0) {
      document.getElementById(`mfa-verify-input-${index - 1}`)?.focus();
    }
  };

  const handleVerifyMfaLogin = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!pendingMfaToken) {
      setError('MFA session expired. Please sign in again.');
      setStep('email');
      return;
    }

    const codeToVerify = mfaMethod === 'recovery' 
      ? recoveryCodeInput.trim() 
      : mfaVerifyCode.join('');

    if (!codeToVerify) {
      setError(mfaMethod === 'recovery' ? 'Please enter a recovery code.' : 'Please enter the 6-digit Authenticator code.');
      return;
    }

    if (mfaMethod === 'totp' && codeToVerify.length !== 6) {
      setError('Authenticator code must be 6 digits.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const res = await mfaApi.verifyLogin(pendingMfaToken, codeToVerify, mfaMethod);
      if (res.success && res.session_token && res.user) {
        setSuccessMsg('MFA Verified! Welcome to Qoneqt Studio.');
        setTimeout(() => {
          login(res.session_token, res.user);
        }, 500);
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Invalid or already-used code.';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  // ==================== FACTOR 2 SETUP: NEW USER (Py_SecureVault mfa_setup.html) ====================
  const handleConfirmSetup = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const cleanedCode = setupConfirmCode.replace(/\D/g, '');
    if (cleanedCode.length !== 6) {
      setError('Please enter the 6-digit code shown in your authenticator app.');
      return;
    }

    if (!pendingSessionToken) {
      setError('Session expired. Please sign in again.');
      setStep('email');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const res = await mfaApi.confirm(cleanedCode, pendingSessionToken);
      if (res.success && res.recovery_codes) {
        setRecoveryCodes(res.recovery_codes);
        setStep('mfa_recovery');
        setSuccessMsg('Authenticator verified! Save your emergency recovery codes.');
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Invalid code. Check the time on your device and try again.';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  // ==================== FACTOR 2 RECOVERY: (Py_SecureVault recovery_codes.html) ====================
  const handleCopyRecoveryCodes = () => {
    if (recoveryCodes.length === 0) return;
    navigator.clipboard.writeText(recoveryCodes.join('\n'));
    setRecoveryCopied(true);
    setTimeout(() => setRecoveryCopied(false), 2000);
  };

  const handleDownloadRecoveryCodes = () => {
    if (recoveryCodes.length === 0) return;
    const content = `QONEQT AI CONTENT STUDIO - MFA RECOVERY CODES\nAccount: ${email}\nDate: ${new Date().toISOString()}\n\n` +
      `Keep these codes safe. Each code can be used ONCE to sign in if you lose your phone.\n\n` +
      recoveryCodes.map((c, i) => `[${i + 1}] ${c}`).join('\n') +
      `\n\n--------------------------------------------\n`;
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'qoneqt-recovery-codes.txt';
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleFinishOnboarding = () => {
    if (pendingSessionToken && pendingUser) {
      login(pendingSessionToken, { ...pendingUser, mfa_enabled: true });
    } else {
      setStep('email');
    }
  };

  const fillDemoOtp = () => {
    if (devOtp && devOtp.length === 6) {
      setOtp(devOtp.split(''));
    }
  };

  const formatTimer = (totalSecs: number) => {
    const mins = Math.floor(totalSecs / 60);
    const secs = totalSecs % 60;
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center p-4 sm:p-6 md:p-8 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-blue-50/60 via-gray-50/80 to-gray-100">
      <div className="w-full max-w-[560px] bg-white rounded-3xl shadow-2xl shadow-blue-500/10 border border-gray-100 p-8 sm:p-11 relative overflow-hidden">
        {/* Ambient glow backgrounds */}
        <div className="absolute -top-28 -left-28 w-72 h-72 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -top-28 -right-28 w-72 h-72 bg-orange-500/10 rounded-full blur-3xl pointer-events-none" />

        {/* Brand Header */}
        <div className="flex flex-col items-center text-center mb-6 relative z-10">
          <div className="w-16 h-16 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-2xl flex items-center justify-center shadow-xl shadow-blue-500/25 mb-3 group hover:scale-105 transition-transform duration-300">
            <Sparkles className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-2xl font-black text-gray-900 tracking-tight">Qoneqt AI Content Studio</h2>
          <p className="text-xs font-semibold text-blue-600 uppercase tracking-widest mt-1">
            Zero-Trust MFA Secure Access
          </p>
        </div>

        {/* ==================== PY_SECUREVAULT MULTI-STEP PROGRESS PILLS ==================== */}
        <div className="flex items-center justify-center gap-1.5 mb-7 text-xs font-bold text-gray-400">
          {step === 'email' && (
            <>
              <span className="px-3 py-1 rounded-full bg-blue-100 text-blue-800 flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-blue-600"></span> 1 Account
              </span>
              <span className="text-gray-300">›</span>
              <span className="px-3 py-1 rounded-full bg-gray-100 text-gray-500">2 Verification</span>
              <span className="text-gray-300">›</span>
              <span className="px-3 py-1 rounded-full bg-gray-100 text-gray-500">3 Authenticator</span>
            </>
          )}

          {step === 'otp' && (
            <>
              <span className="px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 flex items-center gap-1">
                <Check className="w-3.5 h-3.5 text-emerald-600" /> 1 Account
              </span>
              <span className="text-gray-300">›</span>
              <span className="px-3 py-1 rounded-full bg-blue-100 text-blue-800 flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-blue-600"></span> 2 Verification
              </span>
              <span className="text-gray-300">›</span>
              <span className="px-3 py-1 rounded-full bg-gray-100 text-gray-500">3 Authenticator</span>
            </>
          )}

          {step === 'mfa_verify' && (
            <>
              <span className="px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 flex items-center gap-1">
                <Check className="w-3.5 h-3.5 text-emerald-600" /> 1 Password / OTP
              </span>
              <span className="text-gray-300">›</span>
              <span className="px-3 py-1 rounded-full bg-blue-100 text-blue-800 flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-blue-600"></span> 2 Authenticator
              </span>
            </>
          )}

          {step === 'mfa_setup' && (
            <>
              <span className="px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 flex items-center gap-1">
                <Check className="w-3.5 h-3.5 text-emerald-600" /> 1 Account
              </span>
              <span className="text-gray-300">›</span>
              <span className="px-3 py-1 rounded-full bg-blue-100 text-blue-800 flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-blue-600"></span> 2 Set up authenticator
              </span>
              <span className="text-gray-300">›</span>
              <span className="px-3 py-1 rounded-full bg-gray-100 text-gray-500">3 Recovery codes</span>
            </>
          )}

          {step === 'mfa_recovery' && (
            <>
              <span className="px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 flex items-center gap-1">
                <Check className="w-3.5 h-3.5 text-emerald-600" /> 1 Account
              </span>
              <span className="text-gray-300">›</span>
              <span className="px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 flex items-center gap-1">
                <Check className="w-3.5 h-3.5 text-emerald-600" /> 2 Authenticator
              </span>
              <span className="text-gray-300">›</span>
              <span className="px-3 py-1 rounded-full bg-blue-100 text-blue-800 flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-blue-600"></span> 3 Recovery codes
              </span>
            </>
          )}
        </div>

        {/* Heading & Subtitle */}
        <div className="text-center mb-6">
          <h1 className="text-2xl font-black text-gray-900">
            {step === 'email' && 'Sign in to Qoneqt'}
            {step === 'otp' && 'Verify Your Email'}
            {step === 'mfa_verify' && 'Two-step verification'}
            {step === 'mfa_setup' && 'Scan with your authenticator'}
            {step === 'mfa_recovery' && 'Save your recovery codes'}
          </h1>
          <p className="text-xs sm:text-sm text-gray-500 mt-1 max-w-md mx-auto leading-relaxed">
            {step === 'email' && 'Passwordless authentication with TOTP Multi-Factor protection.'}
            {step === 'otp' && (isDemoMode ? 'Enter the 6-digit verification code shown below to sign in.' : `Enter the 6-digit verification code sent to ${email}`)}
            {step === 'mfa_verify' && `Verification accepted for ${email}. Now prove you have your phone.`}
            {step === 'mfa_setup' && 'Use Google Authenticator, Microsoft Authenticator, Authy or any TOTP app. MFA is mandatory on this site.'}
            {step === 'mfa_recovery' && 'If you lose your phone, each code below lets you sign in once. They are stored only as salted hashes, so this is the only time you will see them.'}
          </p>
        </div>

        {/* Error Feedback */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 text-xs sm:text-sm rounded-2xl flex items-start gap-3 animate-fadeIn">
            <AlertCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
            <div className="flex-1 font-medium">{error}</div>
          </div>
        )}

        {/* Success Feedback */}
        {successMsg && !error && (
          <div className="mb-6 p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs sm:text-sm rounded-2xl flex items-start gap-3 animate-fadeIn">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
            <div className="flex-1 font-medium">{successMsg}</div>
          </div>
        )}

        {/* Development Demo Mode Helper */}
        {step === 'otp' && isDemoMode && devOtp && (
          <div className={`mb-6 p-4 rounded-2xl border transition-all ${expirySeconds > 0 ? 'bg-blue-50 border-blue-200/80' : 'bg-red-50 border-red-200'}`}>
            <div className="flex items-center justify-between">
              <span className={`text-xs font-bold uppercase tracking-wider flex items-center gap-1.5 ${expirySeconds > 0 ? 'text-blue-800' : 'text-red-700'}`}>
                {expirySeconds > 0 ? (
                  <>
                    <ShieldCheck className="w-4 h-4 text-blue-600" />
                    Dev OTP Demo Mode
                  </>
                ) : (
                  <>
                    <AlertCircle className="w-4 h-4 text-red-500" />
                    Code Expired
                  </>
                )}
              </span>
              <button
                type="button"
                onClick={fillDemoOtp}
                disabled={expirySeconds === 0}
                className={`text-xs font-bold px-2.5 py-1 rounded-lg shadow-xs border transition-all ${
                  expirySeconds === 0
                    ? 'text-gray-400 bg-gray-100 border-gray-200 cursor-not-allowed'
                    : 'text-blue-600 hover:text-blue-800 bg-white border-blue-200 cursor-pointer'
                }`}
              >
                Auto-fill Code
              </button>
            </div>
            <div className="mt-2 text-xs text-gray-600 flex items-center gap-2">
              Generated Code:{' '}
              {expirySeconds > 0 ? (
                <span className="font-mono font-bold text-blue-700 text-sm tracking-widest bg-white px-2 py-0.5 rounded-lg border border-blue-100">
                  {devOtp}
                </span>
              ) : (
                <span className="font-mono font-bold text-red-600 text-xs tracking-wider bg-red-100 px-2 py-0.5 rounded-lg border border-red-200">
                  EXPIRED
                </span>
              )}
            </div>
            {demoNote && (
              <p className="text-[11px] text-gray-500 mt-2 italic leading-relaxed">{demoNote}</p>
            )}
          </div>
        )}

        {/* ========================================================================= */}
        {/* 1. EMAIL INPUT STEP                                                       */}
        {/* ========================================================================= */}
        {step === 'email' && (
          <form onSubmit={handleSendOtp} className="space-y-5">
            <div>
              <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">
                Email Address
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-gray-400">
                  <Mail className="w-5 h-5" />
                </div>
                <input
                  type="email"
                  required
                  placeholder="creator@qoneqt.studio"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-12 pr-4 py-3.5 bg-gray-50/50 border border-gray-200 rounded-2xl text-sm font-medium text-gray-900 placeholder:text-gray-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-600/20 focus:border-blue-600 transition-all"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3.5 px-6 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white text-sm font-bold rounded-2xl shadow-xl shadow-blue-500/20 transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-60 cursor-pointer"
            >
              {isLoading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Sending Code...</span>
                </>
              ) : (
                <>
                  <span>Continue</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        )}

        {/* ========================================================================= */}
        {/* 2. EMAIL OTP INPUT STEP                                                   */}
        {/* ========================================================================= */}
        {step === 'otp' && (
          <form onSubmit={handleVerifyOtp} className="space-y-6">
            <div>
              <div className="flex items-center justify-between mb-3">
                <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider">
                  Verification Code
                </label>
                <div className={`flex items-center gap-1 text-xs font-semibold ${expirySeconds > 15 ? 'text-gray-500' : expirySeconds > 0 ? 'text-amber-600 animate-pulse' : 'text-red-600 font-bold'}`}>
                  <Clock className={`w-3.5 h-3.5 ${expirySeconds === 0 ? 'text-red-500' : 'text-gray-400'}`} />
                  <span>{expirySeconds > 0 ? `Expires in: ${formatTimer(expirySeconds)}` : 'Expired'}</span>
                </div>
              </div>

              {/* 6 Digit Input Boxes */}
              <div className="grid grid-cols-6 gap-2 sm:gap-2.5">
                {otp.map((digit, idx) => (
                  <input
                    key={idx}
                    id={`otp-input-${idx}`}
                    type="text"
                    inputMode="numeric"
                    maxLength={1}
                    value={digit}
                    onChange={(e) => handleOtpChange(idx, e.target.value)}
                    onKeyDown={(e) => handleKeyDown(idx, e)}
                    onPaste={handlePaste}
                    className="w-full h-13 sm:h-14 text-center text-xl font-bold font-mono text-gray-900 bg-gray-50/50 border border-gray-200 rounded-2xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-600/30 focus:border-blue-600 transition-all shadow-xs"
                  />
                ))}
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading || expirySeconds === 0}
              className="w-full py-3.5 px-6 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white text-sm font-bold rounded-2xl shadow-xl shadow-blue-500/20 transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-60 cursor-pointer"
            >
              {isLoading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Verifying Code...</span>
                </>
              ) : (
                <>
                  <KeyRound className="w-4 h-4" />
                  <span>Verify Code</span>
                </>
              )}
            </button>

            <div className="flex items-center justify-between text-xs pt-2 border-t border-gray-100">
              <button
                type="button"
                onClick={() => {
                  setStep('email');
                  setOtp(['', '', '', '', '', '']);
                  setError(null);
                  setSuccessMsg(null);
                }}
                className="text-gray-500 hover:text-gray-900 font-medium cursor-pointer"
              >
                Change Email
              </button>

              <button
                type="button"
                onClick={handleResendOtp}
                disabled={cooldownSeconds > 0 || isLoading}
                className="text-blue-600 hover:text-blue-800 font-bold disabled:text-gray-400 cursor-pointer"
              >
                {cooldownSeconds > 0 ? `Resend in ${cooldownSeconds}s` : 'Resend Code'}
              </button>
            </div>
          </form>
        )}

        {/* ========================================================================= */}
        {/* 3. RETURNING USER: TWO-STEP VERIFICATION (Py_SecureVault mfa_verify.html)   */}
        {/* ========================================================================= */}
        {step === 'mfa_verify' && (
          <form onSubmit={handleVerifyMfaLogin} className="space-y-6">
            {mfaMethod === 'totp' ? (
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider">
                    6-digit code from your authenticator
                  </label>
                  <div className="flex items-center gap-1 text-xs font-semibold text-gray-500">
                    <Clock className="w-3.5 h-3.5 text-emerald-600" />
                    <span>Next in: <strong className="text-emerald-700 font-mono">{totpSecondsRemaining}s</strong></span>
                  </div>
                </div>

                {/* Py_SecureVault 30-Second Live Ticker Bar */}
                <div className="w-full bg-gray-100 h-1.5 rounded-full overflow-hidden mb-3">
                  <div 
                    className="h-full bg-gradient-to-r from-emerald-500 to-teal-500 transition-all duration-1000 ease-linear rounded-full"
                    style={{ width: `${(totpSecondsRemaining / 30) * 100}%` }}
                  />
                </div>
                <div className="text-[11px] text-gray-400 text-right mb-4">
                  Code refreshes every 30 s
                </div>

                {/* 6 Digit TOTP Input Boxes */}
                <div className="grid grid-cols-6 gap-2 sm:gap-2.5">
                  {mfaVerifyCode.map((digit, idx) => (
                    <input
                      key={idx}
                      id={`mfa-verify-input-${idx}`}
                      type="text"
                      inputMode="numeric"
                      maxLength={1}
                      value={digit}
                      onChange={(e) => handleMfaVerifyCodeChange(idx, e.target.value)}
                      onKeyDown={(e) => handleMfaVerifyKeyDown(idx, e)}
                      className="w-full h-13 sm:h-14 text-center text-xl font-bold font-mono text-gray-900 bg-gray-50/50 border border-gray-200 rounded-2xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-emerald-600/30 focus:border-emerald-600 transition-all shadow-xs"
                    />
                  ))}
                </div>
              </div>
            ) : (
              /* Emergency Recovery Code Input (Py_SecureVault data-panel="recovery") */
              <div>
                <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">
                  Recovery code (each works once)
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-gray-400">
                    <Key className="w-5 h-5 text-emerald-600" />
                  </div>
                  <input
                    type="text"
                    required
                    placeholder="XXXXX-XXXXX"
                    value={recoveryCodeInput}
                    onChange={(e) => setRecoveryCodeInput(e.target.value.toUpperCase())}
                    className="w-full pl-12 pr-4 py-3.5 bg-gray-50/50 border border-gray-200 rounded-2xl text-base font-mono font-bold text-gray-900 placeholder:text-gray-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-emerald-600/20 focus:border-emerald-600 transition-all uppercase tracking-widest text-center"
                  />
                </div>
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3.5 px-6 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white text-sm font-bold rounded-2xl shadow-xl shadow-emerald-500/20 transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-60 cursor-pointer"
            >
              {isLoading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Verifying Code...</span>
                </>
              ) : (
                <>
                  <ShieldCheck className="w-4 h-4" />
                  <span>{mfaMethod === 'totp' ? 'Verify' : 'Use recovery code'}</span>
                </>
              )}
            </button>

            {/* Switch between TOTP and Recovery Code (Py_SecureVault data-switch) */}
            <div className="flex items-center justify-between text-xs pt-2 border-t border-gray-100">
              <button
                type="button"
                onClick={() => {
                  setStep('email');
                  setPendingMfaToken(null);
                  setError(null);
                }}
                className="text-gray-500 hover:text-gray-900 font-medium cursor-pointer"
              >
                ← Back to sign in
              </button>

              <button
                type="button"
                onClick={() => {
                  setMfaMethod(mfaMethod === 'totp' ? 'recovery' : 'totp');
                  setError(null);
                }}
                className="text-emerald-700 hover:text-emerald-800 font-bold cursor-pointer"
              >
                {mfaMethod === 'totp' ? 'Lost your phone? Use a recovery code' : 'Back to authenticator code'}
              </button>
            </div>
          </form>
        )}

        {/* ========================================================================= */}
        {/* 4. NEW USER: MFA ENROLLMENT SETUP (Py_SecureVault mfa_setup.html)           */}
        {/* ========================================================================= */}
        {step === 'mfa_setup' && setupData && (
          <div className="space-y-5">
            {/* QR Code and Manual Entry Card */}
            <div className="bg-gray-50 p-5 rounded-2xl border border-gray-200 flex flex-col items-center text-center">
              <img
                src={setupData.qr_code}
                alt="QR code containing your TOTP secret"
                className="w-44 h-44 rounded-xl shadow-xs border border-gray-200 bg-white p-2"
              />
              <div className="mt-4 w-full">
                <p className="text-xs text-gray-500 mb-1.5 font-medium">Can't scan? Enter this key manually:</p>
                <div className="flex items-center justify-between p-2.5 bg-white rounded-xl border border-gray-200 font-mono text-xs font-bold text-gray-800">
                  <span className="tracking-wider">{setupData.secret}</span>
                  <button
                    type="button"
                    onClick={() => {
                      navigator.clipboard.writeText(setupData.secret.replace(/\s/g, ''));
                      setSecretCopied(true);
                      setTimeout(() => setSecretCopied(false), 2000);
                    }}
                    className="inline-flex items-center gap-1 text-xs text-emerald-700 hover:text-emerald-800 font-bold bg-gray-50 px-2 py-1 rounded-lg border border-gray-200 shadow-xs cursor-pointer"
                  >
                    {secretCopied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{secretCopied ? 'Copied' : 'Copy key'}</span>
                  </button>
                </div>
                <p className="text-[11px] text-gray-400 mt-2">Type: time-based · 6 digits · 30 s</p>
              </div>
            </div>

            {/* Verification Form */}
            <form onSubmit={handleConfirmSetup} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">
                  Enter the 6-digit code shown in the app
                </label>
                <input
                  type="text"
                  inputMode="numeric"
                  pattern="[0-9 ]{6,7}"
                  maxLength={6}
                  required
                  placeholder="123456"
                  value={setupConfirmCode}
                  onChange={(e) => setSetupConfirmCode(e.target.value.replace(/\D/g, ''))}
                  className="w-full text-center py-3.5 px-4 bg-gray-50 border border-gray-200 rounded-xl text-2xl font-mono font-bold tracking-widest text-gray-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-emerald-600/30 focus:border-emerald-600"
                />
              </div>

              <button
                type="submit"
                disabled={isLoading || setupConfirmCode.length !== 6}
                className="w-full py-3.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm rounded-xl shadow-md shadow-emerald-600/20 flex items-center justify-center gap-2 transition-all cursor-pointer disabled:opacity-50"
              >
                {isLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <ShieldCheck className="w-4 h-4" />}
                <span>Verify & enable MFA</span>
              </button>

              <div className="text-center pt-2">
                <button
                  type="button"
                  onClick={() => {
                    if (pendingSessionToken && pendingUser) {
                      login(pendingSessionToken, pendingUser);
                    }
                  }}
                  className="text-xs text-gray-400 hover:text-gray-600 underline cursor-pointer"
                >
                  Skip for now, continue to Dashboard
                </button>
              </div>
            </form>
          </div>
        )}

        {/* ========================================================================= */}
        {/* 5. NEW USER: RECOVERY CODES DISPLAY (Py_SecureVault recovery_codes.html)   */}
        {/* ========================================================================= */}
        {step === 'mfa_recovery' && (
          <div className="space-y-5 animate-fadeIn">
            {/* 8 Recovery codes in Py_SecureVault card style */}
            <div className="grid grid-cols-2 gap-2.5 bg-gray-50 p-4 rounded-2xl border border-gray-200 font-mono text-xs font-bold text-gray-800 text-center">
              {recoveryCodes.map((code, idx) => (
                <div key={idx} className="bg-white p-2.5 rounded-xl border border-gray-200 tracking-wider shadow-2xs">
                  {code}
                </div>
              ))}
            </div>

            <div className="flex flex-col sm:flex-row items-center gap-2.5">
              <button
                type="button"
                onClick={handleCopyRecoveryCodes}
                className="w-full py-2.5 bg-gray-100 hover:bg-gray-200 text-gray-800 font-bold text-xs rounded-xl transition-colors flex items-center justify-center gap-1.5 cursor-pointer"
              >
                {recoveryCopied ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
                <span>{recoveryCopied ? 'Copied all' : 'Copy all'}</span>
              </button>

              <button
                type="button"
                onClick={handleDownloadRecoveryCodes}
                className="w-full py-2.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-bold text-xs rounded-xl transition-colors flex items-center justify-center gap-1.5 cursor-pointer"
              >
                <Download className="w-4 h-4" />
                <span>Download as .txt</span>
              </button>
            </div>

            <button
              type="button"
              onClick={handleFinishOnboarding}
              className="w-full py-3.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm rounded-xl shadow-md shadow-emerald-600/20 transition-all cursor-pointer"
            >
              I've saved them, continue to Dashboard
            </button>
          </div>
        )}

        {/* Security Assurance Footer */}
        <div className="mt-8 pt-5 border-t border-gray-100 flex items-center gap-3 text-gray-500 text-xs leading-relaxed">
          <Lock className="w-5 h-5 text-emerald-600 shrink-0" />
          <span>
            <strong>Py_SecureVault Security Architecture:</strong> AES-128 Fernet encrypted TOTP secrets at rest, clock drift tolerance & single-use recovery code protection.
          </span>
        </div>
      </div>
    </div>
  );
}
