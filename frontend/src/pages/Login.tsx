import React, { useState, useEffect } from 'react';
import { 
  Sparkles, Mail, KeyRound, ArrowRight, RefreshCw, 
  CheckCircle2, AlertCircle, ShieldCheck, Clock, Lock
} from 'lucide-react';
import { authApi } from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function Login() {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [step, setStep] = useState<'email' | 'otp'>('email');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Timers
  const [expirySeconds, setExpirySeconds] = useState(300); // 5 minutes
  const [cooldownSeconds, setCooldownSeconds] = useState(60); // 60 seconds

  // Demo mode
  const [isDemoMode, setIsDemoMode] = useState(false);
  const [devOtp, setDevOtp] = useState<string | null>(null);
  const [demoNote, setDemoNote] = useState<string | null>(null);

  // Countdown timer effect
  useEffect(() => {
    let interval: any = null;
    if (step === 'otp') {
      interval = setInterval(() => {
        setExpirySeconds((prev) => (prev > 0 ? prev - 1 : 0));
        setCooldownSeconds((prev) => (prev > 0 ? prev - 1 : 0));
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [step]);

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
      setExpirySeconds(res.expires_in_seconds || 300);
      setCooldownSeconds(res.cooldown_seconds || 60);
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
      setExpirySeconds(res.expires_in_seconds || 300);
      setCooldownSeconds(res.cooldown_seconds || 60);
      setIsDemoMode(!!res.is_demo_mode);
      setDevOtp(res.dev_otp || null);
      setDemoNote(res.demo_note || null);
      setSuccessMsg('New verification code issued.');
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to resend code.';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleOtpChange = (index: number, val: string) => {
    // Only accept digits
    const cleaned = val.replace(/\D/g, '');
    const newOtp = [...otp];

    if (cleaned.length > 1) {
      // User pasted multiple characters into this input
      const digits = cleaned.slice(0, 6).split('');
      digits.forEach((d, i) => {
        if (i < 6) newOtp[i] = d;
      });
      setOtp(newOtp);
      const nextIdx = Math.min(digits.length, 5);
      const nextInput = document.getElementById(`otp-input-${nextIdx}`);
      nextInput?.focus();
      return;
    }

    newOtp[index] = cleaned;
    setOtp(newOtp);

    // Auto-advance to next input
    if (cleaned && index < 5) {
      const nextInput = document.getElementById(`otp-input-${index + 1}`);
      nextInput?.focus();
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      const prevInput = document.getElementById(`otp-input-${index - 1}`);
      prevInput?.focus();
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
      if (res.success && res.session_token && res.user) {
        setSuccessMsg(res.is_new_user ? 'Account created! Welcome to Qoneqt.' : 'Verified! Welcome back.');
        setTimeout(() => {
          login(res.session_token, res.user);
        }, 500);
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Invalid verification code.';
      setError(msg);
    } finally {
      setIsLoading(false);
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
    <div className="min-h-screen w-full flex items-center justify-center p-4 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-blue-50/50 via-gray-50/80 to-gray-100">
      <div className="w-full max-w-md bg-white rounded-3xl shadow-xl shadow-blue-500/5 border border-gray-100 p-8 sm:p-10 relative overflow-hidden">
        {/* Glow ambient background header */}
        <div className="absolute -top-24 -left-24 w-52 h-52 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -top-24 -right-24 w-52 h-52 bg-orange-500/10 rounded-full blur-3xl pointer-events-none" />

        {/* Brand Logo & Name */}
        <div className="flex flex-col items-center text-center mb-8 relative z-10">
          <div className="w-14 h-14 bg-gradient-to-br from-blue-600 to-orange-500 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-500/20 mb-4 group hover:scale-105 transition-transform duration-300">
            <Sparkles className="w-7 h-7 text-white" />
          </div>
          <h2 className="text-2xl font-black text-gray-900 tracking-tight">Qoneqt AI Content Studio</h2>
          <p className="text-xs font-semibold text-blue-600 uppercase tracking-widest mt-1">
            From One Idea to a Publish-Ready Video
          </p>
        </div>

        {/* Heading & Subtitle */}
        <div className="text-center mb-6">
          <h1 className="text-xl font-bold text-gray-900">Welcome to Qoneqt</h1>
          <p className="text-sm text-gray-500 mt-1">
            {step === 'email' 
              ? 'Sign in securely to your AI Content Studio.' 
              : `Enter the 6-digit code sent to ${email}`}
          </p>
        </div>

        {/* Alerts & Feedback */}
        {error && (
          <div className="mb-5 p-3.5 bg-red-50 border border-red-200 text-red-700 text-xs sm:text-sm rounded-xl flex items-start gap-2.5 animate-fadeIn">
            <AlertCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
            <div className="flex-1 font-medium">{error}</div>
          </div>
        )}

        {successMsg && !error && (
          <div className="mb-5 p-3.5 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs sm:text-sm rounded-xl flex items-start gap-2.5 animate-fadeIn">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
            <div className="flex-1 font-medium">{successMsg}</div>
          </div>
        )}

        {/* Development Demo Mode Badge */}
        {step === 'otp' && isDemoMode && devOtp && (
          <div className="mb-6 p-3.5 bg-blue-50 border border-blue-200/80 rounded-xl">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-blue-800 uppercase tracking-wider flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-blue-600" />
                Dev OTP Demo Mode
              </span>
              <button
                type="button"
                onClick={fillDemoOtp}
                className="text-xs font-bold text-blue-600 hover:text-blue-800 hover:underline bg-white px-2 py-1 rounded shadow-xs border border-blue-200"
              >
                Auto-fill Code
              </button>
            </div>
            <div className="mt-2 text-xs text-gray-600">
              Generated Code:{' '}
              <span className="font-mono font-bold text-blue-700 text-sm tracking-widest bg-white px-2 py-0.5 rounded border border-blue-100">
                {devOtp}
              </span>
            </div>
            {demoNote && (
              <p className="text-[11px] text-gray-500 mt-1.5 italic leading-tight">{demoNote}</p>
            )}
          </div>
        )}

        {/* Step 1: Email Input */}
        {step === 'email' ? (
          <form onSubmit={handleSendOtp} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">
                Email Address
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-gray-400">
                  <Mail className="w-5 h-5" />
                </div>
                <input
                  type="email"
                  required
                  placeholder="creator@qoneqt.studio"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-11 pr-4 py-3 bg-gray-50/50 border border-gray-200 rounded-xl text-sm font-medium text-gray-900 placeholder:text-gray-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-600/20 focus:border-blue-600 transition-all"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3.5 px-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-bold rounded-xl shadow-lg shadow-blue-500/20 transition-all duration-200 flex items-center justify-center gap-2 group disabled:opacity-60 cursor-pointer"
            >
              {isLoading ? (
                <>
                  <RefreshCw className="w-5 h-5 animate-spin" />
                  <span>Generating Code...</span>
                </>
              ) : (
                <>
                  <span>Send OTP</span>
                  <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </button>
          </form>
        ) : (
          /* Step 2: 6-Digit OTP Input */
          <form onSubmit={handleVerifyOtp} className="space-y-5">
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider">
                  Verification Code
                </label>
                <div className="flex items-center gap-1 text-xs font-semibold text-gray-500">
                  <Clock className="w-3.5 h-3.5 text-gray-400" />
                  <span>Expires in: {formatTimer(expirySeconds)}</span>
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
                    className="w-full h-12 text-center text-lg font-bold font-mono text-gray-900 bg-gray-50/50 border border-gray-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-600/30 focus:border-blue-600 transition-all"
                  />
                ))}
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading || expirySeconds === 0}
              className="w-full py-3.5 px-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-bold rounded-xl shadow-lg shadow-blue-500/20 transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-60 cursor-pointer"
            >
              {isLoading ? (
                <>
                  <RefreshCw className="w-5 h-5 animate-spin" />
                  <span>Verifying Code...</span>
                </>
              ) : (
                <>
                  <KeyRound className="w-5 h-5" />
                  <span>Verify OTP</span>
                </>
              )}
            </button>

            {/* Resend & Change Email controls */}
            <div className="flex items-center justify-between text-xs pt-1 border-t border-gray-100">
              <button
                type="button"
                onClick={() => {
                  setStep('email');
                  setOtp(['', '', '', '', '', '']);
                  setError(null);
                  setSuccessMsg(null);
                }}
                className="text-gray-500 hover:text-gray-900 font-medium transition-colors"
              >
                Change Email
              </button>

              <button
                type="button"
                onClick={handleResendOtp}
                disabled={cooldownSeconds > 0 || isLoading}
                className="text-blue-600 hover:text-blue-800 font-semibold disabled:text-gray-400 transition-colors"
              >
                {cooldownSeconds > 0 ? `Resend code in ${cooldownSeconds}s` : 'Resend Code'}
              </button>
            </div>
          </form>
        )}

        {/* Security Note Footer */}
        <div className="mt-8 pt-5 border-t border-gray-100 flex items-center gap-2.5 text-gray-500 text-[11px] leading-tight">
          <Lock className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>
            <strong>Secure Passwordless Authentication:</strong> Single-use cryptographic OTP verified on server. First-time login automatically creates your account.
          </span>
        </div>
      </div>
    </div>
  );
}
