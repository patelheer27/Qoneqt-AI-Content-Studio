import React from 'react';
import { Sparkles, Video, FolderGit2, Zap, Layers } from 'lucide-react';

export default function Header({ currentTab, setCurrentTab, projectCount = 0, health }) {
  const isLive = health?.gemini_configured && !health?.demo_mode;

  return (
    <header className="sticky top-0 z-50 bg-surface border-b border-border px-6 lg:px-10 py-3.5 backdrop-blur-xl">
      <div className="w-full mx-auto flex items-center justify-between">
        {/* Brand */}
        <div 
          onClick={() => setCurrentTab('dashboard')}
          className="flex items-center space-x-3 cursor-pointer group"
        >
          <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center transition-transform duration-300 group-hover:scale-105 shadow-sm">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-extrabold text-xl tracking-wider text-text-primary font-mono">QONEQT</span>
              <span className="text-[10px] uppercase font-bold tracking-widest px-2 py-0.5 rounded-full bg-surface-secondary text-text-secondary border border-border">
                PROTOTYPE
              </span>
            </div>
            <p className="text-[11px] text-text-secondary uppercase tracking-widest font-semibold">
              AI Content Studio
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="hidden md:flex items-center space-x-1 bg-surface p-1 rounded-xl border border-border">
          <button
            onClick={() => setCurrentTab('dashboard')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
              currentTab === 'dashboard'
                ? 'bg-primary-light text-primary shadow-sm'
                : 'text-text-sub hover:text-text-primary hover:bg-primary-light'
            }`}
          >
            <Zap className="w-3.5 h-3.5" />
            <span>Dashboard</span>
          </button>

          <button
            onClick={() => setCurrentTab('create')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
              currentTab === 'create'
                ? 'bg-primary-light text-primary shadow-sm'
                : 'text-text-sub hover:text-text-primary hover:bg-primary-light'
            }`}
          >
            <Video className="w-3.5 h-3.5" />
            <span>Create Video</span>
          </button>

          <button
            onClick={() => setCurrentTab('projects')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
              currentTab === 'projects'
                ? 'bg-primary-light text-primary shadow-sm'
                : 'text-text-sub hover:text-text-primary hover:bg-primary-light'
            }`}
          >
            <FolderGit2 className="w-3.5 h-3.5" />
            <span>Projects</span>
            {projectCount > 0 && (
              <span className={`ml-1 px-1.5 py-0.2 rounded-full text-[10px] ${
                currentTab === 'projects' ? 'bg-primary text-white' : 'bg-surface-secondary text-text-sub'
              }`}>
                {projectCount}
              </span>
            )}
          </button>
        </nav>

        {/* Right Side: AI Engine Status & Profile */}
        <div className="flex items-center space-x-3">
          {/* Engine Status Badge */}
          <div className="hidden sm:flex items-center space-x-2 px-3 py-1.5 rounded-full bg-surface-secondary border border-border">
            <span className="relative flex h-2 w-2">
              <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                isLive ? 'bg-success' : 'bg-primary'
              }`}></span>
              <span className={`relative inline-flex rounded-full h-2 w-2 ${
                isLive ? 'bg-success' : 'bg-primary'
              }`}></span>
            </span>
            <span className="text-[11px] font-mono text-text-secondary">
              {isLive ? 'GEMINI 2.5 • LIVE' : 'AI ENGINE • READY'}
            </span>
          </div>

          {/* User Profile */}
          <div className="flex items-center space-x-2.5 pl-2 border-l border-border">
            <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-xs font-bold text-white shadow-sm">
              QT
            </div>
            <div className="hidden xl:block text-left">
              <p className="text-xs font-semibold text-text-primary leading-tight">Qoneqt Creator</p>
              <p className="text-[10px] text-text-secondary leading-tight">Studio Pass</p>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
