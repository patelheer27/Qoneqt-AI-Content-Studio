import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, FileCheck, Eraser, KeyRound, Copy, Check, 
  AlertTriangle, RefreshCw, Download, ArrowRight, Info, 
  Upload, FileVideo, HardDrive, CheckCircle2, XCircle, Clock,
  Eye, Sparkles, UserCheck, LogOut
} from 'lucide-react';
import { securityApi } from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function SecurityCenter() {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState<'integrity' | 'metadata' | 'auth'>('integrity');

  // Stats
  const [stats, setStats] = useState<{
    authenticated: boolean;
    user_email?: string;
    videos_checked_session: number;
    videos_sanitized_session: number;
  }>({
    authenticated: true,
    videos_checked_session: 0,
    videos_sanitized_session: 0,
  });

  const loadStats = async () => {
    try {
      const data = await securityApi.getSecurityStats();
      setStats(data);
    } catch (err) {
      console.error('Failed to load security stats:', err);
    }
  };

  useEffect(() => {
    loadStats();
  }, []);

  // ==================== FEATURE 2: VIDEO INTEGRITY CHECKER STATE ====================
  const [integrityFile, setIntegrityFile] = useState<File | null>(null);
  const [integrityLoading, setIntegrityLoading] = useState(false);
  const [calculatedHash, setCalculatedHash] = useState<string | null>(null);
  const [bytesProcessed, setBytesProcessed] = useState<number | null>(null);
  const [formattedSize, setFormattedSize] = useState<string | null>(null);
  const [referenceHash, setReferenceHash] = useState<string>('');
  const [integrityResult, setIntegrityResult] = useState<{
    status: string;
    is_match?: boolean;
    details?: string;
  } | null>(null);
  const [integrityError, setIntegrityError] = useState<string | null>(null);
  const [hashCopied, setHashCopied] = useState(false);

  const handleIntegrityFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setIntegrityFile(e.target.files[0]);
      setCalculatedHash(null);
      setIntegrityResult(null);
      setIntegrityError(null);
    }
  };

  const handleCalculateHash = async () => {
    if (!integrityFile) {
      setIntegrityError('Please select a video file first.');
      return;
    }
    setIntegrityLoading(true);
    setIntegrityError(null);
    setIntegrityResult(null);

    try {
      const res = await securityApi.calculateHash(integrityFile);
      setCalculatedHash(res.sha256_hash);
      setBytesProcessed(res.bytes_processed);
      setFormattedSize(res.size_formatted);
      loadStats();
    } catch (err: any) {
      setIntegrityError(err.response?.data?.detail || 'Failed to calculate file hash.');
    } finally {
      setIntegrityLoading(false);
    }
  };

  const handleVerifyIntegrity = async () => {
    if (!integrityFile) {
      setIntegrityError('Please select a video file first.');
      return;
    }
    if (!referenceHash.trim()) {
      setIntegrityError('Please enter a reference SHA-256 hash to compare against.');
      return;
    }

    setIntegrityLoading(true);
    setIntegrityError(null);

    try {
      const res = await securityApi.verifyIntegrity(integrityFile, referenceHash.trim());
      setCalculatedHash(res.calculated_hash);
      setIntegrityResult({
        status: res.status,
        is_match: res.is_match,
        details: res.details,
      });
      loadStats();
    } catch (err: any) {
      setIntegrityError(err.response?.data?.detail || 'Failed to verify integrity.');
    } finally {
      setIntegrityLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setHashCopied(true);
    setTimeout(() => setHashCopied(false), 2000);
  };

  const resetIntegrity = () => {
    setIntegrityFile(null);
    setCalculatedHash(null);
    setReferenceHash('');
    setIntegrityResult(null);
    setIntegrityError(null);
  };

  // ==================== FEATURE 3: VIDEO METADATA SANITIZER STATE ====================
  const [metadataFile, setMetadataFile] = useState<File | null>(null);
  const [metadataLoading, setMetadataLoading] = useState(false);
  const [metadataError, setMetadataError] = useState<string | null>(null);
  const [originalMetadata, setOriginalMetadata] = useState<any | null>(null);
  const [sanitizedResult, setSanitizedResult] = useState<any | null>(null);

  const handleMetadataFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setMetadataFile(e.target.files[0]);
      setOriginalMetadata(null);
      setSanitizedResult(null);
      setMetadataError(null);
    }
  };

  const handleInspectMetadata = async () => {
    if (!metadataFile) {
      setMetadataError('Please select a video file to inspect.');
      return;
    }
    setMetadataLoading(true);
    setMetadataError(null);

    try {
      const res = await securityApi.inspectMetadata(metadataFile);
      setOriginalMetadata(res);
      loadStats();
    } catch (err: any) {
      setMetadataError(err.response?.data?.detail || 'Failed to inspect video metadata.');
    } finally {
      setMetadataLoading(false);
    }
  };

  const handleSanitizeMetadata = async () => {
    if (!metadataFile) {
      setMetadataError('Please select a video file to sanitize.');
      return;
    }
    setMetadataLoading(true);
    setMetadataError(null);

    try {
      const res = await securityApi.sanitizeMetadata(metadataFile);
      setSanitizedResult(res);
      if (res.original) {
        setOriginalMetadata(res.original);
      }
      loadStats();
    } catch (err: any) {
      setMetadataError(err.response?.data?.detail || 'Failed to sanitize video metadata.');
    } finally {
      setMetadataLoading(false);
    }
  };

  const resetMetadata = () => {
    setMetadataFile(null);
    setOriginalMetadata(null);
    setSanitizedResult(null);
    setMetadataError(null);
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-8 animate-fadeIn">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-blue-950 to-indigo-950 rounded-3xl p-8 text-white relative overflow-hidden shadow-xl shadow-blue-900/10 border border-blue-900/40">
        <div className="absolute top-0 right-0 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/20 text-blue-300 text-xs font-bold uppercase tracking-wider mb-3 border border-blue-400/20">
              <ShieldCheck className="w-4 h-4 text-blue-400" />
              Security & Privacy Center
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight">Qoneqt Security & Privacy Suite</h1>
            <p className="text-blue-200/80 text-sm mt-1 max-w-xl">
              Cryptographic verification, video integrity analysis, and container metadata sanitization.
            </p>
          </div>

          {/* Real Session Stats Counter */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="bg-white/10 backdrop-blur-md px-4 py-3 rounded-2xl border border-white/10 text-center min-w-[120px]">
              <div className="text-xs font-medium text-blue-200">Verified Email</div>
              <div className="text-sm font-bold text-white truncate max-w-[150px]">
                {user?.email || 'Active User'}
              </div>
            </div>
            <div className="bg-white/10 backdrop-blur-md px-4 py-3 rounded-2xl border border-white/10 text-center min-w-[110px]">
              <div className="text-xs font-medium text-blue-200">Videos Checked</div>
              <div className="text-xl font-black text-white">{stats.videos_checked_session}</div>
            </div>
            <div className="bg-white/10 backdrop-blur-md px-4 py-3 rounded-2xl border border-white/10 text-center min-w-[110px]">
              <div className="text-xs font-medium text-blue-200">Sanitized</div>
              <div className="text-xl font-black text-emerald-400">{stats.videos_sanitized_session}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Feature Selector Tabs */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Card 1: Video Integrity Checker */}
        <button
          onClick={() => setActiveTab('integrity')}
          className={`p-5 rounded-2xl text-left border transition-all cursor-pointer ${
            activeTab === 'integrity'
              ? 'bg-white border-blue-600 ring-2 ring-blue-600/20 shadow-md'
              : 'bg-white/70 border-gray-200 hover:bg-white hover:border-gray-300'
          }`}
        >
          <div className="flex items-center justify-between mb-3">
            <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold">
              <FileCheck className="w-5 h-5" />
            </div>
            {activeTab === 'integrity' && (
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 uppercase">
                Active Tool
              </span>
            )}
          </div>
          <h3 className="font-bold text-gray-900 text-base">Video Integrity Checker</h3>
          <p className="text-xs text-gray-500 mt-1">
            Calculate and verify SHA-256 cryptographic hashes from actual file bytes to detect file modifications.
          </p>
        </button>

        {/* Card 2: Video Metadata Sanitizer */}
        <button
          onClick={() => setActiveTab('metadata')}
          className={`p-5 rounded-2xl text-left border transition-all cursor-pointer ${
            activeTab === 'metadata'
              ? 'bg-white border-blue-600 ring-2 ring-blue-600/20 shadow-md'
              : 'bg-white/70 border-gray-200 hover:bg-white hover:border-gray-300'
          }`}
        >
          <div className="flex items-center justify-between mb-3">
            <div className="w-10 h-10 rounded-xl bg-orange-50 text-orange-600 flex items-center justify-center font-bold">
              <Eraser className="w-5 h-5" />
            </div>
            {activeTab === 'metadata' && (
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-orange-100 text-orange-700 uppercase">
                Active Tool
              </span>
            )}
          </div>
          <h3 className="font-bold text-gray-900 text-base">Video Metadata Sanitizer</h3>
          <p className="text-xs text-gray-500 mt-1">
            Inspect container tags using FFprobe and create a sanitized output video using FFmpeg without overwriting original.
          </p>
        </button>

        {/* Card 3: Email + OTP Auth */}
        <button
          onClick={() => setActiveTab('auth')}
          className={`p-5 rounded-2xl text-left border transition-all cursor-pointer ${
            activeTab === 'auth'
              ? 'bg-white border-blue-600 ring-2 ring-blue-600/20 shadow-md'
              : 'bg-white/70 border-gray-200 hover:bg-white hover:border-gray-300'
          }`}
        >
          <div className="flex items-center justify-between mb-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold">
              <KeyRound className="w-5 h-5" />
            </div>
            {activeTab === 'auth' && (
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 uppercase">
                Active Tool
              </span>
            )}
          </div>
          <h3 className="font-bold text-gray-900 text-base">Email + OTP Verification</h3>
          <p className="text-xs text-gray-500 mt-1">
            Manage your passwordless authenticated session and view cryptographic authentication parameters.
          </p>
        </button>
      </div>

      {/* ========================================================================= */}
      {/* TAB 1: VIDEO INTEGRITY CHECKER                                            */}
      {/* ========================================================================= */}
      {activeTab === 'integrity' && (
        <div className="bg-white rounded-3xl p-6 sm:p-8 border border-gray-200 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-gray-100 pb-5">
            <div>
              <h2 className="text-xl font-extrabold text-gray-900 flex items-center gap-2">
                <FileCheck className="w-6 h-6 text-blue-600" />
                SHA-256 Video Integrity Checker
              </h2>
              <p className="text-xs text-gray-500 mt-1">
                Reads stream chunks incrementally to calculate and verify the exact cryptographic fingerprint.
              </p>
            </div>
            {integrityFile && (
              <button
                onClick={resetIntegrity}
                className="px-3.5 py-1.5 text-xs font-bold text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-xl transition-colors cursor-pointer self-start"
              >
                Clear / Reset
              </button>
            )}
          </div>

          {integrityError && (
            <div className="p-4 bg-red-50 border border-red-200 text-red-700 text-xs sm:text-sm rounded-2xl flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-red-500 shrink-0" />
              <div className="flex-1 font-medium">{integrityError}</div>
            </div>
          )}

          {/* Upload & Drag-and-Drop Area */}
          <div className="space-y-4">
            <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider">
              Upload Video File (MP4, MOV, WEBM)
            </label>
            <div className="border-2 border-dashed border-gray-200 hover:border-blue-400 rounded-2xl p-6 text-center transition-colors bg-gray-50/50">
              <input
                type="file"
                id="integrity-video-upload"
                accept="video/mp4,video/quicktime,video/webm,video/*"
                onChange={handleIntegrityFileSelect}
                className="hidden"
              />
              <label htmlFor="integrity-video-upload" className="cursor-pointer block">
                <div className="w-12 h-12 bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-3">
                  <Upload className="w-6 h-6" />
                </div>
                {integrityFile ? (
                  <div className="space-y-1">
                    <div className="text-sm font-bold text-gray-900 flex items-center justify-center gap-2">
                      <FileVideo className="w-4 h-4 text-blue-600" />
                      {integrityFile.name}
                    </div>
                    <div className="text-xs text-gray-500">
                      {(integrityFile.size / (1024 * 1024)).toFixed(2)} MB • {integrityFile.type || 'video'}
                    </div>
                    <div className="text-xs text-blue-600 font-semibold mt-2">Click to replace file</div>
                  </div>
                ) : (
                  <div>
                    <span className="text-sm font-bold text-blue-600 hover:text-blue-700">Choose a video</span>
                    <span className="text-sm text-gray-500"> or drag and drop</span>
                    <p className="text-xs text-gray-400 mt-1">Up to 100 MB per file</p>
                  </div>
                )}
              </label>
            </div>
          </div>

          {/* Action 1: Calculate Hash */}
          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={handleCalculateHash}
              disabled={!integrityFile || integrityLoading}
              className="px-5 py-3 bg-blue-600 hover:bg-blue-700 text-white text-xs sm:text-sm font-bold rounded-xl shadow-md shadow-blue-500/20 disabled:opacity-50 transition-all flex items-center gap-2 cursor-pointer"
            >
              {integrityLoading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Processing Bytes...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Calculate SHA-256</span>
                </>
              )}
            </button>
          </div>

          {/* Display Calculated Hash */}
          {calculatedHash && (
            <div className="p-4 bg-gray-50 rounded-2xl border border-gray-200 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-gray-700 uppercase tracking-wider flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  Calculated Fingerprint (SHA-256)
                </span>
                <button
                  onClick={() => copyToClipboard(calculatedHash)}
                  className="inline-flex items-center gap-1 text-xs font-bold text-blue-600 hover:text-blue-800 bg-white px-2.5 py-1 rounded-lg border border-gray-200 shadow-xs transition-colors cursor-pointer"
                >
                  {hashCopied ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-600" />
                      <span className="text-emerald-600">Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      <span>Copy Hash</span>
                    </>
                  )}
                </button>
              </div>
              <div className="font-mono text-xs sm:text-sm font-bold text-gray-900 break-all bg-white p-3 rounded-xl border border-gray-200">
                {calculatedHash}
              </div>
              {formattedSize && (
                <div className="text-[11px] text-gray-500">
                  Total processed: <strong>{formattedSize}</strong> ({bytesProcessed?.toLocaleString()} bytes)
                </div>
              )}
            </div>
          )}

          {/* Action 2: Verify against Reference Hash */}
          <div className="space-y-3 pt-3 border-t border-gray-100">
            <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider">
              Verify Against Reference SHA-256 Hash
            </label>
            <div className="flex flex-col sm:flex-row gap-3">
              <input
                type="text"
                placeholder="Paste expected 64-character SHA-256 reference hash here..."
                value={referenceHash}
                onChange={(e) => setReferenceHash(e.target.value)}
                className="flex-1 px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-xs sm:text-sm font-mono text-gray-900 placeholder:text-gray-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-600/30"
              />
              <button
                onClick={handleVerifyIntegrity}
                disabled={!integrityFile || !referenceHash || integrityLoading}
                className="px-5 py-3 bg-slate-900 hover:bg-black text-white text-xs sm:text-sm font-bold rounded-xl shadow-md disabled:opacity-50 transition-all flex items-center justify-center gap-2 cursor-pointer shrink-0"
              >
                {integrityLoading ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <FileCheck className="w-4 h-4 text-emerald-400" />
                )}
                <span>Verify Integrity</span>
              </button>
            </div>
          </div>

          {/* Verification Result Feedback */}
          {integrityResult && (
            <div
              className={`p-5 rounded-2xl border flex items-start gap-3.5 ${
                integrityResult.is_match
                  ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
                  : 'bg-amber-50 border-amber-200 text-amber-900'
              }`}
            >
              {integrityResult.is_match ? (
                <CheckCircle2 className="w-6 h-6 text-emerald-600 shrink-0 mt-0.5" />
              ) : (
                <XCircle className="w-6 h-6 text-amber-600 shrink-0 mt-0.5" />
              )}
              <div className="space-y-1">
                <h4 className="text-sm font-extrabold">{integrityResult.status}</h4>
                <p className="text-xs leading-relaxed opacity-90">{integrityResult.details}</p>
              </div>
            </div>
          )}

          {/* Educational Disclaimer */}
          <div className="p-4 bg-blue-50/60 rounded-2xl border border-blue-100 flex items-start gap-3 text-xs text-blue-900/80 leading-relaxed">
            <Info className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
            <div>
              <strong>Security Explanation:</strong> SHA-256 detects whether a file differs from a trusted reference. A matching hash does not prove that the video is malware-free or that the original video was trustworthy.
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 2: VIDEO METADATA SANITIZER                                           */}
      {/* ========================================================================= */}
      {activeTab === 'metadata' && (
        <div className="bg-white rounded-3xl p-6 sm:p-8 border border-gray-200 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-gray-100 pb-5">
            <div>
              <h2 className="text-xl font-extrabold text-gray-900 flex items-center gap-2">
                <Eraser className="w-6 h-6 text-orange-600" />
                FFprobe & FFmpeg Video Metadata Sanitizer
              </h2>
              <p className="text-xs text-gray-500 mt-1">
                Inspects stream/container tags with FFprobe and strips identifying metadata into a clean output copy.
              </p>
            </div>
            {metadataFile && (
              <button
                onClick={resetMetadata}
                className="px-3.5 py-1.5 text-xs font-bold text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-xl transition-colors cursor-pointer self-start"
              >
                Clear / Reset
              </button>
            )}
          </div>

          {metadataError && (
            <div className="p-4 bg-red-50 border border-red-200 text-red-700 text-xs sm:text-sm rounded-2xl flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-red-500 shrink-0" />
              <div className="flex-1 font-medium">{metadataError}</div>
            </div>
          )}

          {/* Upload Area */}
          <div className="space-y-4">
            <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider">
              Select Video File (MP4, MOV, WEBM)
            </label>
            <div className="border-2 border-dashed border-gray-200 hover:border-orange-400 rounded-2xl p-6 text-center transition-colors bg-gray-50/50">
              <input
                type="file"
                id="metadata-video-upload"
                accept="video/mp4,video/quicktime,video/webm,video/*"
                onChange={handleMetadataFileSelect}
                className="hidden"
              />
              <label htmlFor="metadata-video-upload" className="cursor-pointer block">
                <div className="w-12 h-12 bg-orange-50 text-orange-600 rounded-2xl flex items-center justify-center mx-auto mb-3">
                  <Upload className="w-6 h-6" />
                </div>
                {metadataFile ? (
                  <div className="space-y-1">
                    <div className="text-sm font-bold text-gray-900 flex items-center justify-center gap-2">
                      <FileVideo className="w-4 h-4 text-orange-600" />
                      {metadataFile.name}
                    </div>
                    <div className="text-xs text-gray-500">
                      {(metadataFile.size / (1024 * 1024)).toFixed(2)} MB
                    </div>
                    <div className="text-xs text-orange-600 font-semibold mt-2">Click to replace file</div>
                  </div>
                ) : (
                  <div>
                    <span className="text-sm font-bold text-orange-600 hover:text-orange-700">Choose a video</span>
                    <span className="text-sm text-gray-500"> or drag and drop</span>
                    <p className="text-xs text-gray-400 mt-1">Up to 100 MB per file</p>
                  </div>
                )}
              </label>
            </div>
          </div>

          {/* Actions: Inspect & Sanitize */}
          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={handleInspectMetadata}
              disabled={!metadataFile || metadataLoading}
              className="px-5 py-3 bg-slate-900 hover:bg-black text-white text-xs sm:text-sm font-bold rounded-xl shadow-md disabled:opacity-50 transition-all flex items-center gap-2 cursor-pointer"
            >
              {metadataLoading ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Eye className="w-4 h-4" />
              )}
              <span>Inspect Metadata</span>
            </button>

            <button
              onClick={handleSanitizeMetadata}
              disabled={!metadataFile || metadataLoading}
              className="px-5 py-3 bg-orange-600 hover:bg-orange-700 text-white text-xs sm:text-sm font-bold rounded-xl shadow-md shadow-orange-500/20 disabled:opacity-50 transition-all flex items-center gap-2 cursor-pointer"
            >
              {metadataLoading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Sanitizing with FFmpeg...</span>
                </>
              ) : (
                <>
                  <Eraser className="w-4 h-4" />
                  <span>Sanitize Video</span>
                </>
              )}
            </button>
          </div>

          {/* Original Metadata Panel */}
          {originalMetadata && (
            <div className="p-5 bg-gray-50 rounded-2xl border border-gray-200 space-y-4">
              <h3 className="text-sm font-extrabold text-gray-900 flex items-center gap-2">
                <FileVideo className="w-4 h-4 text-blue-600" />
                Original Video Metadata (Detected by FFprobe)
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div className="bg-white p-3 rounded-xl border border-gray-100">
                  <span className="text-gray-400 block font-medium">Container Format</span>
                  <span className="font-bold text-gray-900">{originalMetadata.container_format || 'Unknown'}</span>
                </div>
                <div className="bg-white p-3 rounded-xl border border-gray-100">
                  <span className="text-gray-400 block font-medium">Resolution</span>
                  <span className="font-bold text-gray-900">{originalMetadata.dimensions || 'Not present'}</span>
                </div>
                <div className="bg-white p-3 rounded-xl border border-gray-100">
                  <span className="text-gray-400 block font-medium">Video Codec</span>
                  <span className="font-bold text-gray-900">{originalMetadata.video_codec || 'Not present'}</span>
                </div>
                <div className="bg-white p-3 rounded-xl border border-gray-100">
                  <span className="text-gray-400 block font-medium">Audio Codec</span>
                  <span className="font-bold text-gray-900">{originalMetadata.audio_codec || 'Not present'}</span>
                </div>
                <div className="bg-white p-3 rounded-xl border border-gray-100">
                  <span className="text-gray-400 block font-medium">Creation Timestamp</span>
                  <span className="font-bold text-gray-900">{originalMetadata.creation_time || 'Not present'}</span>
                </div>
                <div className="bg-white p-3 rounded-xl border border-gray-100">
                  <span className="text-gray-400 block font-medium">Encoder / Software</span>
                  <span className="font-bold text-gray-900">{originalMetadata.encoder || 'Not present'}</span>
                </div>
                <div className="bg-white p-3 rounded-xl border border-gray-100">
                  <span className="text-gray-400 block font-medium">Location / GPS</span>
                  <span className="font-bold text-gray-900">{originalMetadata.location || 'Not present'}</span>
                </div>
                <div className="bg-white p-3 rounded-xl border border-gray-100">
                  <span className="text-gray-400 block font-medium">Chapters</span>
                  <span className="font-bold text-gray-900">{originalMetadata.chapters_count || 0}</span>
                </div>
              </div>

              {/* Tags inspection */}
              {originalMetadata.container_tags && Object.keys(originalMetadata.container_tags).length > 0 && (
                <div className="bg-white p-3.5 rounded-xl border border-gray-100">
                  <span className="text-[11px] font-bold text-gray-500 uppercase tracking-wider block mb-1.5">
                    Container Level Tags
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {Object.entries(originalMetadata.container_tags).map(([key, val]) => (
                      <span key={key} className="px-2 py-1 bg-gray-100 text-gray-700 rounded-md font-mono text-[11px]">
                        <strong>{key}:</strong> {String(val).slice(0, 40)}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Sanitization Results & Comparison */}
          {sanitizedResult && (
            <div className="p-6 bg-gradient-to-br from-emerald-50/50 via-teal-50/30 to-gray-50 rounded-2xl border border-emerald-200/80 space-y-5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 text-xs font-bold uppercase tracking-wider mb-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    Sanitization Successful
                  </div>
                  <h3 className="text-lg font-black text-gray-900">{sanitizedResult.summary}</h3>
                </div>

                <a
                  href={`http://localhost:8000${sanitizedResult.download_url}`}
                  download
                  className="px-5 py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs sm:text-sm rounded-xl shadow-md shadow-emerald-600/20 flex items-center justify-center gap-2 transition-all cursor-pointer shrink-0"
                >
                  <Download className="w-4 h-4" />
                  <span>Download Sanitized Video</span>
                </a>
              </div>

              {/* Structured Comparison Table */}
              <div className="bg-white rounded-xl border border-emerald-100 overflow-hidden shadow-xs">
                <div className="p-4 bg-emerald-50/50 border-b border-emerald-100 font-bold text-xs text-gray-700 uppercase tracking-wider">
                  Before vs. After Metadata Comparison
                </div>
                <div className="divide-y divide-gray-100 text-xs">
                  {sanitizedResult.comparison?.details?.length > 0 ? (
                    sanitizedResult.comparison.details.map((item: any, idx: number) => (
                      <div key={idx} className="p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                        <div className="font-semibold text-gray-800">{item.field}</div>
                        <div className="flex items-center gap-3">
                          <span className="text-gray-500 font-mono text-[11px] line-through">
                            {item.original}
                          </span>
                          <ArrowRight className="w-3.5 h-3.5 text-gray-400" />
                          <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                            item.status === 'Removed' ? 'bg-emerald-100 text-emerald-800' : 'bg-gray-100 text-gray-700'
                          }`}>
                            {item.sanitized}
                          </span>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="p-4 text-gray-500 text-xs">
                      No optional identifying tags were detected in the original container.
                    </div>
                  )}
                </div>
              </div>

              {/* Preserved Streams Indicator */}
              <div className="flex flex-wrap items-center gap-2 text-xs">
                <span className="font-bold text-gray-700">Preserved Streams:</span>
                {sanitizedResult.comparison?.retained_fields?.map((field: string, idx: number) => (
                  <span key={idx} className="px-2.5 py-1 bg-white text-gray-800 rounded-lg border border-gray-200 font-medium">
                    ✓ {field}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Educational Disclaimer */}
          <div className="p-4 bg-orange-50/60 rounded-2xl border border-orange-100 flex items-start gap-3 text-xs text-orange-950/80 leading-relaxed">
            <Info className="w-4 h-4 text-orange-600 shrink-0 mt-0.5" />
            <div>
              <strong>Metadata Disclaimer:</strong> Metadata sanitization removes supported metadata fields from the output file. It cannot guarantee the removal of every identifying signal embedded in media content or every proprietary metadata format.
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 3: EMAIL + OTP AUTHENTICATION SUMMARY                                 */}
      {/* ========================================================================= */}
      {activeTab === 'auth' && (
        <div className="bg-white rounded-3xl p-6 sm:p-8 border border-gray-200 shadow-sm space-y-6">
          <div className="border-b border-gray-100 pb-5">
            <h2 className="text-xl font-extrabold text-gray-900 flex items-center gap-2">
              <KeyRound className="w-6 h-6 text-emerald-600" />
              Passwordless Authentication Status
            </h2>
            <p className="text-xs text-gray-500 mt-1">
              Active session details, cryptographic verification method, and account controls.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-5 bg-gray-50 rounded-2xl border border-gray-100 space-y-3">
              <span className="text-xs font-bold text-gray-500 uppercase tracking-wider block">
                User Account
              </span>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold">
                  <UserCheck className="w-5 h-5" />
                </div>
                <div>
                  <div className="font-extrabold text-gray-900 text-sm">{user?.email}</div>
                  <div className="text-[11px] text-emerald-600 font-bold flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Verified Account
                  </div>
                </div>
              </div>
              <div className="pt-2 text-xs text-gray-500 border-t border-gray-200/60">
                User ID: #{user?.id} • Active Session
              </div>
            </div>

            <div className="p-5 bg-gray-50 rounded-2xl border border-gray-100 space-y-3">
              <span className="text-xs font-bold text-gray-500 uppercase tracking-wider block">
                Security Architecture
              </span>
              <ul className="text-xs text-gray-600 space-y-1.5 leading-relaxed">
                <li>• <strong>Cryptographic 6-Digit OTP:</strong> Single-use code with 5-minute expiry.</li>
                <li>• <strong>Passwordless Security:</strong> No password storage eliminates credential stuffing.</li>
                <li>• <strong>Keyed HMAC Hashing:</strong> OTP codes are never stored in plaintext on disk.</li>
              </ul>
            </div>
          </div>

          <div className="pt-2 flex items-center justify-between border-t border-gray-100">
            <span className="text-xs text-gray-500">Need to switch accounts or end your session?</span>
            <button
              onClick={logout}
              className="px-4 py-2 bg-red-50 hover:bg-red-100 text-red-600 font-bold text-xs rounded-xl transition-colors flex items-center gap-1.5 cursor-pointer"
            >
              <LogOut className="w-4 h-4" />
              <span>Log Out</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
