import React, { useState } from 'react';
import { 
  FileText, 
  Sparkles, 
  Copy, 
  Check, 
  ChevronDown, 
  ChevronUp, 
  LayoutGrid, 
  Hash, 
  Eye, 
  Clock,
  Layers,
  Volume2
} from 'lucide-react';

export default function ContentPlanView({ project }) {
  const [copiedKey, setCopiedKey] = useState(null);
  const [expandedScenes, setExpandedScenes] = useState({ 1: true });

  const copyToClipboard = (text, key) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const toggleScene = (num) => {
    setExpandedScenes(prev => ({
      ...prev,
      [num]: !prev[num]
    }));
  };

  if (!project) return null;

  return (
    <div className="space-y-4">
      {/* 1. Title & Hook Card */}
      <div className="bg-surface rounded-2xl p-5 border border-border space-y-4 shadow-sm">
        {/* Title */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] font-mono font-bold tracking-wider text-primary uppercase">
              CONTENT TITLE
            </span>
            <button
              onClick={() => copyToClipboard(project.title || '', 'title')}
              className="text-text-secondary hover:text-text-primary p-1 rounded transition-colors"
              title="Copy Title"
            >
              {copiedKey === 'title' ? <Check className="w-3.5 h-3.5 text-success" /> : <Copy className="w-3.5 h-3.5" />}
            </button>
          </div>
          <h2 className="text-lg font-bold text-text-primary tracking-tight">
            {project.title || project.topic}
          </h2>
        </div>

        {/* Hook */}
        <div className="p-3.5 rounded-xl bg-surface-secondary border border-border">
          <div className="flex items-center justify-between mb-1.5">
            <div className="flex items-center space-x-1.5 text-accent">
              <Sparkles className="w-3.5 h-3.5" />
              <span className="text-[11px] font-bold uppercase tracking-wider font-mono">
                ATTENTION HOOK (0-3 SECONDS)
              </span>
            </div>
            <button
              onClick={() => copyToClipboard(project.hook || '', 'hook')}
              className="text-text-secondary hover:text-text-primary p-1 rounded transition-colors"
              title="Copy Hook"
            >
              {copiedKey === 'hook' ? <Check className="w-3.5 h-3.5 text-success" /> : <Copy className="w-3.5 h-3.5" />}
            </button>
          </div>
          <p className="text-xs text-text-primary leading-relaxed italic">
            "{project.hook || 'Analyzing hook...'}"
          </p>
        </div>
      </div>

      {/* 2. Full Script Card */}
      <div className="bg-surface rounded-2xl p-5 border border-border space-y-3 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <FileText className="w-4 h-4 text-primary" />
            <span className="text-xs font-bold uppercase tracking-wider text-text-primary font-mono">
              FULL NARRATION SCRIPT
            </span>
          </div>
          <button
            onClick={() => copyToClipboard(project.script || '', 'script')}
            className="flex items-center space-x-1 text-text-secondary hover:text-text-primary text-xs px-2 py-1 rounded bg-surface-secondary transition-colors"
          >
            {copiedKey === 'script' ? (
              <>
                <Check className="w-3.5 h-3.5 text-success" />
                <span className="text-[11px] text-success">Copied</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5" />
                <span className="text-[11px]">Copy Script</span>
              </>
            )}
          </button>
        </div>
        <div className="p-3.5 rounded-xl bg-surface-secondary border border-border text-xs text-text-secondary leading-relaxed">
          {project.script || 'Script is being synthesized...'}
        </div>
      </div>

      {/* 3. Scene-By-Scene Plan (Expandable Cards) */}
      <div className="bg-surface rounded-2xl p-5 border border-border space-y-3 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <LayoutGrid className="w-4 h-4 text-primary" />
            <span className="text-xs font-bold uppercase tracking-wider text-text-primary font-mono">
              SCENE-BY-SCENE PRODUCTION BLUEPRINT ({project.scenes?.length || 0})
            </span>
          </div>
        </div>

        <div className="space-y-2.5 pt-1">
          {project.scenes && project.scenes.length > 0 ? (
            project.scenes.map((sc) => {
              const isOpen = expandedScenes[sc.scene_number];
              return (
                <div 
                  key={sc.id || sc.scene_number}
                  className="rounded-xl border border-border bg-surface-secondary overflow-hidden transition-all"
                >
                  {/* Scene Accordion Header */}
                  <div
                    onClick={() => toggleScene(sc.scene_number)}
                    className="p-3.5 flex items-center justify-between cursor-pointer hover:bg-border/50 transition-colors"
                  >
                    <div className="flex items-center space-x-3">
                      <span className="w-6 h-6 rounded-md bg-primary/10 text-primary flex items-center justify-center font-mono font-bold text-xs">
                        {sc.scene_number}
                      </span>
                      <div>
                        <span className="text-xs font-semibold text-text-primary block">
                          {sc.on_screen_text || `Scene ${sc.scene_number}`}
                        </span>
                        <span className="text-[10px] text-text-secondary flex items-center space-x-2">
                          <span className="flex items-center space-x-1">
                            <Clock className="w-3 h-3 text-text-secondary" />
                            <span>{sc.duration}s</span>
                          </span>
                          <span>•</span>
                          <span>Transition: {sc.transition || 'fade'}</span>
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      {sc.visual_path && (
                        <span className="text-[9px] px-1.5 py-0.5 rounded bg-success/10 text-success font-mono">
                          VISUAL READY
                        </span>
                      )}
                      {isOpen ? (
                        <ChevronUp className="w-4 h-4 text-text-secondary" />
                      ) : (
                        <ChevronDown className="w-4 h-4 text-text-secondary" />
                      )}
                    </div>
                  </div>

                  {/* Scene Accordion Body */}
                  {isOpen && (
                    <div className="p-3.5 border-t border-border bg-surface space-y-3 text-xs">
                      {/* Narration */}
                      <div>
                        <span className="text-[10px] font-mono font-bold text-text-secondary uppercase flex items-center space-x-1 mb-1">
                          <Volume2 className="w-3 h-3 text-primary" />
                          <span>VOICEOVER NARRATION</span>
                        </span>
                        <p className="text-text-primary bg-surface-secondary p-2.5 rounded-lg border border-border">
                          {sc.narration}
                        </p>
                      </div>

                      {/* Visual Prompt */}
                      <div>
                        <span className="text-[10px] font-mono font-bold text-text-secondary uppercase flex items-center space-x-1 mb-1">
                          <Eye className="w-3 h-3 text-primary" />
                          <span>VISUAL DIRECTIVE & GRAPHIC PROMPT</span>
                        </span>
                        <p className="text-text-secondary bg-surface-secondary p-2.5 rounded-lg border border-border font-mono text-[11px]">
                          {sc.visual_prompt}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              );
            })
          ) : (
            <div className="p-4 rounded-xl bg-surface text-center text-xs text-text-secondary border border-border">
              No scenes created yet.
            </div>
          )}
        </div>
      </div>

      {/* 4. Captions & Hashtags Card */}
      <div className="bg-surface rounded-2xl p-5 border border-border space-y-4 shadow-sm">
        {/* Post Caption */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[10px] font-mono font-bold tracking-wider text-text-secondary uppercase">
              PUBLISH READY CAPTION
            </span>
            <button
              onClick={() => copyToClipboard(project.caption || '', 'caption')}
              className="text-text-secondary hover:text-text-primary p-1 rounded transition-colors"
            >
              {copiedKey === 'caption' ? <Check className="w-3.5 h-3.5 text-success" /> : <Copy className="w-3.5 h-3.5" />}
            </button>
          </div>
          <div className="p-3 rounded-xl bg-surface-secondary border border-border text-xs text-text-secondary whitespace-pre-line">
            {project.caption || 'Caption generated for social feed'}
          </div>
        </div>

        {/* Hashtags */}
        {project.hashtags && project.hashtags.length > 0 && (
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[10px] font-mono font-bold tracking-wider text-text-secondary uppercase">
                SUGGESTED HASHTAGS
              </span>
              <button
                onClick={() => copyToClipboard(project.hashtags.join(' '), 'hashtags')}
                className="text-text-secondary hover:text-text-primary p-1 rounded transition-colors"
              >
                {copiedKey === 'hashtags' ? <Check className="w-3.5 h-3.5 text-success" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {project.hashtags.map((tag, i) => (
                <span 
                  key={i}
                  className="px-2.5 py-1 rounded-lg text-xs font-mono font-medium bg-primary/10 text-primary border border-primary/20"
                >
                  {tag.startsWith('#') ? tag : `#${tag}`}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
