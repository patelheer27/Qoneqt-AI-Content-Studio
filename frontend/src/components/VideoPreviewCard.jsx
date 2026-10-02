import React, { useRef, useState } from 'react';
import { 
  Play, 
  Pause, 
  Download, 
  Share2, 
  RefreshCw, 
  Film, 
  Sparkles, 
  Check, 
  Volume2, 
  Maximize2 
} from 'lucide-react';

export default function VideoPreviewCard({ 
  project, 
  onRegenerate, 
  onPublish, 
  isPublishing,
  isPublished 
}) {
  const videoRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);

  const togglePlay = () => {
    if (!videoRef.current) return;
    if (videoRef.current.paused) {
      videoRef.current.play();
      setIsPlaying(true);
    } else {
      videoRef.current.pause();
      setIsPlaying(false);
    }
  };

  const videoSrc = project?.video_url || (project?.id ? `/api/projects/${project.id}/video` : null);

  return (
    <div className="bg-surface rounded-3xl p-5 lg:p-6 border border-border space-y-5 shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border pb-3">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 rounded-lg bg-primary/10 text-primary flex items-center justify-center">
            <Film className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-text-primary tracking-wide">
              VIDEO PREVIEW
            </h4>
            <p className="text-[11px] text-text-secondary">
              9:16 Vertical Video (1080 x 1920)
            </p>
          </div>
        </div>

        <span className="text-[10px] font-mono font-bold uppercase tracking-widest px-2.5 py-1 rounded-full bg-success/10 text-success border border-success/20">
          H.264 / AAC READY
        </span>
      </div>

      {/* Video Player Container */}
      <div className="relative mx-auto max-w-[340px] aspect-[9/16] bg-surface-secondary rounded-2xl overflow-hidden shadow-sm border border-border group">
        {videoSrc ? (
          <video
            ref={videoRef}
            src={videoSrc}
            controls
            playsInline
            preload="metadata"
            className="w-full h-full object-cover"
            onPlay={() => setIsPlaying(true)}
            onPause={() => setIsPlaying(false)}
          />
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center p-6 text-center text-text-secondary">
            <Film className="w-10 h-10 mb-2 opacity-50" />
            <p className="text-xs">Video is compiling...</p>
          </div>
        )}
      </div>

      {/* Video Metadata */}
      <div className="grid grid-cols-3 gap-2 bg-surface-secondary p-3 rounded-xl border border-border text-center">
        <div>
          <span className="text-[10px] text-text-secondary uppercase block">Duration</span>
          <span className="text-xs font-mono font-bold text-text-primary">{project?.duration || 30}s</span>
        </div>
        <div>
          <span className="text-[10px] text-text-secondary uppercase block">Scenes</span>
          <span className="text-xs font-mono font-bold text-text-primary">{project?.scenes?.length || 5}</span>
        </div>
        <div>
          <span className="text-[10px] text-text-secondary uppercase block">Platform</span>
          <span className="text-xs font-mono font-bold text-primary truncate block">
            {project?.platform?.replace("Qoneqt ", "") || "Global Feed"}
          </span>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="space-y-2.5 pt-1">
        {/* Publish Button */}
        <button
          onClick={onPublish}
          disabled={isPublishing || isPublished}
          className={`w-full py-3 px-4 rounded-xl font-bold text-xs flex items-center justify-center space-x-2 transition-all shadow-sm ${
            isPublished
              ? 'bg-success text-white cursor-default'
              : 'bg-accent text-white hover:bg-accent-dark active:scale-[0.99]'
          }`}
        >
          {isPublished ? (
            <>
              <Check className="w-4 h-4" />
              <span>Published to Qoneqt Global Feed ✓</span>
            </>
          ) : isPublishing ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Publishing to Qoneqt Feed...</span>
            </>
          ) : (
            <>
              <Share2 className="w-4 h-4" />
              <span>Publish to Qoneqt Global Feed</span>
            </>
          )}
        </button>

        {/* Secondary Buttons: Download & Regenerate */}
        <div className="grid grid-cols-2 gap-2">
          {videoSrc && (
            <a
              href={videoSrc}
              download={`qoneqt_${project?.id?.slice(0, 8)}.mp4`}
              className="py-2.5 px-3 rounded-xl bg-surface hover:bg-surface-secondary text-text-primary text-xs font-semibold flex items-center justify-center space-x-1.5 transition-colors border border-border"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download MP4</span>
            </a>
          )}

          <button
            onClick={onRegenerate}
            className="py-2.5 px-3 rounded-xl bg-surface hover:bg-surface-secondary text-text-primary text-xs font-semibold flex items-center justify-center space-x-1.5 transition-colors border border-border"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Regenerate</span>
          </button>
        </div>
      </div>

      {/* Attribution Footer */}
      <div className="text-center pt-1">
        <span className="text-[10px] text-text-secondary font-mono">
          Engineered & Generated by Qoneqt AI Engine
        </span>
      </div>
    </div>
  );
}
