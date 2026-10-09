import React, { useEffect, useState } from 'react';
import { 
  Folder, Search, Filter, MoreVertical, Video, Clock, 
  CheckCircle2, Sparkles, Share2, Plus, ChevronRight 
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

export default function Projects() {
  const [projects, setProjects] = useState<any[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('All');
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    axios.get(`${API_URL}/projects/`)
      .then(res => setProjects(res.data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const getVideoUrl = (path: string) => {
    if (!path) return '';
    const normalized = path.replace(/\\/g, '/');
    const storageIndex = normalized.indexOf('storage/');
    if (storageIndex !== -1) {
      return `http://localhost:8000/${normalized.substring(storageIndex)}`;
    }
    return `http://localhost:8000/${normalized}`;
  };

  const filteredProjects = projects.filter(project => {
    const matchesSearch = 
      (project.topic || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (project.title || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (project.platform || '').toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = filterStatus === 'All' || project.status === filterStatus;
    return matchesSearch && matchesStatus;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'Completed':
        return { badge: 'bg-emerald-50 text-emerald-700 border-emerald-200', dot: 'bg-emerald-500', label: 'Completed' };
      case 'Ready':
        return { badge: 'bg-blue-50 text-blue-700 border-blue-200', dot: 'bg-blue-500', label: 'Script Ready' };
      case 'Rendering':
        return { badge: 'bg-amber-50 text-amber-700 border-amber-200 animate-pulse', dot: 'bg-amber-500', label: 'Rendering...' };
      case 'Planning':
        return { badge: 'bg-purple-50 text-purple-700 border-purple-200', dot: 'bg-purple-500', label: 'Planning' };
      case 'Failed':
        return { badge: 'bg-rose-50 text-rose-700 border-rose-200', dot: 'bg-rose-500', label: 'Failed' };
      default:
        return { badge: 'bg-gray-50 text-gray-700 border-gray-200', dot: 'bg-gray-400', label: status };
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto h-full flex flex-col space-y-8 animate-fadeIn">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-extrabold text-gray-900 tracking-tight">Projects</h2>
          <p className="text-gray-500 text-sm mt-0.5">Manage, review, and download your AI-generated videos ({projects.length} total).</p>
        </div>
        
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 sm:w-64">
            <Search className="w-4 h-4 absolute left-3.5 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <input 
              type="text" 
              placeholder="Search by topic..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 bg-white border border-gray-200 rounded-xl text-xs sm:text-sm focus:ring-2 focus:ring-blue-500 outline-none shadow-2xs" 
            />
          </div>

          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-3.5 py-2.5 bg-white border border-gray-200 rounded-xl text-xs sm:text-sm font-semibold text-gray-700 outline-none focus:ring-2 focus:ring-blue-500 shadow-2xs cursor-pointer">
            <option value="All">All Statuses</option>
            <option value="Completed">Completed</option>
            <option value="Ready">Script Ready</option>
            <option value="Planning">Planning</option>
            <option value="Failed">Failed</option>
          </select>

          <Link
            to="/create"
            className="inline-flex items-center gap-1.5 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl text-xs sm:text-sm shadow-sm transition-all shrink-0">
            <Plus className="w-4 h-4" /> New Video
          </Link>
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((n) => (
            <div key={n} className="bg-white rounded-3xl border border-gray-100 p-6 space-y-4 animate-pulse">
              <div className="h-44 bg-gray-100 rounded-2xl"></div>
              <div className="h-4 bg-gray-100 rounded w-3/4"></div>
              <div className="h-3 bg-gray-100 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      ) : filteredProjects.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center text-center text-gray-500 mt-6 bg-white rounded-3xl border border-dashed border-gray-300 p-12 shadow-sm">
          <Folder className="w-16 h-16 text-gray-300 mb-4" />
          <h3 className="text-xl font-bold text-gray-900 mb-2">
            {searchTerm || filterStatus !== 'All' ? 'No matching projects found' : 'No projects found'}
          </h3>
          <p className="mb-6 max-w-md text-sm">
            {searchTerm || filterStatus !== 'All' 
              ? 'Try adjusting your search terms or filter selection.'
              : "You haven't created any videos yet. Head over to the Create Video page to get started!"}
          </p>
          <Link
            to="/create"
            className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl shadow-md transition-all">
            <Plus className="w-5 h-5" /> Create Video
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredProjects.map((project: any) => {
            const statusInfo = getStatusBadge(project.status);
            const hasVideo = Boolean(project.output_path);

            return (
              <div 
                key={project.id} 
                onClick={() => navigate(`/projects/${project.id}`)}
                className="bg-white rounded-3xl border border-gray-200/80 overflow-hidden shadow-2xs hover:shadow-xl hover:border-blue-200 transition-all duration-300 group cursor-pointer flex flex-col">
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

                  <div className="absolute top-3 left-3">
                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold border backdrop-blur-md bg-white/90 shadow-2xs ${statusInfo.badge}`}>
                      <span className={`w-2 h-2 rounded-full ${statusInfo.dot}`}></span>
                      {statusInfo.label}
                    </span>
                  </div>

                  <div className="absolute top-3 right-3">
                    <span className="px-2.5 py-1 rounded-lg text-[10px] font-extrabold uppercase tracking-wider bg-black/60 text-white backdrop-blur-md">
                      {project.platform || 'Shorts'}
                    </span>
                  </div>

                  <div className="absolute bottom-3 left-3 right-3 pointer-events-none">
                    <h4 className="font-extrabold text-white text-base truncate">
                      {project.topic || 'Untitled Project'}
                    </h4>
                    <p className="text-gray-300 text-xs truncate">
                      {project.strategy?.title || project.title || project.topic}
                    </p>
                  </div>
                </div>

                <div className="p-5 flex-1 flex flex-col justify-between space-y-4">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5 text-gray-400" />
                        {project.duration || 60} seconds
                      </span>
                      <span className="font-semibold text-purple-700 bg-purple-50 px-2 py-0.5 rounded-md border border-purple-100 text-[11px]">
                        🌐 {project.language || 'English'}
                      </span>
                    </div>

                    {project.social_post && (
                      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-blue-50/80 border border-blue-100 rounded-lg text-xs font-semibold text-blue-700">
                        <Share2 className="w-3 h-3 text-blue-600" />
                        <span>Captions & Hashtags ready</span>
                      </div>
                    )}
                  </div>

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
  );
}
