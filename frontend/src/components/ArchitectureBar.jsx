import React from 'react';
import { ArrowRight, Lightbulb, Brain, FileText, LayoutGrid, Image as ImageIcon, Mic, Subtitles, Film, CheckCircle2, Share2 } from 'lucide-react';

export default function ArchitectureBar({ stats }) {
  const steps = [
    { label: 'One Idea', icon: Lightbulb, color: 'text-accent' },
    { label: 'AI Planning', icon: Brain, color: 'text-primary' },
    { label: 'Script', icon: FileText, color: 'text-primary' },
    { label: 'Scenes', icon: LayoutGrid, color: 'text-primary' },
    { label: 'Visuals', icon: ImageIcon, color: 'text-primary' },
    { label: 'Voice', icon: Mic, color: 'text-primary' },
    { label: 'Captions', icon: Subtitles, color: 'text-primary' },
    { label: 'Video (FFmpeg)', icon: Film, color: 'text-primary' },
    { label: 'Publish', icon: Share2, color: 'text-success' },
  ];

  return (
    <div className="w-full space-y-4">
      {/* Concept Pipeline Header */}
      <div className="bg-surface shadow-sm rounded-2xl p-4 lg:p-5 border border-border cursor-default">
        <div className="flex flex-col lg:flex-row items-center justify-between gap-4 mb-4">
          <div>
            <span className="text-[10px] font-bold tracking-widest text-primary uppercase font-mono">
              END-TO-END AUTOMATED PIPELINE
            </span>
            <h3 className="text-sm lg:text-base font-bold text-text-primary tracking-wide">
              FROM ONE IDEA TO A PUBLISH-READY VIDEO
            </h3>
          </div>

          {/* Quick Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-3 w-full lg:w-auto">
            <div className="bg-surface-secondary px-3.5 py-2 rounded-xl border border-border text-center">
              <span className="text-[10px] text-text-secondary uppercase font-medium block">Created</span>
              <span className="text-base font-bold text-text-primary font-mono">{stats?.total || 0}</span>
            </div>
            <div className="bg-surface-secondary px-3.5 py-2 rounded-xl border border-border text-center">
              <span className="text-[10px] text-text-secondary uppercase font-medium block">Published</span>
              <span className="text-base font-bold text-success font-mono">{stats?.published || 0}</span>
            </div>
            <div className="bg-surface-secondary px-3.5 py-2 rounded-xl border border-border text-center">
              <span className="text-[10px] text-text-secondary uppercase font-medium block">Processing</span>
              <span className="text-base font-bold text-primary font-mono">{stats?.processing || 0}</span>
            </div>
            <div className="bg-surface-secondary px-3.5 py-2 rounded-xl border border-border text-center">
              <span className="text-[10px] text-text-secondary uppercase font-medium block">Engine</span>
              <span className="text-xs font-bold text-success font-mono mt-0.5 block">READY ✓</span>
            </div>
          </div>
        </div>

        {/* Visual Pipeline Flow (NON-INTERACTIVE) */}
        <div className="hidden md:flex items-center justify-between overflow-x-auto py-2 px-1">
          {steps.map((st, idx) => {
            const Icon = st.icon;
            return (
              <React.Fragment key={idx}>
                <div className="flex flex-col items-center min-w-[70px] cursor-default">
                  <div className="w-9 h-9 rounded-xl bg-surface-secondary border border-border flex items-center justify-center shadow-sm">
                    <Icon className={`w-4 h-4 ${st.color}`} />
                  </div>
                  <span className="text-[11px] font-medium text-text-secondary mt-2 font-mono whitespace-nowrap">
                    {st.label}
                  </span>
                </div>
                {idx < steps.length - 1 && (
                  <ArrowRight className="w-3.5 h-3.5 text-[#CBD5E1] mx-1 flex-shrink-0" />
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>
    </div>
  );
}
