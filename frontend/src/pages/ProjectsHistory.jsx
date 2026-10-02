import React, { useState } from 'react';
import { 
  FolderGit2, 
  Film, 
  Calendar, 
  Clock, 
  Download, 
  Share2, 
  Play, 
  CheckCircle2, 
  AlertCircle,
  ExternalLink,
  Search,
  Sparkles
} from 'lucide-react';

export default function ProjectsHistory({ 
  projects = [], 
  onSelectProject, 
  onPublishProject 
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [previewVideo, setPreviewVideo] = useState(null);

  const filtered = projects.filter(p => 
    (p.title || p.topic || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6 pb-16">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-5">
        <div>
          <div className="flex items-center space-x-2">
            <FolderGit2 className="w-5 h-5 text-primary" />
            <h2 className="text-xl font-bold text-text-primary tracking-tight">
              PROJECT HISTORY
            </h2>
          </div>
          <p className="text-xs text-text-secondary mt-1">
            Archived video assets, scripts, and publish-ready social videos
          </p>
        </div>

        {/* Search Input */}
        <div className="relative w-full sm:w-64">
          <Search className="w-4 h-4 text-text-secondary absolute left-3 top-3" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search projects..."
            className="w-full pl-9 pr-3.5 py-2 rounded-xl bg-surface border border-border text-xs text-text-primary placeholder-text-secondary/60 focus:border-primary focus:ring-1 focus:ring-primary focus:outline-none transition-all shadow-sm"
          />
        </div>
      </div>

      {/* Projects Grid */}
      {filtered.length === 0 ? (
        <div className="bg-surface rounded-3xl p-12 text-center border border-border space-y-3 shadow-sm">
          <Film className="w-12 h-12 text-text-secondary mx-auto" />
          <h3 className="text-base font-bold text-text-primary">No Projects Found</h3>
          <p className="text-xs text-text-secondary max-w-sm mx-auto">
            {searchTerm 
              ? 'No projects match your search query.' 
              : 'You have not generated any videos yet. Go to the dashboard to create your first video.'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filtered.map((proj) => {
            const hasVideo = !!proj.video_url || !!proj.video_path;
            const isPublished = proj.status === 'published';

            return (
              <div 
                key={proj.id}
                className="bg-surface rounded-2xl p-4 border border-border flex flex-col justify-between hover:border-text-secondary/30 transition-all shadow-sm group"
              >
                <div className="space-y-3">
                  {/* Card Header: Platform & Status */}
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20">
                      {proj.platform || 'Global Feed'}
                    </span>

                    <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full ${
                      isPublished 
                        ? 'bg-success/10 text-success border border-success/30'
                        : proj.status === 'ready'
                          ? 'bg-secondary/10 text-secondary border border-secondary/30'
                          : 'bg-surface-secondary text-text-secondary'
                    }`}>
                      {isPublished ? 'PUBLISHED ✓' : proj.status.toUpperCase()}
                    </span>
                  </div>

                  {/* Thumbnail / Video Preview Box */}
                  <div 
                    onClick={() => hasVideo && setPreviewVideo(proj)}
                    className="relative aspect-video rounded-xl bg-surface-secondary border border-border flex items-center justify-center overflow-hidden cursor-pointer group-hover:border-primary/50 transition-all"
                  >
                    {hasVideo ? (
                      <>
                        <video
                          src={proj.video_url || `/api/projects/${proj.id}/video`}
                          className="w-full h-full object-cover"
                          preload="metadata"
                        />
                        <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                          <div className="w-10 h-10 rounded-full bg-primary/90 text-white flex items-center justify-center shadow-md">
                            <Play className="w-4 h-4 ml-0.5 fill-current" />
                          </div>
                        </div>
                      </>
                    ) : (
                      <div className="text-text-secondary text-center p-3">
                        <Film className="w-8 h-8 mx-auto mb-1 opacity-40" />
                        <span className="text-[10px]">Processing</span>
                      </div>
                    )}
                  </div>

                  {/* Project Title & Topic */}
                  <div>
                    <h3 className="text-sm font-bold text-text-primary line-clamp-1 group-hover:text-primary transition-colors">
                      {proj.title || proj.topic}
                    </h3>
                    <p className="text-xs text-text-secondary line-clamp-2 mt-0.5">
                      {proj.hook || proj.topic}
                    </p>
                  </div>

                  {/* Metadata Chips */}
                  <div className="flex items-center space-x-3 text-[11px] text-text-secondary pt-1">
                    <span className="flex items-center space-x-1">
                      <Clock className="w-3 h-3" />
                      <span>{proj.duration || 30}s</span>
                    </span>
                    <span>•</span>
                    <span className="flex items-center space-x-1">
                      <Calendar className="w-3 h-3" />
                      <span>{new Date(proj.created_at).toLocaleDateString()}</span>
                    </span>
                  </div>
                </div>

                {/* Card Actions */}
                <div className="grid grid-cols-2 gap-2 pt-4 mt-3 border-t border-border">
                  <button
                    onClick={() => onSelectProject(proj)}
                    className="py-1.5 px-3 rounded-xl bg-surface-secondary hover:bg-border text-text-primary text-xs font-semibold flex items-center justify-center space-x-1 transition-colors"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                    <span>View Studio</span>
                  </button>

                  {hasVideo ? (
                    <a
                      href={proj.video_url || `/api/projects/${proj.id}/video`}
                      download={`qoneqt_${proj.id.slice(0, 8)}.mp4`}
                      className="py-1.5 px-3 rounded-xl bg-surface-secondary hover:bg-border text-text-primary text-xs font-semibold flex items-center justify-center space-x-1 transition-colors"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>Download</span>
                    </a>
                  ) : (
                    <span className="py-1.5 px-3 rounded-xl bg-surface-secondary text-text-secondary text-xs text-center border border-border border-dashed">
                      Rendering
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Video Modal Preview */}
      {previewVideo && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-text-primary/30 backdrop-blur-sm">
          <div className="relative max-w-sm w-full bg-surface rounded-3xl p-5 border border-border shadow-xl space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-border">
              <h4 className="text-xs font-bold text-text-primary truncate max-w-[240px]">
                {previewVideo.title || previewVideo.topic}
              </h4>
              <button
                onClick={() => setPreviewVideo(null)}
                className="text-text-secondary hover:text-text-primary text-xs font-bold px-2 py-1 rounded bg-surface-secondary transition-colors"
              >
                Close
              </button>
            </div>

            <div className="aspect-[9/16] bg-surface-secondary rounded-2xl overflow-hidden border border-border">
              <video
                src={previewVideo.video_url || `/api/projects/${previewVideo.id}/video`}
                controls
                autoPlay
                playsInline
                className="w-full h-full object-cover"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
