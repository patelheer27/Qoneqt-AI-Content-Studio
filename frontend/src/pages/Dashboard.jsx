import React, { useState } from 'react';
import { 
  Sparkles, 
  Video, 
  Sliders, 
  Clock, 
  Globe, 
  Smile, 
  ArrowRight, 
  RefreshCw, 
  AlertCircle,
  Play
} from 'lucide-react';
import PipelineTracker from '../components/PipelineTracker';
import VideoPreviewCard from '../components/VideoPreviewCard';
import ContentPlanView from '../components/ContentPlanView';
import ArchitectureBar from '../components/ArchitectureBar';

export default function Dashboard({ 
  currentProject, 
  onGenerate, 
  isGenerating, 
  onRegenerate,
  onPublish,
  isPublishing,
  stats
}) {
  const [topic, setTopic] = useState('');
  const [platform, setPlatform] = useState('Qoneqt Global Feed');
  const [duration, setDuration] = useState(30);
  const [tone, setTone] = useState('Educational');
  const [inputError, setInputError] = useState('');

  const demoTopic = "5 AI trends that will change content creation in 2026";

  const handleUseDemo = () => {
    setTopic(demoTopic);
    setPlatform('Qoneqt Global Feed');
    setDuration(30);
    setTone('Educational');
    setInputError('');
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!topic.trim()) {
      setInputError('Please enter a topic or content idea.');
      return;
    }
    setInputError('');
    onGenerate({
      topic: topic.trim(),
      platform,
      duration: Number(duration),
      tone
    });
  };

  const platforms = ['Qoneqt Global Feed', 'Instagram Reels', 'YouTube Shorts'];
  const durations = [
    { label: '20 sec', value: 20 },
    { label: '30 sec', value: 30 },
    { label: '45 sec', value: 45 },
  ];
  const tones = ['Educational', 'News', 'Energetic', 'Professional'];

  return (
    <div className="space-y-8 pb-16">
      {/* Visual Pipeline Bar */}
      <ArchitectureBar stats={stats} />

      {/* Hero Section */}
      <div className="relative bg-surface rounded-3xl p-6 lg:p-10 border border-border shadow-sm overflow-hidden">
        <div className="relative max-w-4xl mx-auto text-center space-y-4">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5" />
            <span>AI-Powered Video Generation Engine</span>
          </div>

          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black text-text-primary tracking-tight">
            Create Your Next Video
          </h1>

          <p className="text-sm sm:text-base text-text-secondary max-w-2xl mx-auto leading-relaxed">
            Turn a simple idea into a publish-ready social video using AI.
            Instant AI planning, script, voice synthesis, captions, and FFmpeg video composition.
          </p>

          {/* Quick Demo Preset Trigger */}
          <div className="pt-1">
            <button
              type="button"
              onClick={handleUseDemo}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-surface-secondary hover:bg-border text-text-secondary hover:text-text-primary border border-border transition-all hover:scale-105"
            >
              <span>✨ Use Demo Topic:</span>
              <span className="text-primary italic font-mono">"{demoTopic}"</span>
            </button>
          </div>

          {/* Creation Form */}
          <form onSubmit={handleSubmit} className="pt-4 space-y-6 text-left max-w-3xl mx-auto">
            {/* Topic Input Box */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold uppercase tracking-wider text-text-primary font-mono block">
                TOPIC / CONTENT IDEA
              </label>
              <div className="relative">
                <textarea
                  rows={3}
                  value={topic}
                  onChange={(e) => {
                    setTopic(e.target.value);
                    if (inputError) setInputError('');
                  }}
                  placeholder="e.g. 5 AI trends that will change content creation in 2026"
                  className="w-full px-4 py-3.5 rounded-2xl bg-surface border border-[#CBD5E1] focus:border-primary focus:ring-2 focus:ring-primary/20 text-text-primary placeholder-text-secondary/60 text-sm font-sans transition-all resize-none shadow-sm"
                />
              </div>
              {inputError && (
                <p className="text-xs text-error flex items-center space-x-1 mt-1">
                  <AlertCircle className="w-3.5 h-3.5" />
                  <span>{inputError}</span>
                </p>
              )}
            </div>

            {/* Optional Controls Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Platform Selector */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold uppercase tracking-wider text-text-secondary font-mono flex items-center space-x-1.5">
                  <Globe className="w-3.5 h-3.5 text-primary" />
                  <span>PLATFORM</span>
                </label>
                <div className="grid grid-cols-1 gap-1.5">
                  <select
                    value={platform}
                    onChange={(e) => setPlatform(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-surface border border-border text-text-primary text-xs font-medium focus:border-primary focus:ring-1 focus:ring-primary"
                  >
                    {platforms.map((p) => (
                      <option key={p} value={p}>{p}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Duration Selector */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold uppercase tracking-wider text-text-secondary font-mono flex items-center space-x-1.5">
                  <Clock className="w-3.5 h-3.5 text-primary" />
                  <span>DURATION</span>
                </label>
                <div className="grid grid-cols-3 gap-1.5">
                  {durations.map((d) => (
                    <button
                      key={d.value}
                      type="button"
                      onClick={() => setDuration(d.value)}
                      className={`py-2 px-2 rounded-xl text-xs font-semibold transition-all border ${
                        duration === d.value
                          ? 'bg-primary border-primary text-white shadow-sm'
                          : 'bg-surface border-border text-text-secondary hover:text-text-primary hover:bg-surface-secondary'
                      }`}
                    >
                      {d.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Tone Selector */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold uppercase tracking-wider text-text-secondary font-mono flex items-center space-x-1.5">
                  <Smile className="w-3.5 h-3.5 text-primary" />
                  <span>TONE</span>
                </label>
                <select
                  value={tone}
                  onChange={(e) => setTone(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-surface border border-border text-text-primary text-xs font-medium focus:border-primary focus:ring-1 focus:ring-primary"
                >
                  {tones.map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Generate Video Action Button */}
            <div className="pt-2 text-center">
              <button
                type="submit"
                disabled={isGenerating}
                className="w-full py-4 px-6 rounded-2xl bg-accent text-white font-extrabold text-sm sm:text-base tracking-wide flex items-center justify-center space-x-2.5 shadow-sm hover:bg-accent-dark active:scale-[0.99] transition-all disabled:opacity-60 disabled:cursor-not-allowed group"
              >
                {isGenerating ? (
                  <>
                    <RefreshCw className="w-5 h-5 animate-spin" />
                    <span>Orchestrating AI Pipeline...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-5 h-5 text-white group-hover:rotate-12 transition-transform" />
                    <span>Generate Video</span>
                    <ArrowRight className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform" />
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* Live Generation & Result View */}
      {currentProject && (
        <div className="space-y-6 pt-4 animate-in fade-in duration-300">
          {/* Real-time Pipeline Status Bar */}
          <PipelineTracker
            status={currentProject.status}
            stage={currentProject.stage}
            progress={currentProject.progress}
            error={currentProject.error_message}
          />

          {/* Split Screen Layout: Left = Content Plan, Right = Video Preview */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Left: Content Plan & Scene breakdown */}
            <div className="lg:col-span-7 space-y-6">
              <ContentPlanView project={currentProject} />
            </div>

            {/* Right: Video Preview & Publishing */}
            <div className="lg:col-span-5 sticky top-24">
              <VideoPreviewCard
                project={currentProject}
                onRegenerate={onRegenerate}
                onPublish={onPublish}
                isPublishing={isPublishing}
                isPublished={currentProject.status === 'published'}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
