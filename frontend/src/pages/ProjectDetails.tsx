import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  Wand2, Loader2, CheckCircle2, ChevronRight, Play, Film, Type, Music, 
  Edit2, Save, X, Download, Copy, Check, Share2, Hash, Sparkles, RefreshCw, 
  MessageSquare, Lightbulb, ExternalLink, CheckCheck
} from 'lucide-react';

const API_URL = 'http://localhost:8000/api';

export default function ProjectDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState('');
  
  const [isEditingStrategy, setIsEditingStrategy] = useState(false);
  const [editedStrategy, setEditedStrategy] = useState<any>(null);

  const [isEditingScript, setIsEditingScript] = useState(false);
  const [editedScript, setEditedScript] = useState<any>(null);

  // Social Post & Hashtags State
  const [isEditingSocial, setIsEditingSocial] = useState(false);
  const [editedSocial, setEditedSocial] = useState<any>(null);
  const [isGeneratingSocial, setIsGeneratingSocial] = useState(false);
  const [activePlatformTab, setActivePlatformTab] = useState<'recommended' | 'short' | 'instagram' | 'tiktok' | 'youtube' | 'linkedin'>('recommended');
  const [copiedItem, setCopiedItem] = useState<string | null>(null);

  const fetchProject = async () => {
    try {
      const res = await axios.get(`${API_URL}/projects/${id}`);
      setProject(res.data);
      if (res.data.strategy) {
        setEditedStrategy(res.data.strategy);
      }
      if (res.data.script) {
        setEditedScript(res.data.script);
      }
      if (res.data.social_post) {
        setEditedSocial(res.data.social_post);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProject();
  }, [id]);

  const handleGenerateScript = async () => {
    setActionLoading(true);
    try {
      const res = await axios.post(`${API_URL}/projects/${id}/generate-script`);
      setProject(res.data);
      setEditedScript(res.data.script);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleSaveStrategy = async () => {
    setActionLoading(true);
    try {
      const res = await axios.put(`${API_URL}/projects/${id}/strategy`, editedStrategy);
      setProject(res.data);
      setIsEditingStrategy(false);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleSaveScript = async () => {
    setActionLoading(true);
    try {
      const res = await axios.put(`${API_URL}/projects/${id}/script`, editedScript);
      setProject(res.data);
      setIsEditingScript(false);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleRegenerateSocialPost = async () => {
    setIsGeneratingSocial(true);
    try {
      const res = await axios.post(`${API_URL}/projects/${id}/generate-social-post`);
      setProject(res.data);
      setEditedSocial(res.data.social_post);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsGeneratingSocial(false);
    }
  };

  const handleSaveSocialPost = async () => {
    setActionLoading(true);
    try {
      const res = await axios.put(`${API_URL}/projects/${id}/social-post`, editedSocial);
      setProject(res.data);
      setIsEditingSocial(false);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setActionLoading(false);
    }
  };

  const copyToClipboard = async (text: string, type: string) => {
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      setCopiedItem(type);
      setTimeout(() => {
        setCopiedItem((prev) => (prev === type ? null : prev));
      }, 2500);
    } catch (e) {
      console.error('Failed to copy', e);
    }
  };

  const getActiveCaptionText = () => {
    const post = isEditingSocial ? editedSocial : (project?.social_post || {});
    if (!post) return '';

    if (activePlatformTab === 'short') {
      return post.short_caption || post.caption || '';
    }
    if (activePlatformTab === 'instagram') {
      return post.platform_variations?.instagram_reels || post.caption || '';
    }
    if (activePlatformTab === 'tiktok') {
      return post.platform_variations?.tiktok || post.caption || '';
    }
    if (activePlatformTab === 'youtube') {
      return post.platform_variations?.youtube_shorts || post.caption || '';
    }
    if (activePlatformTab === 'linkedin') {
      return post.platform_variations?.linkedin || post.caption || '';
    }
    return post.caption || '';
  };

  const getActiveHashtagsString = () => {
    const post = isEditingSocial ? editedSocial : (project?.social_post || {});
    if (!post) return '';
    if (post.hashtags_string) return post.hashtags_string;
    if (Array.isArray(post.hashtags)) return post.hashtags.join(' ');
    return '';
  };

  const getActiveHashtagsList = (): string[] => {
    const post = isEditingSocial ? editedSocial : (project?.social_post || {});
    if (!post) return [];
    if (Array.isArray(post.hashtags) && post.hashtags.length > 0) {
      return post.hashtags;
    }
    if (post.hashtags_string) {
      return post.hashtags_string.split(/\s+/).filter((t: string) => t.startsWith('#'));
    }
    return [];
  };

  const handleCopyCompletePost = () => {
    const caption = getActiveCaptionText();
    const hashtags = getActiveHashtagsString();
    const fullPost = `${caption}\n\n${hashtags}`.trim();
    copyToClipboard(fullPost, 'complete_post');
  };

  const getVideoUrl = (path: string) => {
    if (!path) return '';
    const normalized = path.replace(/\\/g, '/');
    const storageIndex = normalized.indexOf('storage/');
    if (storageIndex !== -1) {
      return `http://localhost:8000/${normalized.substring(storageIndex)}`;
    }
    return `http://localhost:8000/${normalized}`;
  };

  if (loading) return <div className="p-8 flex items-center justify-center h-full"><Loader2 className="w-8 h-8 animate-spin text-blue-600" /></div>;
  if (error) return <div className="p-8 text-red-600">Error: {error}</div>;
  if (!project) return <div className="p-8">Project not found</div>;

  return (
    <div className="p-8 max-w-6xl mx-auto pb-24">
      <div className="flex items-center text-sm font-medium text-gray-500 mb-6">
        <span className="cursor-pointer hover:text-blue-600" onClick={() => navigate('/projects')}>Projects</span>
        <ChevronRight className="w-4 h-4 mx-2" />
        <span className="text-gray-900">{project.title || 'Untitled Project'}</span>
      </div>

      <div className="mb-8">
        <h2 className="text-3xl font-extrabold text-gray-900 mb-2">{project.topic}</h2>
        <div className="flex flex-wrap items-center gap-3">
          <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-bold uppercase tracking-wider">{project.status}</span>
          <span className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-xs font-bold uppercase tracking-wider">{project.platform}</span>
          
        </div>
      </div>

      {project.status === 'Planning' && project.strategy && (
        <div className="bg-white rounded-2xl border border-gray-200 p-8 shadow-sm mb-8">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xl font-bold flex items-center gap-2 text-gray-900">
              <CheckCircle2 className="w-6 h-6 text-green-500" /> 
              AI Strategy Generated
            </h3>
            {!isEditingStrategy ? (
              <button 
                onClick={() => setIsEditingStrategy(true)}
                className="flex items-center gap-2 text-sm font-semibold text-gray-600 hover:text-blue-600 transition-colors">
                <Edit2 className="w-4 h-4" /> Edit Strategy
              </button>
            ) : (
              <div className="flex gap-3">
                <button 
                  onClick={() => {
                    setIsEditingStrategy(false);
                    setEditedStrategy(project.strategy); // Reset
                  }}
                  className="flex items-center gap-2 px-3 py-1.5 text-sm font-semibold text-gray-500 hover:text-gray-700 transition-colors">
                  <X className="w-4 h-4" /> Cancel
                </button>
                <button 
                  onClick={handleSaveStrategy}
                  disabled={actionLoading}
                  className="flex items-center gap-2 px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg shadow-sm transition-all disabled:opacity-50">
                  {actionLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />} Save
                </button>
              </div>
            )}
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
            <div className="space-y-4">
              <div>
                <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Suggested Title</span>
                {isEditingStrategy ? (
                  <input 
                    type="text" 
                    value={editedStrategy.title} 
                    onChange={e => setEditedStrategy({...editedStrategy, title: e.target.value})}
                    className="w-full mt-1 p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" 
                  />
                ) : (
                  <p className="font-medium text-gray-900">{project.strategy.title}</p>
                )}
              </div>
              <div>
                <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Hook</span>
                {isEditingStrategy ? (
                  <textarea 
                    rows={2}
                    value={editedStrategy.hook} 
                    onChange={e => setEditedStrategy({...editedStrategy, hook: e.target.value})}
                    className="w-full mt-1 p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" 
                  />
                ) : (
                  <p className="font-medium text-gray-900">{project.strategy.hook}</p>
                )}
              </div>
            </div>
            <div className="space-y-4">
              <div className="flex gap-4">
                <div className="flex-1">
                  <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Style</span>
                  {isEditingStrategy ? (
                    <input 
                      type="text" 
                      value={editedStrategy.style} 
                      onChange={e => setEditedStrategy({...editedStrategy, style: e.target.value})}
                      className="w-full mt-1 p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" 
                    />
                  ) : (
                    <p className="font-medium text-gray-900">{project.strategy.style}</p>
                  )}
                </div>
                <div className="flex-1">
                  <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Duration (s)</span>
                  {isEditingStrategy ? (
                    <input 
                      type="number" 
                      value={editedStrategy.recommended_duration} 
                      onChange={e => setEditedStrategy({...editedStrategy, recommended_duration: parseInt(e.target.value)})}
                      className="w-full mt-1 p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" 
                    />
                  ) : (
                    <p className="font-medium text-gray-900">{project.strategy.recommended_duration}s</p>
                  )}
                </div>
              </div>
              <div>
                <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Call to Action</span>
                {isEditingStrategy ? (
                  <input 
                    type="text" 
                    value={editedStrategy.cta} 
                    onChange={e => setEditedStrategy({...editedStrategy, cta: e.target.value})}
                    className="w-full mt-1 p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" 
                  />
                ) : (
                  <p className="font-medium text-gray-900">{project.strategy.cta}</p>
                )}
              </div>
            </div>
          </div>

          <div className="flex justify-end border-t border-gray-100 pt-6">
            <button 
              onClick={handleGenerateScript}
              disabled={actionLoading || isEditingStrategy}
              className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white font-bold rounded-xl shadow-md transition-all transform hover:scale-105 disabled:opacity-50 disabled:hover:scale-100 disabled:cursor-not-allowed">
              {actionLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Wand2 className="w-5 h-5" />}
              Generate Script & Storyboard
            </button>
          </div>
        </div>
      )}

      {project.status === 'Ready' && project.script && (
        <div className="space-y-8">
          <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden shadow-sm">
             <div className="bg-gray-50 px-6 py-4 border-b border-gray-200 flex justify-between items-center">
                <h3 className="text-lg font-bold text-gray-900">Script Review</h3>
                {!isEditingScript ? (
                  <button 
                    onClick={() => setIsEditingScript(true)}
                    className="flex items-center gap-2 text-sm font-semibold text-gray-600 hover:text-blue-600 transition-colors">
                    <Edit2 className="w-4 h-4" /> Edit Script
                  </button>
                ) : (
                  <div className="flex gap-3">
                    <button 
                      onClick={() => {
                        setIsEditingScript(false);
                        setEditedScript(project.script); // Reset
                      }}
                      className="flex items-center gap-2 px-3 py-1.5 text-sm font-semibold text-gray-500 hover:text-gray-700 transition-colors">
                      <X className="w-4 h-4" /> Cancel
                    </button>
                    <button 
                      onClick={handleSaveScript}
                      disabled={actionLoading}
                      className="flex items-center gap-2 px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg shadow-sm transition-all disabled:opacity-50">
                      {actionLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />} Save
                    </button>
                  </div>
                )}
             </div>
             <div className="p-6">
                <div className="mb-4">
                  <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Hook</span>
                  {isEditingScript ? (
                    <textarea 
                      rows={2}
                      value={editedScript.hook}
                      onChange={e => setEditedScript({...editedScript, hook: e.target.value})}
                      className="w-full mt-2 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-lg font-medium italic"
                    />
                  ) : (
                    <p className="text-lg font-medium text-gray-900 mb-4 italic">"{project.script.hook}"</p>
                  )}
                </div>
                <div className="mb-4">
                  <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Body / Scenes</span>
                  <div className="space-y-4 mt-4">
                    {(isEditingScript ? editedScript.scenes : project.script.scenes)?.map((scene: any, idx: number) => (
                      <div key={idx} className="flex gap-4 items-start bg-gray-50 p-4 rounded-xl">
                        <div className="w-8 h-8 shrink-0 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold">{idx + 1}</div>
                        <div className="flex-1 space-y-3">
                          {isEditingScript ? (
                            <>
                              <div>
                                <label className="text-xs font-bold text-gray-500">Narration</label>
                                <textarea 
                                  value={scene.narration}
                                  onChange={e => {
                                    const newScenes = [...editedScript.scenes];
                                    newScenes[idx].narration = e.target.value;
                                    setEditedScript({...editedScript, scenes: newScenes});
                                  }}
                                  className="w-full mt-1 p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none font-medium"
                                  rows={2}
                                />
                              </div>
                              <div>
                                <label className="text-xs font-bold text-gray-500 flex items-center gap-1"><Film className="w-3 h-3"/> Visual Prompt</label>
                                <input 
                                  type="text"
                                  value={scene.visual_description}
                                  onChange={e => {
                                    const newScenes = [...editedScript.scenes];
                                    newScenes[idx].visual_description = e.target.value;
                                    setEditedScript({...editedScript, scenes: newScenes});
                                  }}
                                  className="w-full mt-1 p-2 border border-gray-300 rounded-lg text-sm text-gray-700 outline-none focus:ring-1 focus:ring-blue-500"
                                />
                              </div>
                              <div>
                                <label className="text-xs font-bold text-gray-500 flex items-center gap-1"><Type className="w-3 h-3"/> On-screen Text</label>
                                <input 
                                  type="text"
                                  value={scene.on_screen_text}
                                  onChange={e => {
                                    const newScenes = [...editedScript.scenes];
                                    newScenes[idx].on_screen_text = e.target.value;
                                    setEditedScript({...editedScript, scenes: newScenes});
                                  }}
                                  className="w-full mt-1 p-2 border border-gray-300 rounded-lg text-sm text-gray-700 outline-none focus:ring-1 focus:ring-blue-500"
                                />
                              </div>
                            </>
                          ) : (
                            <>
                              <p className="text-gray-900 font-medium">"{scene.narration}"</p>
                              <p className="text-sm text-gray-500 mt-2 flex items-center gap-2"><Film className="w-4 h-4"/> {scene.visual_description}</p>
                              <p className="text-sm text-gray-500 mt-1 flex items-center gap-2"><Type className="w-4 h-4"/> Text: {scene.on_screen_text}</p>
                            </>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
             </div>
          </div>
          
          <div className="flex justify-end">
             <button 
                onClick={async () => {
                  setActionLoading(true);
                  try {
                    await axios.post(`${API_URL}/projects/${id}/render`);
                    fetchProject(); // refresh to see status
                  } catch (err: any) {
                    setError(err.message);
                  } finally {
                    setActionLoading(false);
                  }
                }}
                disabled={actionLoading || isEditingScript}
                className="flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-bold rounded-xl shadow-xl shadow-blue-200 transition-all transform hover:scale-105 disabled:opacity-50">
                {actionLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Play className="w-5 h-5 fill-current" />}
                Render Final Video
             </button>
          </div>
        </div>
      )}

      {project.status === 'Rendering' && (
        <div className="bg-white rounded-2xl border border-gray-200 p-12 shadow-sm text-center">
          <Loader2 className="w-16 h-16 animate-spin text-blue-600 mx-auto mb-6" />
          <h3 className="text-2xl font-bold text-gray-900 mb-2">Rendering your video...</h3>
          <p className="text-gray-500 max-w-md mx-auto">The AI Director is generating visuals, synthesizing voiceovers, adding captions, and compiling the final video. This may take a few minutes.</p>
        </div>
      )}

      {project.status === 'Completed' && (
        <div className="space-y-8 animate-fadeIn">
          {/* Top Banner: Video Ready & Download */}
          <div className="bg-gradient-to-r from-emerald-600 via-teal-600 to-blue-600 rounded-3xl p-6 sm:p-8 text-white shadow-xl shadow-teal-500/10 flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-2xl bg-white/20 backdrop-blur-md flex items-center justify-center shrink-0 border border-white/30">
                <CheckCircle2 className="w-8 h-8 text-white" />
              </div>
              <div>
                <span className="inline-block px-3 py-1 bg-white/25 rounded-full text-xs font-bold uppercase tracking-wider mb-1">
                  Ready to Download & Post
                </span>
                <h3 className="text-2xl sm:text-3xl font-extrabold tracking-tight">Your Video is Ready!</h3>
                <p className="text-emerald-100 text-sm mt-1">
                  Rendered in {project.aspect_ratio || '9:16'} for {project.platform || 'Social Media'}. Use the generated captions and hashtags below when posting.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3 w-full md:w-auto">
              <a 
                href={`${API_URL}/projects/${project.id}/download`} 
                download
                className="flex-1 md:flex-initial flex items-center justify-center gap-3 px-7 py-3.5 bg-white text-emerald-800 hover:bg-emerald-50 font-bold rounded-2xl shadow-lg hover:shadow-xl transition-all transform hover:-translate-y-0.5">
                <Download className="w-5 h-5 text-emerald-600" />
                Download Video (.MP4)
              </a>
            </div>
          </div>

          {/* Grid Layout: Video Player (Left) + Social Media Kit (Right) */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            {/* Left Column: Video Preview & Specs */}
            <div className="lg:col-span-5 space-y-6">
              <div className="bg-white rounded-3xl border border-gray-200/80 p-5 shadow-sm overflow-hidden">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="font-bold text-gray-900 flex items-center gap-2 text-sm">
                    <Film className="w-4 h-4 text-blue-600" /> Video Preview
                  </h4>
                  <span className="text-xs font-semibold px-2.5 py-1 bg-gray-100 text-gray-700 rounded-lg">
                    {project.aspect_ratio || '9:16'}
                  </span>
                </div>

                {project.output_path ? (
                  <div className={`relative bg-neutral-950 rounded-2xl overflow-hidden shadow-inner flex items-center justify-center ${project.aspect_ratio === '16:9' ? 'aspect-video' : 'aspect-[9/16] max-h-[500px] mx-auto'}`}>
                    <video 
                      src={getVideoUrl(project.output_path)} 
                      controls 
                      playsInline
                      className="w-full h-full object-contain"
                    />
                  </div>
                ) : (
                  <div className="aspect-video bg-gray-100 rounded-2xl flex items-center justify-center text-gray-400">
                    Video file not ready
                  </div>
                )}

                <div className="mt-5 pt-4 border-t border-gray-100 space-y-2.5 text-xs text-gray-600">
                  <div className="flex justify-between">
                    <span className="text-gray-400 font-medium">Platform</span>
                    <span className="font-semibold text-gray-800">{project.platform}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400 font-medium">Topic</span>
                    <span className="font-semibold text-gray-800 truncate max-w-[200px]">{project.topic}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400 font-medium">Audience</span>
                    <span className="font-semibold text-gray-800">{project.audience || 'General'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400 font-medium">Language</span>
                    <span className="font-semibold text-purple-700">{project.language || 'English'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400 font-medium">Target Duration</span>
                    <span className="font-semibold text-gray-800">{project.duration || 60}s</span>
                  </div>
                </div>

                <div className="mt-5">
                  <a 
                    href={`${API_URL}/projects/${project.id}/download`} 
                    download
                    className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl shadow-md shadow-emerald-600/20 transition-all text-sm">
                    <Download className="w-4 h-4" /> Download MP4 File
                  </a>
                </div>
              </div>

              {/* Creator Tip Card */}
              <div className="bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-200/80 rounded-2xl p-4.5 shadow-sm">
                <div className="flex items-start gap-3">
                  <Lightbulb className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                  <div className="text-xs text-amber-900 leading-relaxed">
                    <strong className="block font-bold text-amber-950 mb-1">Posting Best Practice:</strong>
                    Copy the complete post below or customize the platform variation. Include 5-10 hashtags in your caption to help the {project.platform} algorithm categorize and distribute your video to the right audience.
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column: Social Media Kit (Captions & Hashtags) */}
            <div className="lg:col-span-7 space-y-6">
              {!project.social_post && !isGeneratingSocial ? (
                <div className="bg-white rounded-3xl border border-gray-200 p-10 text-center shadow-sm">
                  <div className="w-16 h-16 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto mb-4">
                    <Sparkles className="w-8 h-8" />
                  </div>
                  <h4 className="text-xl font-bold text-gray-900 mb-2">Ready to Post?</h4>
                  <p className="text-gray-500 text-sm max-w-md mx-auto mb-6">
                    Generate viral captions and high-ranking hashtags tailored specifically for <strong>"{project.topic}"</strong>.
                  </p>
                  <button
                    onClick={handleRegenerateSocialPost}
                    disabled={isGeneratingSocial}
                    className="inline-flex items-center gap-2 px-6 py-3.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-bold rounded-xl shadow-lg shadow-blue-500/20 transition-all transform hover:scale-105">
                    <Sparkles className="w-5 h-5" /> Generate Captions & Hashtags
                  </button>
                </div>
              ) : isGeneratingSocial ? (
                <div className="bg-white rounded-3xl border border-gray-200 p-12 text-center shadow-sm">
                  <Loader2 className="w-12 h-12 animate-spin text-blue-600 mx-auto mb-4" />
                  <h4 className="text-lg font-bold text-gray-900 mb-1">Crafting Captions & Hashtags...</h4>
                  <p className="text-gray-500 text-sm">
                    Analyzing "{project.topic}" to generate viral hooks, platform copy, and targeted tags.
                  </p>
                </div>
              ) : (
                <div className="bg-white rounded-3xl border border-gray-200/80 shadow-sm overflow-hidden">
                  {/* Card Header */}
                  <div className="p-6 border-b border-gray-100 bg-gray-50/50 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider bg-blue-100 text-blue-700">
                          AI Social Kit
                        </span>
                        <span className="text-xs font-semibold text-gray-400">• For {project.platform}</span>
                      </div>
                      <h3 className="text-xl font-extrabold text-gray-900 flex items-center gap-2">
                        <Share2 className="w-5 h-5 text-blue-600" />
                        Captions & Hashtags
                      </h3>
                      <p className="text-xs text-gray-500 mt-0.5">
                        Copy and paste directly when posting your video to social media
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={handleRegenerateSocialPost}
                        disabled={isGeneratingSocial || actionLoading}
                        title="Regenerate fresh copy"
                        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-gray-600 hover:text-blue-600 hover:bg-white rounded-lg border border-gray-200 transition-all disabled:opacity-50">
                        <RefreshCw className={`w-3.5 h-3.5 ${isGeneratingSocial ? 'animate-spin' : ''}`} />
                        <span>Regenerate</span>
                      </button>

                      {!isEditingSocial ? (
                        <button
                          onClick={() => {
                            setEditedSocial(project.social_post || {});
                            setIsEditingSocial(true);
                          }}
                          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-gray-600 hover:text-blue-600 hover:bg-white rounded-lg border border-gray-200 transition-all">
                          <Edit2 className="w-3.5 h-3.5" />
                          <span>Edit</span>
                        </button>
                      ) : (
                        <div className="flex items-center gap-1.5">
                          <button
                            onClick={() => {
                              setIsEditingSocial(false);
                              setEditedSocial(project.social_post);
                            }}
                            className="px-2.5 py-1.5 text-xs font-semibold text-gray-500 hover:text-gray-700 rounded-lg">
                            Cancel
                          </button>
                          <button
                            onClick={handleSaveSocialPost}
                            disabled={actionLoading}
                            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white rounded-lg shadow-sm disabled:opacity-50">
                            {actionLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                            <span>Save</span>
                          </button>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="p-6 space-y-6">
                    {/* Primary One-Click "Copy Complete Post" Banner */}
                    <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-700 p-4 text-white shadow-md">
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                        <div>
                          <div className="font-bold text-sm flex items-center gap-2">
                            <Sparkles className="w-4 h-4 text-amber-300" />
                            Ready-to-Post Copy
                          </div>
                          <p className="text-xs text-blue-100 mt-0.5">
                            Copies formatted caption + all hashtags with proper line breaks
                          </p>
                        </div>
                        <button
                          onClick={handleCopyCompletePost}
                          className="flex items-center justify-center gap-2 px-5 py-2.5 bg-white text-blue-700 hover:bg-blue-50 font-bold rounded-xl text-xs shadow-sm transition-all transform active:scale-95 shrink-0">
                          {copiedItem === 'complete_post' ? (
                            <>
                              <CheckCheck className="w-4 h-4 text-emerald-600" />
                              <span className="text-emerald-700 font-extrabold">✓ Copied to Clipboard!</span>
                            </>
                          ) : (
                            <>
                              <Copy className="w-4 h-4 text-blue-600" />
                              <span>Copy Complete Post</span>
                            </>
                          )}
                        </button>
                      </div>
                    </div>

                    {/* Platform Selector Tabs */}
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <label className="text-xs font-bold text-gray-400 uppercase tracking-wider">
                          Caption Format Style
                        </label>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {[
                          { id: 'recommended', label: `⭐ ${project.platform || 'Recommended'}` },
                          { id: 'short', label: '⚡ Short & Punchy' },
                          { id: 'instagram', label: '📸 Instagram Reels' },
                          { id: 'tiktok', label: '🎵 TikTok' },
                          { id: 'youtube', label: '▶️ YouTube Shorts' },
                          { id: 'linkedin', label: '💼 LinkedIn' },
                        ].map((tab) => (
                          <button
                            key={tab.id}
                            onClick={() => setActivePlatformTab(tab.id as any)}
                            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                              activePlatformTab === tab.id
                                ? 'bg-blue-600 text-white shadow-sm shadow-blue-500/20'
                                : 'bg-gray-100 text-gray-600 hover:bg-gray-200/80 hover:text-gray-900'
                            }`}>
                            {tab.label}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Caption Section */}
                    <div className="bg-gray-50/70 border border-gray-200/80 rounded-2xl p-4.5 space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Type className="w-4 h-4 text-blue-600" />
                          <span className="text-xs font-bold text-gray-700 uppercase tracking-wider">Post Caption</span>
                          <span className="text-[11px] text-gray-400 font-medium">
                            ({getActiveCaptionText().length} chars)
                          </span>
                        </div>

                        <button
                          onClick={() => copyToClipboard(getActiveCaptionText(), 'caption')}
                          className="flex items-center gap-1.5 px-3 py-1 bg-white hover:bg-gray-100 border border-gray-200 text-xs font-semibold text-gray-700 rounded-lg shadow-2xs transition-all">
                          {copiedItem === 'caption' ? (
                            <>
                              <Check className="w-3.5 h-3.5 text-emerald-600" />
                              <span className="text-emerald-700 font-bold">Copied Caption!</span>
                            </>
                          ) : (
                            <>
                              <Copy className="w-3.5 h-3.5 text-gray-500" />
                              <span>Copy Caption</span>
                            </>
                          )}
                        </button>
                      </div>

                      {isEditingSocial ? (
                        <textarea
                          rows={6}
                          value={editedSocial.caption || ''}
                          onChange={(e) => setEditedSocial({ ...editedSocial, caption: e.target.value })}
                          className="w-full p-3 bg-white border border-gray-300 rounded-xl text-sm font-normal text-gray-800 outline-none focus:ring-2 focus:ring-blue-500 shadow-inner"
                          placeholder="Write your post caption..."
                        />
                      ) : (
                        <div className="bg-white border border-gray-200/70 rounded-xl p-4 text-sm text-gray-800 whitespace-pre-line leading-relaxed shadow-2xs max-h-64 overflow-y-auto selection:bg-blue-100">
                          {getActiveCaptionText()}
                        </div>
                      )}
                    </div>

                    {/* Hashtags Section */}
                    <div className="bg-gray-50/70 border border-gray-200/80 rounded-2xl p-4.5 space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Hash className="w-4 h-4 text-indigo-600" />
                          <span className="text-xs font-bold text-gray-700 uppercase tracking-wider">
                            Targeted Hashtags
                          </span>
                          <span className="text-[11px] text-gray-400 font-medium">
                            ({getActiveHashtagsList().length} tags)
                          </span>
                        </div>

                        <button
                          onClick={() => copyToClipboard(getActiveHashtagsString(), 'hashtags')}
                          className="flex items-center gap-1.5 px-3 py-1 bg-white hover:bg-gray-100 border border-gray-200 text-xs font-semibold text-gray-700 rounded-lg shadow-2xs transition-all">
                          {copiedItem === 'hashtags' ? (
                            <>
                              <Check className="w-3.5 h-3.5 text-emerald-600" />
                              <span className="text-emerald-700 font-bold">Copied Hashtags!</span>
                            </>
                          ) : (
                            <>
                              <Copy className="w-3.5 h-3.5 text-gray-500" />
                              <span>Copy All Tags</span>
                            </>
                          )}
                        </button>
                      </div>

                      {/* Interactive Hashtag Chips */}
                      <div className="flex flex-wrap gap-1.5 pt-1">
                        {getActiveHashtagsList().map((tag, idx) => {
                          const isTagCopied = copiedItem === tag;
                          return (
                            <button
                              key={idx}
                              onClick={() => copyToClipboard(tag, tag)}
                              title={`Click to copy ${tag}`}
                              className={`group inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                                isTagCopied
                                  ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                                  : 'bg-white hover:bg-blue-50 text-indigo-700 border border-gray-200 hover:border-blue-300 hover:shadow-2xs'
                              }`}>
                              {isTagCopied ? (
                                <Check className="w-3 h-3 text-emerald-600" />
                              ) : (
                                <span className="text-indigo-400 group-hover:text-blue-600">#</span>
                              )}
                              <span>{tag.replace(/^#/, '')}</span>
                              {isTagCopied && <span className="text-[10px] text-emerald-600 ml-1">Copied!</span>}
                            </button>
                          );
                        })}
                      </div>

                      {isEditingSocial ? (
                        <div className="pt-2">
                          <label className="text-[11px] font-semibold text-gray-500 mb-1 block">
                            Hashtags String (space-separated):
                          </label>
                          <textarea
                            rows={2}
                            value={editedSocial.hashtags_string || (Array.isArray(editedSocial.hashtags) ? editedSocial.hashtags.join(' ') : '')}
                            onChange={(e) => {
                              const val = e.target.value;
                              const tags = val.split(/\s+/).filter((t: string) => t.trim().length > 0).map((t: string) => t.startsWith('#') ? t : `#${t}`);
                              setEditedSocial({
                                ...editedSocial,
                                hashtags_string: val,
                                hashtags: tags
                              });
                            }}
                            className="w-full p-2.5 bg-white border border-gray-300 rounded-xl text-xs text-gray-800 outline-none focus:ring-2 focus:ring-blue-500"
                          />
                        </div>
                      ) : (
                        <div className="bg-white/80 border border-dashed border-gray-200 rounded-xl p-2.5 text-xs text-gray-500 font-mono select-all">
                          {getActiveHashtagsString()}
                        </div>
                      )}
                    </div>

                    {/* Pinned Comment / Engagement Booster */}
                    {project.social_post?.engagement_question && (
                      <div className="bg-purple-50/60 border border-purple-200/70 rounded-2xl p-4.5 space-y-2">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <MessageSquare className="w-4 h-4 text-purple-600" />
                            <span className="text-xs font-bold text-purple-900 uppercase tracking-wider">
                              Suggested Pinned Comment
                            </span>
                          </div>

                          <button
                            onClick={() => copyToClipboard(project.social_post.engagement_question, 'pinned_comment')}
                            className="flex items-center gap-1.5 px-3 py-1 bg-white hover:bg-purple-100/60 border border-purple-200 text-xs font-semibold text-purple-800 rounded-lg shadow-2xs transition-all">
                            {copiedItem === 'pinned_comment' ? (
                              <>
                                <Check className="w-3.5 h-3.5 text-emerald-600" />
                                <span className="text-emerald-700 font-bold">Copied!</span>
                              </>
                            ) : (
                              <>
                                <Copy className="w-3.5 h-3.5 text-purple-500" />
                                <span>Copy Comment</span>
                              </>
                            )}
                          </button>
                        </div>
                        <p className="text-xs text-purple-950 font-medium bg-white/70 border border-purple-100 rounded-xl p-3">
                          "{project.social_post.engagement_question}"
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
