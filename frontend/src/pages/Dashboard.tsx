import React, { useEffect, useState } from 'react';
import { 
  Video, Folder, Play, Clock, Plus, 
  CheckCircle2, Sparkles, Layers, 
  ChevronRight, Share2, ShieldCheck, Image,
  ArrowRight, Film, Wand2
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

export default function Dashboard() {
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    axios.get(`${API_URL}/projects/`)
      .then(res => {
        setProjects(res.data);
      })
      .catch(err => {
        console.error('Error fetching dashboard projects:', err);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const totalProjects = projects.length;
  const completedVideos = projects.filter(p => p.status === 'Completed').length;
  const inProgressJobs = projects.filter(p => ['Rendering', 'Planning', 'Ready'].includes(p.status)).length;
  const totalAssets = projects.reduce((acc, p) => acc + (Array.isArray(p.scenes) ? p.scenes.length : 0), 0) + completedVideos;

  const getVideoUrl = (path: string) => {
    if (!path) return '';
    const normalized = path.replace(/\\/g, '/');
    const storageIndex = normalized.indexOf('storage/');
    if (storageIndex !== -1) {
      return `http://localhost:8000/${normalized.substring(storageIndex)}`;
    }
    return `http://localhost:8000/${normalized}`;
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'Completed':
        return {
          badge: 'bg-emerald-50 text-emerald-700 border-emerald-200/80',
          dot: 'bg-emerald-500',
          label: 'Ready to Post'
        };
      case 'Ready':
        return {
          badge: 'bg-indigo-50 text-indigo-700 border-indigo-200/80',
          dot: 'bg-indigo-500',
          label: 'Script Ready'
        };
      case 'Rendering':
        return {
          badge: 'bg-amber-50 text-amber-700 border-amber-200/80 animate-pulse',
          dot: 'bg-amber-500',
          label: 'Rendering...'
        };
      case 'Planning':
        return {
          badge: 'bg-purple-50 text-purple-700 border-purple-200/80',
          dot: 'bg-purple-500',
          label: 'Planning'
        };
      case 'Failed':
        return {
          badge: 'bg-rose-50 text-rose-700 border-rose-200/80',
          dot: 'bg-rose-500',
          label: 'Failed'
        };
      default:
        return {
          badge: 'bg-slate-100 text-slate-700 border-slate-200',
          dot: 'bg-slate-400',
          label: status
        };
    }
  };

  return (
    <div className="p-6 md:p-10 max-w-7xl mx-auto space-y-10 animate-fadeIn text-slate-900 font-sans">
      {/* Studio Hero Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-2">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-white border border-slate-200/80 rounded-full text-xs font-semibold text-slate-700 shadow-2xs">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>Qoneqt AI Content Studio</span>
            <span className="text-slate-300">•</span>
            <span className="text-indigo-600 font-bold">Studio Hub</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight leading-tight">
            Produce studio-grade videos in minutes.
          </h1>
          <p className="text-slate-500 text-sm sm:text-base max-w-2xl font-normal leading-relaxed">
            Transform scripts, photos, and concepts into publish-ready video stories with natural AI voice narration and synchronized captions.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-3 shrink-0">
          <Link 
            to="/assets" 
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-white hover:bg-slate-50 text-slate-700 hover:text-slate-900 font-semibold rounded-xl border border-slate-200/90 shadow-2xs transition-all text-sm"
          >
            <Image className="w-4 h-4 text-orange-500" />
            <span>Image-to-Video</span>
          </Link>
          <Link 
            to="/create" 
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl shadow-xs transition-all text-sm"
          >
            <Plus className="w-4 h-4" />
            <span>Create Video</span>
          </Link>
        </div>
      </div>

      {/* Studio Creation Hub Cards (Aesthetic Quick Access) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Card 1: Image to Video */}
        <Link 
          to="/assets"
          className="group p-6 bg-white rounded-2xl border border-slate-200/80 shadow-2xs hover:shadow-md hover:border-orange-300 transition-all duration-200 flex flex-col justify-between"
        >
          <div className="space-y-3">
            <div className="w-10 h-10 rounded-xl bg-orange-50 text-orange-600 border border-orange-100 flex items-center justify-center group-hover:scale-105 transition-transform">
              <Image className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 group-hover:text-orange-600 transition-colors">
                Image-to-Video Studio
              </h3>
              <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                Upload photos & landmarks (JPG, PNG, JFIF). AI auto-identifies subjects, generates custom narrations, and applies camera motion.
              </p>
            </div>
          </div>
          <div className="pt-4 mt-2 border-t border-slate-100 flex items-center justify-between text-xs font-bold text-orange-600">
            <span>Launch Image Studio</span>
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </div>
        </Link>

        {/* Card 2: Multi-Scene Video Generator */}
        <Link 
          to="/create"
          className="group p-6 bg-white rounded-2xl border border-slate-200/80 shadow-2xs hover:shadow-md hover:border-indigo-300 transition-all duration-200 flex flex-col justify-between"
        >
          <div className="space-y-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 border border-indigo-100 flex items-center justify-center group-hover:scale-105 transition-transform">
              <Wand2 className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">
                Prompt to Video Engine
              </h3>
              <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                Enter any topic or prompt. The AI scriptwriter crafts full scenes, timing, captions, and ready-to-post hashtags.
              </p>
            </div>
          </div>
          <div className="pt-4 mt-2 border-t border-slate-100 flex items-center justify-between text-xs font-bold text-indigo-600">
            <span>Start Generator</span>
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </div>
        </Link>

        {/* Card 3: Security & Metadata Sanitizer */}
        <Link 
          to="/security"
          className="group p-6 bg-white rounded-2xl border border-slate-200/80 shadow-2xs hover:shadow-md hover:border-emerald-300 transition-all duration-200 flex flex-col justify-between"
        >
          <div className="space-y-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 border border-emerald-100 flex items-center justify-center group-hover:scale-105 transition-transform">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 group-hover:text-emerald-600 transition-colors">
                Media Sanitizer & Privacy
              </h3>
              <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                Inspect SHA-256 byte fingerprints, verify content integrity, and strip private camera metadata before publishing.
              </p>
            </div>
          </div>
          <div className="pt-4 mt-2 border-t border-slate-100 flex items-center justify-between text-xs font-bold text-emerald-600">
            <span>Security Center</span>
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </div>
        </Link>
      </div>

      {/* Unified Studio Metrics Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
        {[
          { 
            title: 'Total Projects', 
            count: totalProjects, 
            subtext: `${completedVideos} completed videos`,
            icon: Folder, 
            iconClass: 'text-slate-700 bg-slate-100'
          },
          { 
            title: 'Videos Created', 
            count: completedVideos, 
            subtext: 'Ready to post & download',
            icon: Video, 
            iconClass: 'text-emerald-600 bg-emerald-50'
          },
          { 
            title: 'Active Workflows', 
            count: inProgressJobs, 
            subtext: 'Scripts & storyboard drafting',
            icon: Play, 
            iconClass: 'text-amber-600 bg-amber-50'
          },
          { 
            title: 'Media Scenes & Assets', 
            count: totalAssets, 
            subtext: 'Visuals, voice & audio clips',
            icon: Layers, 
            iconClass: 'text-indigo-600 bg-indigo-50'
          },
        ].map((stat, i) => (
          <div 
            key={i} 
            className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-2xs hover:shadow-xs transition-all relative overflow-hidden"
          >
            <div className="flex items-center justify-between mb-3">
              <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${stat.iconClass}`}>
                <stat.icon className="w-4 h-4" />
              </div>
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                Live
              </span>
            </div>

            <h3 className="text-slate-500 text-xs font-semibold uppercase tracking-wider mb-1">{stat.title}</h3>
            <p className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              {loading ? (
                <span className="inline-block w-8 h-7 bg-slate-100 rounded animate-pulse"></span>
              ) : (
                stat.count
              )}
            </p>
            <p className="text-[11px] text-slate-400 mt-1 font-medium">{stat.subtext}</p>
          </div>
        ))}
      </div>
      
      {/* Recent Projects Gallery Section */}
      <div className="space-y-5">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-slate-900 tracking-tight">Recent Projects</h2>
            <p className="text-xs text-slate-500 mt-0.5">Your latest video creations, status, and ready-to-post copy</p>
          </div>
          <Link 
            to="/projects" 
            className="inline-flex items-center gap-1.5 text-xs font-bold text-indigo-600 hover:text-indigo-700 bg-indigo-50/70 hover:bg-indigo-100/70 px-3 py-1.5 rounded-lg transition-all"
          >
            <span>View all ({totalProjects})</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>
        
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((n) => (
              <div key={n} className="bg-white rounded-2xl border border-slate-200/80 p-5 space-y-4 animate-pulse">
                <div className="h-36 bg-slate-100 rounded-xl"></div>
                <div className="h-4 bg-slate-100 rounded w-3/4"></div>
                <div className="h-3 bg-slate-100 rounded w-1/2"></div>
              </div>
            ))}
          </div>
        ) : projects.length === 0 ? (
          <div className="bg-white rounded-2xl border border-dashed border-slate-200 p-12 text-center text-slate-500">
            <div className="w-14 h-14 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto mb-3">
              <Film className="w-7 h-7" />
            </div>
            <h4 className="text-base font-bold text-slate-900 mb-1">No projects created yet</h4>
            <p className="text-xs text-slate-500 max-w-sm mx-auto mb-5 leading-relaxed">
              Start by uploading your images in Image-to-Video or write a prompt to produce your first high-converting video.
            </p>
            <div className="flex items-center justify-center gap-3">
              <Link 
                to="/assets" 
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-white hover:bg-slate-50 text-slate-700 font-semibold text-xs rounded-xl border border-slate-200 shadow-2xs transition-all"
              >
                <Image className="w-3.5 h-3.5 text-orange-500" /> Image-to-Video
              </Link>
              <Link 
                to="/create" 
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-xl shadow-xs transition-all"
              >
                <Plus className="w-3.5 h-3.5" /> Create Video
              </Link>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {projects.slice(0, 6).map((project: any) => {
              const statusInfo = getStatusBadge(project.status);
              const hasVideo = Boolean(project.output_path);

              return (
                <div 
                  key={project.id} 
                  onClick={() => navigate(`/projects/${project.id}`)}
                  className="bg-white rounded-2xl border border-slate-200/80 overflow-hidden shadow-2xs hover:shadow-md hover:border-indigo-300 transition-all duration-200 group cursor-pointer flex flex-col"
                >
                  {/* Card Thumbnail / Preview */}
                  <div className="relative h-40 bg-slate-950 overflow-hidden flex items-center justify-center">
                    {hasVideo ? (
                      <video 
                        src={getVideoUrl(project.output_path)} 
                        preload="metadata"
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500 opacity-90"
                      />
                    ) : (
                      <div className="w-full h-full flex flex-col items-center justify-center bg-gradient-to-br from-slate-900 to-slate-800 text-slate-500 group-hover:text-indigo-400 transition-colors">
                        <Video className="w-10 h-10 mb-1 group-hover:scale-110 transition-transform text-slate-600 group-hover:text-indigo-400" />
                        <span className="text-[10px] font-medium text-slate-400">
                          {project.aspect_ratio || '9:16'} • {project.duration || 60}s
                        </span>
                      </div>
                    )}

                    <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent pointer-events-none"></div>

                    {/* Status Badge */}
                    <div className="absolute top-2.5 left-2.5">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold border backdrop-blur-md bg-white/95 shadow-2xs ${statusInfo.badge}`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${statusInfo.dot}`}></span>
                        {statusInfo.label}
                      </span>
                    </div>

                    {/* Platform Tag */}
                    <div className="absolute top-2.5 right-2.5">
                      <span className="px-2 py-0.5 rounded-md text-[9px] font-extrabold uppercase tracking-wider bg-black/60 text-white backdrop-blur-md">
                        {project.platform || 'Shorts'}
                      </span>
                    </div>

                    {/* Title overlay */}
                    <div className="absolute bottom-2.5 left-3 right-3 pointer-events-none">
                      <h4 className="font-bold text-white text-sm truncate">
                        {project.topic || 'Untitled Project'}
                      </h4>
                      <p className="text-slate-300 text-[11px] truncate">
                        {project.strategy?.title || project.title || project.topic}
                      </p>
                    </div>
                  </div>

                  {/* Card Body */}
                  <div className="p-4 flex-1 flex flex-col justify-between space-y-3">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-xs text-slate-500">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5 text-slate-400" />
                          {project.duration || 60}s duration
                        </span>
                        <span className="font-medium text-slate-400">
                          {project.audience || 'General'}
                        </span>
                      </div>

                      {project.social_post && (
                        <div className="inline-flex items-center gap-1.5 px-2 py-1 bg-indigo-50 border border-indigo-100/80 rounded-md text-[11px] font-semibold text-indigo-700">
                          <Share2 className="w-3 h-3 text-indigo-600" />
                          <span>Captions ready</span>
                        </div>
                      )}
                    </div>

                    {/* Bottom Action Footer */}
                    <div className="pt-2.5 border-t border-slate-100 flex items-center justify-between">
                      <span className="text-xs font-bold text-indigo-600 group-hover:text-indigo-700 flex items-center gap-1">
                        Open Project <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                      </span>

                      {project.status === 'Completed' && (
                        <span className="text-xs font-semibold text-emerald-600 flex items-center gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5" /> Ready
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
