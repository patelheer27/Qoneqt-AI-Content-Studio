import React from 'react';
import { 
  CheckCircle2, 
  Loader2, 
  Circle, 
  Brain, 
  FileText, 
  Image as ImageIcon, 
  Mic, 
  Film, 
  Sparkles,
  AlertCircle
} from 'lucide-react';

export default function PipelineTracker({ status, stage, progress = 0, error }) {
  const stages = [
    {
      id: 'analyzing_topic',
      title: 'Topic Analysis',
      subtitle: 'Analyzing topic & intent',
      icon: Brain,
      minProgress: 10
    },
    {
      id: 'ai_planning',
      title: 'AI Planning',
      subtitle: 'Hook & script generation',
      icon: FileText,
      minProgress: 25
    },
    {
      id: 'content_generated',
      title: 'Scene Blueprint',
      subtitle: 'Structured 5-scene timeline',
      icon: Sparkles,
      minProgress: 40
    },
    {
      id: 'generating_visuals',
      title: 'Visual Assets',
      subtitle: '1080x1920 graphic synthesis',
      icon: ImageIcon,
      minProgress: 55
    },
    {
      id: 'generating_voice',
      title: 'Voice & Captions',
      subtitle: 'Neural narration & SRT sync',
      icon: Mic,
      minProgress: 75
    },
    {
      id: 'composing_video',
      title: 'Video Compositor',
      subtitle: 'FFmpeg H.264 / AAC 9:16 MP4',
      icon: Film,
      minProgress: 90
    }
  ];

  const isFailed = status === 'failed';
  const isComplete = status === 'ready' || status === 'published' || progress >= 100;

  return (
    <div className="bg-surface rounded-2xl p-5 border border-border space-y-5 shadow-sm">
      {/* Header and Progress Percentage */}
      <div className="flex items-center justify-between border-b border-border pb-3">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-xs font-bold uppercase tracking-widest text-primary font-mono">
              REAL-TIME PRODUCTION PIPELINE
            </span>
            {status === 'processing' && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-primary/10 text-primary animate-pulse">
                Processing
              </span>
            )}
            {isComplete && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-success/10 text-success">
                Completed
              </span>
            )}
          </div>
          <p className="text-xs text-text-secondary mt-0.5">
            Synchronized AI media execution pipeline
          </p>
        </div>

        <div className="text-right">
          <span className="text-2xl font-black font-mono text-text-primary">
            {progress}%
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-surface-secondary rounded-full h-2 overflow-hidden p-0.5">
        <div 
          className="h-full rounded-full bg-primary transition-all duration-500 ease-out"
          style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
        />
      </div>

      {/* Error Message if any */}
      {isFailed && (
        <div className="p-3.5 rounded-xl bg-error/10 border border-error/30 text-error text-xs flex items-start space-x-2.5">
          <AlertCircle className="w-4 h-4 text-error flex-shrink-0 mt-0.5" />
          <div>
            <span className="font-bold">Pipeline Error:</span> {error || 'Generation encountered an error.'}
          </div>
        </div>
      )}

      {/* Stage Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {stages.map((st, idx) => {
          const Icon = st.icon;
          const isDone = isComplete || progress > st.minProgress;
          const isActive = !isComplete && !isFailed && progress >= st.minProgress - 15 && progress <= st.minProgress;

          return (
            <div 
              key={st.id}
              className={`p-3 rounded-xl border transition-all duration-300 ${
                isDone 
                  ? 'bg-surface-secondary border-success/30 text-text-primary' 
                  : isActive 
                    ? 'bg-surface border-primary text-text-primary ring-1 ring-primary/20 shadow-sm' 
                    : 'bg-surface border-border text-text-secondary'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center space-x-2">
                  <div className={`w-7 h-7 rounded-lg flex items-center justify-center ${
                    isDone 
                      ? 'bg-success/10 text-success' 
                      : isActive 
                        ? 'bg-primary/10 text-primary' 
                        : 'bg-surface-secondary text-text-secondary/60'
                  }`}>
                    <Icon className="w-3.5 h-3.5" />
                  </div>
                  <span className="text-xs font-semibold">{st.title}</span>
                </div>

                {isDone ? (
                  <CheckCircle2 className="w-4 h-4 text-success" />
                ) : isActive ? (
                  <Loader2 className="w-4 h-4 text-primary animate-spin" />
                ) : (
                  <Circle className="w-3.5 h-3.5 text-border" />
                )}
              </div>
              <p className="text-[11px] text-text-secondary leading-tight pl-9">
                {st.subtitle}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
