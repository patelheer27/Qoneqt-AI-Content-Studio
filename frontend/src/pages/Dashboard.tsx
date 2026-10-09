import React, { useEffect, useState } from 'react';
import { 
  Video, Folder, Upload, Play, Clock, MoreVertical, Plus, 
  CheckCircle2, AlertCircle, ArrowUpRight, Sparkles, Layers, 
  ChevronRight, Download, Share2, ShieldCheck, FileCheck, Eraser
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
          badge: 'bg-emerald-50 text-emerald-700 border-emerald-200',
          dot: 'bg-emerald-500',
          label: 'Ready to Post'
        };
      case 'Ready':
        return {
          badge: 'bg-blue-50 text-blue-700 border-blue-200',
          dot: 'bg-blue-500',
          label: 'Script Ready'
        };
      case 'Rendering':
        return {
          badge: 'bg-amber-50 text-amber-700 border-amber-200 animate-pulse',
          dot: 'bg-amber-500',
          label: 'Rendering...'
        };
      case 'Planning':
        return {
          badge: 'bg-purple-50 text-purple-700 border-purple-200',
          dot: 'bg-purple-500',
          label: 'Planning'
        };
      case 'Failed':
        return {
          badge: 'bg-rose-50 text-rose-700 border-rose-200',
          dot: 'bg-rose-500',
          label: 'Failed'
        };
      default:
        return {
          badge: 'bg-gray-50 text-gray-700 border-gray-200',
          dot: 'bg-gray-400',
          label: status
        };
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-10 animate-fadeIn">
      {/* Hero Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-2">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-blue-50 border border-blue-100 rounded-full text-xs font-bold text-blue-700 uppercase tracking-wider mb-2">
            <Sparkles className="w-3.5 h-3.5 text-blue-600" />
            Qoneqt AI Content Studio
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-gray-900 tracking-tight">
            Turn ideas into <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 via-indigo-600 to-orange-500">viral videos.</span>
          </h2>
          <p className="text-gray-500 mt-1 text-sm sm:text-base">
            Create, manage and publish high-converting video content with AI-assisted captions and hashtags.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to="/security"
            className="inline-flex items-center justify-center gap-2 px-5 py-3.5 bg-white hover:bg-gray-50 text-gray-800 font-bold rounded-2xl border border-gray-200 shadow-sm transition-all text-sm shrink-0"
          >
            <ShieldCheck className="w-4 h-4 text-blue-600" />
            Security & Privacy
          </Link>
          <Link 
            to="/create" 
            className="inline-flex items-center justify-center gap-2.5 px-6 py-3.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-bold rounded-2xl shadow-lg shadow-blue-500/25 transition-all transform hover:-translate-y-0.5 shrink-0"
          >
            <Plus className="w-5 h-5" />
            Create Video
          </Link>
        </div>
      </div>

      {/* Security & Integrity Quick Banner */}
      <div className="p-5 bg-gradient-to-r from-blue-900 via-indigo-900 to-slate-900 rounded-3xl text-white flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-lg shadow-blue-950/10">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-white/10 backdrop-blur-md flex items-center justify-center text-blue-300 shrink-0">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <h4 className="font-extrabold text-sm sm:text-base">Video Integrity & Metadata Sanitizer Tools</h4>
            <p className="text-xs text-blue-200/80 mt-0.5">
              Verify SHA-256 byte fingerprints and strip identifying container metadata before publishing.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Link
            to="/security"
            className="px-4 py-2 bg-white text-gray-900 hover:bg-blue-50 text-xs font-bold rounded-xl transition-all shadow-sm flex items-center gap-1.5"
          >
            <span>Launch Security Center</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      
      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          { 
            title: 'Total Projects', 
            count: totalProjects, 
            subtext: `${completedVideos} finished`,
            icon: Folder, 
            bg: 'bg-blue-500/10', 
            text: 'text-blue-600',
            gradient: 'from-blue-500 to-indigo-600'
          },
          { 
            title: 'Videos Created', 
            count: completedVideos, 
            subtext: 'Ready to download & post',
            icon: Video, 
            bg: 'bg-emerald-500/10', 
            text: 'text-emerald-600',
            gradient: 'from-emerald-500 to-teal-600'
          },
          { 
            title: 'Active Workflows', 
            count: inProgressJobs, 
            subtext: 'Scripts & storyboard drafting',
            icon: Play, 
            bg: 'bg-amber-500/10', 
            text: 'text-amber-600',
            gradient: 'from-amber-500 to-orange-600'
          },
          { 
            title: 'Media Scenes & Assets', 
            count: totalAssets, 
            subtext: 'Visuals, audio & voice clips',
            icon: Layers, 
            bg: 'bg-purple-500/10', 
            text: 'text-purple-600',
            gradient: 'from-purple-500 to-pink-600'
          },
        ].map((stat, i) => (
          <div 
            key={i} 
            className="bg-white p-6 rounded-3xl border border-gray-100 shadow-sm hover:shadow-md transition-all relative overflow-hidden group">
            <div className={`absolute top-0 right-0 w-28 h-28 bg-gradient-to-bl ${stat.gradient} opacity-5 -mr-8 -mt-8 rounded-full group-hover:scale-125 transition-transform duration-500`}></div>
            
            <div className="flex items-center justify-between mb-4">
              <div className={`w-12 h-12 rounded-2xl flex items-center justify-center ${stat.bg}`}>
                <stat.icon className={`w-6 h-6 ${stat.text}`} />
              </div>
              <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider">
                Live Stat
              </span>
            </div>

            <h3 className="text-gray-500 text-xs font-bold uppercase tracking-wider mb-1">{stat.title}</h3>
            <p className="text-3xl sm:text-4xl font-extrabold text-gray-900 tracking-tight">
              {loading ? (
                <span className="inline-block w-8 h-8 bg-gray-200 rounded animate-pulse"></span>
              ) : (
                stat.count
              )}
            </p>
            <p className="text-xs text-gray-400 mt-1 font-medium">{stat.subtext}</p>
          </div>
        ))}
      </div>
      
      {/* Recent Projects Section */}
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-2xl font-extrabold text-gray-900 tracking-tight">Recent Projects</h3>
            <p className="text-xs sm:text-sm text-gray-500">Your latest video creations, status, and ready-to-post copy</p>
          </div>
          <Link 
            to="/projects" 
            className="inline-flex items-center gap-1.5 text-sm font-bold text-blue-600 hover:text-blue-700 bg-blue-50/70 hover:bg-blue-100/70 px-4 py-2 rounded-xl transition-all">
            <span>View all ({totalProjects})</span>
            <ChevronRight className="w-4 h-4" />
          </Link>
        </div>
        
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((n) => (
              <div key={n} className="bg-white rounded-3xl border border-gray-100 p-6 space-y-4 animate-pulse">
                <div className="h-40 bg-gray-100 rounded-2xl"></div>
                <div className="h-4 bg-gray-100 rounded w-3/4"></div>
                <div className="h-3 bg-gray-100 rounded w-1/2"></div>
              </div>
            ))}
          </div>
        ) : projects.length === 0 ? (
          <div className="bg-white rounded-3xl border border-dashed border-gray-200 p-12 text-center text-gray-500">
            <div className="w-16 h-16 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto mb-4">
              <Folder className="w-8 h-8" />
            </div>
            <h4 className="text-lg font-bold text-gray-900 mb-2">No projects found</h4>
            <p className="text-sm max-w-md mx-auto mb-6">
              You haven't created any videos yet. Click below to start generating your first AI video!
            </p>
            <Link 
              to="/create" 
              className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl shadow-md transition-all">
              <Plus className="w-5 h-5" /> Create Video
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.slice(0, 6).map((project: any) => {
              const statusInfo = getStatusBadge(project.status);
              const hasVideo = Boolean(project.output_path);

              return (
                <div 
                  key={project.id} 
                  onClick={() => navigate(`/projects/${project.id}`)}
                  className="bg-white rounded-3xl border border-gray-200/80 overflow-hidden shadow-2xs hover:shadow-xl hover:border-blue-200 transition-all duration-300 group cursor-pointer flex flex-col">
                  {/* Card Thumbnail / Preview */}
                  <div className="relative h-44 bg-gray-950 overflow-hidden flex items-center justify-center">
                    {hasVideo ? (
                      <video 
                        src={getVideoUrl(project.output_path)} 
                        preload="metadata"
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500 opacity-90"
                      />
                    ) : (
                      <div className="w-full h-full flex flex-col items-center justify-center bg-gradient-to-br from-gray-900 to-gray-800 text-gray-500 group-hover:text-blue-400 transition-colors">
                        <Video className="w-12 h-12 mb-1 group-hover:scale-110 transition-transform" />
                        <span className="text-[11px] font-medium text-gray-400">
                          {project.aspect_ratio || '9:16'} • {project.duration || 60}s
                        </span>
                      </div>
                    )}

                    <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent pointer-events-none"></div>

                    {/* Status Badge */}
                    <div className="absolute top-3 left-3">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold border backdrop-blur-md bg-white/90 shadow-2xs ${statusInfo.badge}`}>
                        <span className={`w-2 h-2 rounded-full ${statusInfo.dot}`}></span>
                        {statusInfo.label}
                      </span>
                    </div>

                    {/* Platform Tag */}
                    <div className="absolute top-3 right-3">
                      <span className="px-2.5 py-1 rounded-lg text-[10px] font-extrabold uppercase tracking-wider bg-black/60 text-white backdrop-blur-md">
                        {project.platform || 'Shorts'}
                      </span>
                    </div>

                    {/* Title overlay */}
                    <div className="absolute bottom-3 left-3 right-3 pointer-events-none">
                      <h4 className="font-extrabold text-white text-base truncate">
                        {project.topic || 'Untitled Project'}
                      </h4>
                      <p className="text-gray-300 text-xs truncate">
                        {project.strategy?.title || project.title || project.topic}
                      </p>
                    </div>
                  </div>

                  {/* Card Body */}
                  <div className="p-5 flex-1 flex flex-col justify-between space-y-4">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-xs text-gray-500">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5 text-gray-400" />
                          {project.duration || 60} seconds
                        </span>
                        <span className="font-medium text-gray-400">
                          {project.audience || 'General'}
                        </span>
                      </div>

                      {project.social_post && (
                        <div className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-blue-50/80 border border-blue-100 rounded-lg text-xs font-semibold text-blue-700">
                          <Share2 className="w-3 h-3 text-blue-600" />
                          <span>Captions & Hashtags ready</span>
                        </div>
                      )}
                    </div>

                    {/* Bottom Action Footer */}
                    <div className="pt-3 border-t border-gray-100 flex items-center justify-between">
                      <span className="text-xs font-bold text-blue-600 group-hover:text-blue-700 flex items-center gap-1">
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
