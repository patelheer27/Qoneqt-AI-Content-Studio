import React from 'react';
import { CheckCircle2, Share2, X, ExternalLink, Sparkles, Heart, MessageCircle, Repeat2, Bookmark } from 'lucide-react';

export default function PublishModal({ isOpen, onClose, publishData, project }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-text-primary/30 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-lg bg-surface rounded-3xl p-6 border border-border shadow-xl space-y-5">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-1.5 rounded-full text-text-secondary hover:text-text-primary bg-surface-secondary transition-colors"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Success Header */}
        <div className="text-center space-y-2">
          <div className="w-12 h-12 mx-auto rounded-2xl bg-success/10 text-success flex items-center justify-center border border-success/20">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <span className="text-[10px] font-mono font-bold tracking-widest text-success uppercase">
            PROTOTYPE PUBLISHING WORKFLOW
          </span>
          <h3 className="text-lg font-bold text-text-primary">
            Published to Qoneqt Global Feed ✓
          </h3>
          <p className="text-xs text-text-secondary max-w-sm mx-auto">
            Your AI-composed video is now live on the Qoneqt discovery network with automated metadata and hashtags.
          </p>
        </div>

        {/* Live Feed Card Simulation */}
        <div className="bg-surface-secondary rounded-2xl p-4 border border-border space-y-3">
          {/* Post Header */}
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-full bg-primary flex items-center justify-center text-xs font-bold text-white shadow-sm">
              QT
            </div>
            <div>
              <div className="flex items-center space-x-1.5">
                <span className="text-xs font-bold text-text-primary">Qoneqt Creator</span>
                <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-primary/10 text-primary font-mono border border-primary/20">
                  Verified AI
                </span>
              </div>
              <span className="text-[10px] text-text-secondary">@creator_studio • Just now</span>
            </div>
          </div>

          {/* Post Content */}
          <p className="text-xs text-text-primary line-clamp-3 leading-relaxed">
            {project?.caption || project?.hook || project?.topic}
          </p>

          {/* Video Preview Miniature */}
          {publishData?.video_url && (
            <div className="relative rounded-xl overflow-hidden aspect-video bg-black flex items-center justify-center border border-border">
              <video
                src={publishData.video_url}
                controls
                playsInline
                className="w-full h-full object-cover"
              />
            </div>
          )}

          {/* Social Feedback Simulation */}
          <div className="flex items-center justify-between pt-2 border-t border-border text-text-secondary text-xs">
            <div className="flex items-center space-x-1 hover:text-error cursor-pointer transition-colors">
              <Heart className="w-3.5 h-3.5" />
              <span className="text-[11px] font-mono">1</span>
            </div>
            <div className="flex items-center space-x-1 hover:text-primary cursor-pointer transition-colors">
              <MessageCircle className="w-3.5 h-3.5" />
              <span className="text-[11px] font-mono">0</span>
            </div>
            <div className="flex items-center space-x-1 hover:text-success cursor-pointer transition-colors">
              <Repeat2 className="w-3.5 h-3.5" />
              <span className="text-[11px] font-mono">0</span>
            </div>
            <div className="flex items-center space-x-1 hover:text-primary cursor-pointer transition-colors">
              <Bookmark className="w-3.5 h-3.5" />
            </div>
          </div>
        </div>

        {/* Dismiss Button */}
        <button
          onClick={onClose}
          className="w-full py-2.5 px-4 rounded-xl bg-surface hover:bg-surface-secondary border border-border text-text-primary font-semibold text-xs transition-colors shadow-sm"
        >
          Close & Return to Studio
        </button>
      </div>
    </div>
  );
}
