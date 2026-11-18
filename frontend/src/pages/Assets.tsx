import React, { useState, useEffect, useRef } from 'react';
import { 
  Upload, Trash2, ArrowUp, ArrowDown, Play, Download, Sparkles, 
  RefreshCw, Film, Volume2, Type, CheckCircle2, 
  AlertCircle, X, Compass, Move, ExternalLink, Plus, RotateCcw,
  Check, User
} from 'lucide-react';
import { imageToVideoApi } from '../services/api';

interface SceneItem {
  id: string;
  image_url: string;
  image_path?: string;
  filename: string;
  width?: number;
  height?: number;
  size_kb?: number;
  text: string;
  headline?: string;
  duration: number;
  motion_type: 'camera' | 'ai';
  camera_motion: string;
  ai_motion: string;
  ai_intensity: 'low' | 'medium' | 'high';
  transition: string;
  transition_duration: number;
}

interface GenerationJob {
  job_id: number;
  project_id: number;
  status: string;
  progress: number;
  current_step: string;
  video_url?: string;
  error?: string;
}

const CAMERA_MOTIONS = [
  { id: 'zoom_in', label: 'Zoom In', desc: 'Smooth slow forward camera push' },
  { id: 'zoom_out', label: 'Zoom Out', desc: 'Gradual backward reveal' },
  { id: 'pan_left', label: 'Pan Left', desc: 'Horizontal sweep from right to left' },
  { id: 'pan_right', label: 'Pan Right', desc: 'Horizontal sweep from left to right' },
  { id: 'pan_up', label: 'Pan Up', desc: 'Vertical crane camera rise' },
  { id: 'pan_down', label: 'Pan Down', desc: 'Vertical tilt downwards' },
  { id: 'ken_burns', label: 'Ken Burns', desc: 'Classic documentary zoom & pan' },
  { id: 'cinematic', label: 'Cinematic Dynamic', desc: 'Sophisticated slow orbital motion' },
  { id: 'parallax', label: '2.5D Parallax', desc: 'Simulated multi-depth focal push' },
];

const AI_MOTIONS = [
  { id: 'natural_flow', label: 'Natural Flow', desc: 'Organic ambient motion for nature & landscapes' },
  { id: 'wind_breeze', label: 'Wind & Breeze', desc: 'Subtle swaying of foliage, trees & fabrics' },
  { id: 'ambient_living', label: 'Ambient Living', desc: 'Living atmosphere with subtle pulse & drift' },
  { id: 'cinematic_dynamic', label: 'Cinematic Dynamic', desc: 'Dramatic depth expansion and micro-shifts' },
  { id: 'ocean_waves', label: 'Water & Waves', desc: 'Fluid ripple and shoreline water movement' },
];

const TRANSITIONS = [
  { id: 'fade', label: 'Fade to Black' },
  { id: 'crossfade', label: 'Smooth Crossfade' },
  { id: 'slideleft', label: 'Slide Left' },
  { id: 'slideright', label: 'Slide Right' },
  { id: 'slideup', label: 'Slide Up' },
  { id: 'slidedown', label: 'Slide Down' },
  { id: 'zoom', label: 'Zoom Transition' },
  { id: 'dissolve', label: 'Dissolve' },
  { id: 'blur', label: 'Blur Transition' },
];

const SUBTITLE_COLOR_PRESETS = [
  { label: 'White', color: '#FFFFFF' },
  { label: 'Yellow', color: '#FACC15' },
  { label: 'Cyan', color: '#22D3EE' },
  { label: 'Amber', color: '#F59E0B' },
];

export const SUBTITLE_FONTS = [
  { id: 'Inter', label: 'Inter Clean', family: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif', weight: 600, letterSpacing: 'normal' },
  { id: 'Arial', label: 'Arial Bold', family: 'Arial, "Helvetica Neue", Helvetica, sans-serif', weight: 700, letterSpacing: 'normal' },
  { id: 'Georgia', label: 'Georgia Cinematic', family: 'Georgia, "Times New Roman", Cambria, serif', weight: 700, letterSpacing: 'normal' },
  { id: 'Impact', label: 'Impact Bold', family: 'Impact, "Arial Black", "Trebuchet MS", sans-serif', weight: 900, letterSpacing: '0.04em' },
];

export const getSubtitleFontFamily = (fontId: string) => {
  const match = SUBTITLE_FONTS.find(f => f.id.toLowerCase() === (fontId || '').toLowerCase());
  return match ? match.family : '"Inter", system-ui, -apple-system, sans-serif';
};

export const getSubtitleFontWeight = (fontId: string) => {
  const match = SUBTITLE_FONTS.find(f => f.id.toLowerCase() === (fontId || '').toLowerCase());
  return match ? match.weight : 600;
};

export const getSubtitleLetterSpacing = (fontId: string) => {
  const match = SUBTITLE_FONTS.find(f => f.id.toLowerCase() === (fontId || '').toLowerCase());
  return match ? match.letterSpacing : 'normal';
};

export const resolveMediaUrl = (url?: string | null): string => {
  if (!url) return '';
  if (url.startsWith('http://') || url.startsWith('https://')) return url;
  const clean = url.startsWith('/') ? url : `/${url}`;
  return `http://localhost:8000${clean}`;
};

export default function Assets() {
  // Main Scenes state
  const [scenes, setScenes] = useState<SceneItem[]>([]);
  const [activeSceneIndex, setActiveSceneIndex] = useState<number>(0);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Settings
  const [aspectRatio, setAspectRatio] = useState<'16:9' | '9:16' | '1:1'>('16:9');
  const [resolution, setResolution] = useState<'720p' | '1080p'>('1080p');
  
  // Voice Narration state: Two options only (Female & Male) + Custom Audio upload
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [selectedVoice, setSelectedVoice] = useState<'en-US-JennyNeural' | 'en-US-GuyNeural'>('en-US-JennyNeural');
  const [customAudioUrl, setCustomAudioUrl] = useState<string | null>(null);
  const [customAudioPath, setCustomAudioPath] = useState<string | null>(null);
  const [narrationVolume, setNarrationVolume] = useState(1.0);

  // Subtitle state
  const [subtitleEnabled, setSubtitleEnabled] = useState(true);
  const [subtitleFont, setSubtitleFont] = useState('Inter');
  const [subtitleFontSize, setSubtitleFontSize] = useState<'small' | 'medium' | 'large'>('medium');
  const [subtitleColor, setSubtitleColor] = useState('#FFFFFF');
  const [subtitleBg, setSubtitleBg] = useState<'translucent' | 'solid' | 'none'>('translucent');
  const [subtitlePosition, setSubtitlePosition] = useState<'bottom' | 'center' | 'top'>('bottom');

  // Script Modal state (AI generator & Custom script)
  const [showScriptModal, setShowScriptModal] = useState(false);
  const [scriptModalTab, setScriptModalTab] = useState<'ai' | 'custom'>('ai');
  const [aiTopic, setAiTopic] = useState('');
  const [aiTone, setAiTone] = useState('Inspiring');
  const [isGeneratingScript, setIsGeneratingScript] = useState(false);
  const [generatedAiScenes, setGeneratedAiScenes] = useState<Array<{ scene_index: number; headline: string; text: string }>>([]);
  const [rewritingSceneIndex, setRewritingSceneIndex] = useState<number | null>(null);
  const [bulkScript, setBulkScript] = useState('');

  // Scene Preview Modal
  const [previewingScene, setPreviewingScene] = useState<SceneItem | null>(null);
  const [scenePreviewUrl, setScenePreviewUrl] = useState<string | null>(null);
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);

  // Generation & Status
  const [isGenerating, setIsGenerating] = useState(false);
  const [currentJob, setCurrentJob] = useState<GenerationJob | null>(null);
  const [recentProjects, setRecentProjects] = useState<any[]>([]);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const audioInputRef = useRef<HTMLInputElement>(null);

  // Load recent projects on mount
  useEffect(() => {
    loadRecentProjects();
  }, []);

  const loadRecentProjects = async () => {
    try {
      const projects = await imageToVideoApi.getRecentProjects();
      setRecentProjects(projects || []);

      // Automatically display the most recent completed video if idle
      if (projects && projects.length > 0) {
        const latest = projects[0];
        if (latest.video_url && (latest.status || '').toLowerCase() === 'completed') {
          setCurrentJob(prev => {
            if (!prev) {
              return {
                job_id: latest.id,
                project_id: latest.id,
                status: 'completed',
                progress: 100,
                current_step: 'Completed',
                video_url: latest.video_url,
              };
            }
            return prev;
          });
        }
      }
    } catch (err) {
      console.warn('Failed to load recent projects:', err);
    }
  };

  // Drag and drop handlers (JPG, JPEG, PNG, WEBP, and JFIF)
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFilesUpload(Array.from(e.dataTransfer.files));
    }
  };

  const handleFilesUpload = async (files: File[]) => {
    setUploadError(null);
    const validExtensions = ['jpg', 'jpeg', 'png', 'webp', 'jfif'];
    const validFiles = files.filter(f => {
      const ext = f.name.split('.').pop()?.toLowerCase() || '';
      return validExtensions.includes(ext);
    });

    if (validFiles.length === 0) {
      setUploadError('Please select valid image files (JPG, JPEG, PNG, WEBP, or JFIF).');
      return;
    }

    setIsUploading(true);
    try {
      const res = await imageToVideoApi.uploadImages(validFiles);
      const uploadedList = res?.images || res?.uploaded || [];
      if (uploadedList && uploadedList.length > 0) {
        const newScenes: SceneItem[] = uploadedList.map((img: any, idx: number) => ({
          id: `scene_${Date.now()}_${idx}_${Math.random().toString(36).substring(2, 6)}`,
          image_url: img.url,
          image_path: img.file_path,
          filename: img.filename,
          width: img.width,
          height: img.height,
          size_kb: img.file_size ? Math.round(img.file_size / 1024) : img.size_kb,
          text: `Scene ${scenes.length + idx + 1}: Captivating visual moment.`,
          duration: 4.0,
          motion_type: 'camera',
          camera_motion: CAMERA_MOTIONS[idx % CAMERA_MOTIONS.length].id,
          ai_motion: AI_MOTIONS[idx % AI_MOTIONS.length].id,
          ai_intensity: 'medium',
          transition: 'crossfade',
          transition_duration: 1.0,
        }));

        setScenes(prev => [...prev, ...newScenes]);
      }
    } catch (err: any) {
      setUploadError(err.response?.data?.detail || 'Failed to upload images. Check file sizes and formats.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleCustomAudioUpload = async (file: File) => {
    try {
      const res = await imageToVideoApi.uploadAudio(file);
      const audioData = res?.audio || res;
      if (audioData && audioData.url) {
        setCustomAudioUrl(audioData.url);
        setCustomAudioPath(audioData.file_path);
      }
    } catch (err) {
      alert('Failed to upload custom audio file.');
    }
  };

  // Reordering & Scene actions
  const moveScene = (index: number, direction: 'up' | 'down') => {
    const targetIndex = direction === 'up' ? index - 1 : index + 1;
    if (targetIndex < 0 || targetIndex >= scenes.length) return;
    const updated = [...scenes];
    const temp = updated[index];
    updated[index] = updated[targetIndex];
    updated[targetIndex] = temp;
    setScenes(updated);
    setActiveSceneIndex(targetIndex);
  };

  const removeScene = (index: number) => {
    setScenes(prev => prev.filter((_, i) => i !== index));
    if (activeSceneIndex >= scenes.length - 1) {
      setActiveSceneIndex(Math.max(0, scenes.length - 2));
    }
  };

  const updateScene = (index: number, patch: Partial<SceneItem>) => {
    setScenes(prev => {
      const next = [...prev];
      next[index] = { ...next[index], ...patch };
      return next;
    });
  };

  // Auto infer topic from uploaded scenes if aiTopic is empty
  const getSuggestedTopic = () => {
    if (scenes.length === 0) return '';
    const names = scenes.map(s => {
      const fn = s.filename || '';
      const noExt = fn.replace(/\.[^/.]+$/, '');
      const clean = noExt.replace(/^[a-f0-9]{8,16}_/, '').replace(/[_\W]+/g, ' ').trim();
      return clean;
    }).filter(n => n && !n.toLowerCase().startsWith('temp') && !/^(image|img|\d+)$/i.test(n));
    return names.length > 0 ? names[0].charAt(0).toUpperCase() + names[0].slice(1) : 'Visual Story';
  };

  const handleGenerateAiScript = async (topicOverride?: string) => {
    if (scenes.length === 0) {
      alert('Please upload one or more images first.');
      return;
    }
    const topicToUse = topicOverride || aiTopic.trim() || getSuggestedTopic();
    setIsGeneratingScript(true);
    try {
      const res = await imageToVideoApi.generateScript({
        topic: topicToUse,
        tone: aiTone,
        scenes_count: scenes.length,
        images_info: scenes.map((s, i) => ({ filename: s.filename, scene_index: i + 1 })),
      });

      if (res && res.scenes && res.scenes.length > 0) {
        setGeneratedAiScenes(res.scenes);
        if (!aiTopic && res.topic) {
          setAiTopic(res.topic);
        }
      }
    } catch (err: any) {
      alert('Failed to generate AI script. Please check your topic or try again.');
    } finally {
      setIsGeneratingScript(false);
    }
  };

  const applyGeneratedAiScript = () => {
    if (!generatedAiScenes || generatedAiScenes.length === 0) return;
    setScenes(prev =>
      prev.map((sc, i) => {
        if (i < generatedAiScenes.length) {
          return {
            ...sc,
            text: generatedAiScenes[i].text,
            headline: generatedAiScenes[i].headline || sc.headline,
          };
        }
        return sc;
      })
    );
    setShowScriptModal(false);
  };

  const handleRewriteSingleScene = async (sceneIdx: number) => {
    if (sceneIdx < 0 || sceneIdx >= scenes.length) return;
    const targetScene = scenes[sceneIdx];
    setRewritingSceneIndex(sceneIdx);
    try {
      const res = await imageToVideoApi.rewriteSceneScript({
        scene_index: sceneIdx + 1,
        current_text: targetScene.text || '',
        topic: aiTopic || getSuggestedTopic(),
        tone: aiTone,
        filename: targetScene.filename,
      });

      if (res && res.text) {
        updateScene(sceneIdx, {
          text: res.text,
          headline: res.headline || targetScene.headline,
        });
      }
    } catch (err) {
      console.warn('Failed to rewrite scene script:', err);
    } finally {
      setRewritingSceneIndex(null);
    }
  };

  // Distribute bulk script into scenes
  const applyBulkScript = () => {
    const lines = bulkScript
      .split('\n')
      .map(l => l.trim())
      .filter(l => l.length > 0);

    if (lines.length === 0) return;

    setScenes(prev =>
      prev.map((sc, i) => {
        if (i < lines.length) {
          return { ...sc, text: lines[i] };
        }
        return sc;
      })
    );
    setShowScriptModal(false);
  };

  // Preview individual scene with subtitles and selected voice
  const handlePreviewScene = async (scene: SceneItem) => {
    setPreviewingScene(scene);
    setScenePreviewUrl(null);
    setIsPreviewLoading(true);

    try {
      const res = await imageToVideoApi.previewScene({
        image_url: scene.image_url,
        motion_type: scene.motion_type,
        camera_motion: scene.camera_motion,
        ai_motion: scene.ai_motion,
        ai_intensity: scene.ai_intensity,
        duration: scene.duration,
        aspect_ratio: aspectRatio,
        text: scene.text,
        voice_id: selectedVoice,
        voice_enabled: voiceEnabled,
        subtitles_enabled: subtitleEnabled,
        subtitle_font: subtitleFont,
        subtitle_size: subtitleFontSize,
        subtitle_color: subtitleColor,
        subtitle_bg: subtitleBg,
        subtitle_position: subtitlePosition,
      });

      const pUrl = res?.preview_url || res?.preview_video_url;
      if (pUrl) {
        setScenePreviewUrl(pUrl);
      }
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Scene preview rendering failed.');
      setPreviewingScene(null);
    } finally {
      setIsPreviewLoading(false);
    }
  };

  // Full Video Generation (No background music)
  const handleGenerateVideo = async () => {
    if (scenes.length === 0) {
      alert('Please upload at least one image before generating a video.');
      return;
    }

    setIsGenerating(true);
    setCurrentJob({
      job_id: 0,
      project_id: 0,
      status: 'Rendering',
      progress: 5,
      current_step: 'Submitting video generation job...',
    });

    try {
      const payload = {
        title: `Image-to-Video - ${new Date().toLocaleDateString()}`,
        aspect_ratio: aspectRatio,
        resolution: resolution,
        scenes: scenes.map(s => ({
          image_url: s.image_url,
          image_path: s.image_path,
          text: s.text,
          duration: s.duration,
          motion_type: s.motion_type,
          camera_motion: s.camera_motion,
          ai_motion: s.ai_motion,
          ai_intensity: s.ai_intensity,
          transition: s.transition,
          transition_duration: s.transition_duration,
        })),
        settings: {
          aspect_ratio: aspectRatio,
          resolution: resolution,
          voice_enabled: voiceEnabled,
          voice_id: selectedVoice,
          custom_audio_url: customAudioUrl,
          custom_audio_path: customAudioPath,
          narration_volume: narrationVolume,
          music_enabled: false,
          subtitle_enabled: subtitleEnabled,
          subtitles_enabled: subtitleEnabled,
          subtitle_font: subtitleFont,
          subtitle_size: subtitleFontSize,
          subtitle_color: subtitleColor,
          subtitle_bg: subtitleBg,
          subtitle_position: subtitlePosition,
        },
      };

      const res = await imageToVideoApi.generateVideo(payload);
      if (res && res.job_id) {
        setCurrentJob({
          job_id: res.job_id,
          project_id: res.job_id,
          status: 'Rendering',
          progress: 10,
          current_step: 'Starting rendering engine...',
        });

        // Start polling status
        pollJobStatus(res.job_id);
      }
    } catch (err: any) {
      setIsGenerating(false);
      setCurrentJob(null);
      alert(err.response?.data?.detail || 'Video generation failed to initialize.');
    }
  };

  const pollJobStatus = async (jobId: number) => {
    const interval = setInterval(async () => {
      try {
        const status = await imageToVideoApi.getJobStatus(jobId);
        setCurrentJob(status);

        const normStatus = (status?.status || '').toLowerCase();
        if (normStatus === 'completed') {
          clearInterval(interval);
          setIsGenerating(false);
          loadRecentProjects();
        } else if (normStatus === 'failed') {
          clearInterval(interval);
          setIsGenerating(false);
        }
      } catch (err) {
        clearInterval(interval);
        setIsGenerating(false);
      }
    }, 1500);
  };

  const totalDuration = scenes.reduce((sum, s) => sum + s.duration, 0);

  // Status checks normalized to lowercase
  const isJobCompleted = (currentJob?.status || '').toLowerCase() === 'completed';
  const isJobFailed = (currentJob?.status || '').toLowerCase() === 'failed';
  const isJobRendering = isGenerating || (Boolean(currentJob) && !isJobCompleted && !isJobFailed);
  const currentVideoUrl = resolveMediaUrl(currentJob?.video_url);

  return (
    <div className="p-8 max-w-7xl mx-auto h-full flex flex-col space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-gray-100">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-3xl font-black text-gray-900 tracking-tight">Image-to-Video</h2>
            <span className="px-2.5 py-0.5 text-xs font-bold bg-blue-50 text-blue-700 border border-blue-200 rounded-full">
              Automated Motion Pipeline
            </span>
          </div>
          <p className="text-sm font-medium text-gray-500 mt-1">
            Transform photos into cinematic videos with AI living motion, narration, synchronized subtitles, and transitions.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              if (confirm('Clear all scenes and reset?')) {
                setScenes([]);
              }
            }}
            disabled={scenes.length === 0 || isJobRendering}
            className="flex items-center gap-2 px-4 py-2.5 border border-gray-200 hover:bg-gray-100 text-gray-700 font-semibold rounded-xl text-sm transition-all disabled:opacity-50 cursor-pointer"
          >
            <RotateCcw className="w-4 h-4" />
            Reset
          </button>

          <button
            onClick={handleGenerateVideo}
            disabled={scenes.length === 0 || isJobRendering}
            className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-blue-600 via-blue-700 to-orange-500 hover:from-blue-700 hover:to-orange-600 text-white font-bold rounded-xl shadow-lg shadow-blue-500/20 text-sm transition-all disabled:opacity-50 cursor-pointer"
          >
            {isJobRendering ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Rendering Video...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 text-orange-200" />
                Generate Video ({scenes.length} {scenes.length === 1 ? 'Scene' : 'Scenes'})
              </>
            )}
          </button>
        </div>
      </div>

      {/* Video Settings Bar */}
      <div className="bg-white rounded-2xl border border-gray-100 p-4 shadow-sm flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Aspect Ratio:</span>
            <div className="flex bg-gray-100 p-1 rounded-lg">
              {(['16:9', '9:16', '1:1'] as const).map(ratio => (
                <button
                  key={ratio}
                  onClick={() => setAspectRatio(ratio)}
                  className={`px-3 py-1 rounded-md text-xs font-bold transition-all cursor-pointer ${
                    aspectRatio === ratio
                      ? 'bg-white text-blue-700 shadow-sm'
                      : 'text-gray-500 hover:text-gray-900'
                  }`}
                >
                  {ratio === '16:9' ? '16:9 Landscape' : ratio === '9:16' ? '9:16 Portrait' : '1:1 Square'}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Resolution:</span>
            <div className="flex bg-gray-100 p-1 rounded-lg">
              {(['1080p', '720p'] as const).map(res => (
                <button
                  key={res}
                  onClick={() => setResolution(res)}
                  className={`px-3 py-1 rounded-md text-xs font-bold transition-all cursor-pointer ${
                    resolution === res
                      ? 'bg-white text-blue-700 shadow-sm'
                      : 'text-gray-500 hover:text-gray-900'
                  }`}
                >
                  {res}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4 text-xs font-semibold text-gray-500">
          <span className="flex items-center gap-1.5 bg-blue-50 text-blue-700 px-3 py-1 rounded-full border border-blue-100">
            <Film className="w-3.5 h-3.5" /> {scenes.length} Scenes
          </span>
          <span className="flex items-center gap-1.5 bg-orange-50 text-orange-700 px-3 py-1 rounded-full border border-orange-100">
            Duration: ~{Math.round(totalDuration)}s
          </span>
        </div>
      </div>

      {/* Generation Progress Banner */}
      {isJobRendering && currentJob && (
        <div className="bg-blue-50 border border-blue-200 rounded-2xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2 font-bold text-blue-900 text-sm">
              <RefreshCw className="w-4 h-4 animate-spin text-blue-600" />
              <span>{currentJob.current_step || 'Processing video generation...'}</span>
            </div>
            <span className="text-xs font-black text-blue-700">{currentJob.progress}%</span>
          </div>
          <div className="w-full bg-blue-200 h-2.5 rounded-full overflow-hidden">
            <div 
              className="bg-gradient-to-r from-blue-600 to-orange-500 h-full rounded-full transition-all duration-300"
              style={{ width: `${Math.max(5, currentJob.progress)}%` }}
            />
          </div>
        </div>
      )}

      {/* Error Alert */}
      {isJobFailed && currentJob && (
        <div className="bg-red-50 border border-red-200 rounded-2xl p-5 shadow-sm text-xs font-semibold text-red-700 flex items-center gap-2">
          <AlertCircle className="w-5 h-5 shrink-0 text-red-600" />
          <span>Generation failed: {currentJob.error || 'FFmpeg process encountered an unexpected issue.'}</span>
        </div>
      )}

      {/* Generated Video Ready & Player Card */}
      {isJobCompleted && currentVideoUrl && (
        <div className="bg-gradient-to-br from-emerald-50 via-teal-50 to-blue-50 border-2 border-emerald-300 rounded-3xl p-6 shadow-xl flex flex-col md:flex-row items-center gap-6">
          <div className="w-full md:w-96 rounded-2xl overflow-hidden shadow-2xl border-2 border-emerald-200 bg-black aspect-video flex items-center justify-center relative">
            <video 
              key={currentVideoUrl}
              src={currentVideoUrl} 
              controls 
              playsInline
              autoPlay
              className="w-full h-full object-contain"
            />
          </div>
          <div className="flex-1 space-y-3">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-100 text-emerald-800 rounded-full text-xs font-extrabold">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              Video Generated Successfully
            </div>
            <h3 className="text-2xl font-black text-gray-900">Your Video is Ready!</h3>
            <p className="text-xs text-gray-600 leading-relaxed">
              Synthesized voiceover, camera & AI motion effects, synchronized subtitles, and transitions have been combined into a high-definition MP4.
            </p>
            <div className="flex flex-wrap items-center gap-3 pt-2">
              <a
                href={currentJob?.job_id ? `http://localhost:8000/api/image-to-video/download/${currentJob.job_id}` : currentVideoUrl}
                download={`image_to_video_${currentJob?.job_id || Date.now()}.mp4`}
                className="flex items-center gap-2 px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl shadow-lg shadow-emerald-500/20 text-sm transition-all cursor-pointer"
              >
                <Download className="w-4 h-4" />
                Download Video (MP4)
              </a>
              <a
                href={currentVideoUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 px-4 py-3 bg-white border border-gray-200 text-gray-700 font-semibold rounded-xl text-sm hover:bg-gray-50 shadow-sm transition-all cursor-pointer"
              >
                <ExternalLink className="w-4 h-4" />
                Open Fullscreen
              </a>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(currentVideoUrl);
                  alert('Video URL copied to clipboard!');
                }}
                className="px-4 py-3 bg-white border border-gray-200 text-gray-700 font-semibold rounded-xl text-sm hover:bg-gray-50 shadow-sm transition-all cursor-pointer"
              >
                Copy Link
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Workspace 2-Column Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Image Upload & Scenes Timeline (2 cols) */}
        <div className="lg:col-span-2 space-y-6">
          {/* Upload Zone (JPG, JPEG, PNG, WEBP, and JFIF) */}
          <div
            onDragOver={e => e.preventDefault()}
            onDrop={handleDrop}
            className="border-2 border-dashed border-blue-200 hover:border-blue-400 bg-blue-50/30 rounded-2xl p-6 transition-all text-center flex flex-col items-center justify-center gap-3"
          >
            <div className="w-12 h-12 rounded-2xl bg-blue-100 text-blue-600 flex items-center justify-center">
              <Upload className="w-6 h-6" />
            </div>
            <div>
              <h4 className="text-base font-bold text-gray-900">
                Drag & drop your images here, or{' '}
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="text-blue-600 hover:underline cursor-pointer"
                >
                  browse files
                </button>
              </h4>
              <p className="text-xs text-gray-500 mt-1">
                Supports JPG, JPEG, PNG, WEBP, and JFIF. Upload multiple images to create a multi-scene video.
              </p>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept="image/jpeg,image/png,image/webp,image/jfif,.jfif,.jpg,.jpeg,.png,.webp"
              className="hidden"
              onChange={e => {
                if (e.target.files && e.target.files.length > 0) {
                  handleFilesUpload(Array.from(e.target.files));
                }
              }}
            />
            {isUploading && (
              <div className="flex items-center gap-2 text-xs font-bold text-blue-600">
                <RefreshCw className="w-4 h-4 animate-spin" /> Uploading & inspecting image dimensions...
              </div>
            )}
            {uploadError && (
              <div className="text-xs font-semibold text-red-600 flex items-center gap-1">
                <AlertCircle className="w-4 h-4" /> {uploadError}
              </div>
            )}
          </div>

          {/* Timeline & Scene Editor */}
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <Film className="w-5 h-5 text-blue-600" />
                <h3 className="text-lg font-black text-gray-900 tracking-tight">Scenes & Script Timeline</h3>
                <span className="text-xs font-bold bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
                  {scenes.length}
                </span>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setScriptModalTab('ai');
                    if (!aiTopic) setAiTopic(getSuggestedTopic());
                    setShowScriptModal(true);
                  }}
                  disabled={scenes.length === 0}
                  className="flex items-center gap-1.5 text-xs font-bold text-white bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 px-3.5 py-1.5 rounded-lg shadow-xs transition-all cursor-pointer disabled:opacity-40"
                  title="Generate engaging scene scripts and subtitles with AI"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Generate Script with AI</span>
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setScriptModalTab('custom');
                    setShowScriptModal(true);
                  }}
                  disabled={scenes.length === 0}
                  className="flex items-center gap-1.5 text-xs font-bold text-blue-700 hover:text-blue-800 bg-blue-50 hover:bg-blue-100 px-3 py-1.5 rounded-lg border border-blue-200 transition-colors cursor-pointer disabled:opacity-40"
                  title="Enter or paste your own custom script"
                >
                  <Type className="w-3.5 h-3.5" />
                  <span>Custom Script (Paste / Write)</span>
                </button>

                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="flex items-center gap-1 text-xs font-bold text-gray-700 bg-white hover:bg-gray-50 border border-gray-200 px-3 py-1.5 rounded-lg shadow-2xs transition-colors cursor-pointer"
                >
                  <Plus className="w-3.5 h-3.5" /> Add Images
                </button>
              </div>
            </div>

            {/* Script Choice Quick Banner */}
            {scenes.length > 0 && (
              <div className="bg-gradient-to-r from-purple-50 via-blue-50 to-indigo-50 border border-purple-100 rounded-xl p-3 flex flex-col sm:flex-row items-center justify-between gap-3 shadow-2xs">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-purple-600 text-white flex items-center justify-center shrink-0 shadow-xs">
                    <Sparkles className="w-4 h-4" />
                  </div>
                  <div>
                    <h5 className="text-xs font-black text-gray-900">
                      {scenes.length} Images Uploaded for Scripting & Video
                    </h5>
                    <p className="text-[11px] text-gray-600">
                      Let AI craft personalized narration for each image, or provide your own custom script.
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <button
                    type="button"
                    onClick={() => {
                      setScriptModalTab('ai');
                      if (!aiTopic) setAiTopic(getSuggestedTopic());
                      setShowScriptModal(true);
                    }}
                    className="flex items-center gap-1.5 text-xs font-bold text-white bg-purple-600 hover:bg-purple-700 px-3 py-1.5 rounded-lg shadow-xs cursor-pointer transition-colors"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    Generate with AI
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setScriptModalTab('custom');
                      setShowScriptModal(true);
                    }}
                    className="flex items-center gap-1.5 text-xs font-bold text-gray-700 bg-white hover:bg-gray-100 border border-gray-200 px-3 py-1.5 rounded-lg shadow-2xs cursor-pointer transition-colors"
                  >
                    <Type className="w-3.5 h-3.5" />
                    Write My Own Script
                  </button>
                </div>
              </div>
            )}

            {scenes.length === 0 ? (
              <div className="bg-white rounded-2xl border border-gray-100 p-12 text-center text-gray-400">
                <Film className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                <h4 className="text-base font-bold text-gray-700">No scenes created yet</h4>
                <p className="text-xs text-gray-500 mt-1 max-w-sm mx-auto">
                  Upload one or more images above (JPG, PNG, WEBP, or JFIF). Each image becomes an animated scene with voice narration and synchronized subtitles.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {scenes.map((scene, idx) => (
                  <div
                    key={scene.id}
                    className={`bg-white rounded-2xl border transition-all p-5 shadow-sm ${
                      activeSceneIndex === idx
                        ? 'border-blue-500 ring-2 ring-blue-100'
                        : 'border-gray-100 hover:border-gray-200'
                    }`}
                    onClick={() => setActiveSceneIndex(idx)}
                  >
                    <div className="flex flex-col md:flex-row gap-5">
                      {/* Thumbnail & File Details */}
                      <div className="w-full md:w-44 shrink-0 flex flex-col gap-2">
                        <div className="relative aspect-video rounded-xl overflow-hidden bg-gray-900 border border-gray-200 group">
                          <img
                            src={resolveMediaUrl(scene.image_url)}
                            alt={scene.filename}
                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                          />
                          <div className="absolute top-2 left-2 bg-black/70 backdrop-blur-md text-white text-[10px] font-black px-2 py-0.5 rounded-md">
                            Scene {idx + 1}
                          </div>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handlePreviewScene(scene);
                            }}
                            className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity text-white text-xs font-bold gap-1 cursor-pointer"
                          >
                            <Play className="w-4 h-4 fill-white" /> Preview Scene
                          </button>
                        </div>

                        <div className="text-[11px] text-gray-400 flex justify-between font-semibold px-1">
                          <span>{scene.width && scene.height ? `${scene.width}x${scene.height}` : 'Image'}</span>
                          <span>{scene.size_kb ? `${scene.size_kb} KB` : ''}</span>
                        </div>

                        {/* Reorder & Delete controls */}
                        <div className="flex items-center justify-between pt-1 border-t border-gray-100">
                          <div className="flex items-center gap-1">
                            <button
                              disabled={idx === 0}
                              onClick={(e) => {
                                e.stopPropagation();
                                moveScene(idx, 'up');
                              }}
                              title="Move scene up"
                              className="p-1 rounded-md text-gray-400 hover:text-blue-600 hover:bg-blue-50 disabled:opacity-20 cursor-pointer"
                            >
                              <ArrowUp className="w-4 h-4" />
                            </button>
                            <button
                              disabled={idx === scenes.length - 1}
                              onClick={(e) => {
                                e.stopPropagation();
                                moveScene(idx, 'down');
                              }}
                              title="Move scene down"
                              className="p-1 rounded-md text-gray-400 hover:text-blue-600 hover:bg-blue-50 disabled:opacity-20 cursor-pointer"
                            >
                              <ArrowDown className="w-4 h-4" />
                            </button>
                          </div>

                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              removeScene(idx);
                            }}
                            title="Delete scene"
                            className="p-1 rounded-md text-gray-400 hover:text-red-600 hover:bg-red-50 cursor-pointer"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>

                      {/* Scene Configurations: Text, Motion & Transition */}
                      <div className="flex-1 space-y-4">
                        {/* Narration Script Text */}
                        <div>
                          <div className="flex items-center justify-between mb-1">
                            <label className="block text-xs font-bold text-gray-700">
                              Scene Script & Subtitle Text
                            </label>
                            <div className="flex items-center gap-2">
                              <span className="text-[10px] text-gray-400 font-medium">
                                {scene.text ? `${scene.text.trim().split(/\s+/).length} words (~${Math.max(2, Math.round(scene.text.trim().split(/\s+/).length / 3))}s)` : '0 words'}
                              </span>
                              <button
                                type="button"
                                disabled={rewritingSceneIndex === idx}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleRewriteSingleScene(idx);
                                }}
                                className="flex items-center gap-1 text-[10px] font-bold text-purple-600 hover:text-purple-700 bg-purple-50 hover:bg-purple-100 px-2 py-0.5 rounded-md border border-purple-200 transition-colors cursor-pointer disabled:opacity-50"
                                title="Rewrite and polish this scene's script with AI"
                              >
                                {rewritingSceneIndex === idx ? (
                                  <RefreshCw className="w-3 h-3 animate-spin text-purple-600" />
                                ) : (
                                  <Sparkles className="w-3 h-3 text-purple-600" />
                                )}
                                <span>AI Rewrite</span>
                              </button>
                            </div>
                          </div>
                          <textarea
                            value={scene.text}
                            onChange={(e) => updateScene(idx, { text: e.target.value })}
                            rows={2}
                            placeholder="Enter the voiceover script and subtitle for this scene..."
                            className="w-full text-xs font-medium p-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none resize-none"
                          />
                        </div>

                        {/* Controls Grid */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {/* Motion Mode Selector */}
                          <div className="bg-gray-50/70 p-3 rounded-xl border border-gray-100">
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-[11px] font-bold text-gray-700 flex items-center gap-1">
                                {scene.motion_type === 'camera' ? (
                                  <Compass className="w-3.5 h-3.5 text-blue-600" />
                                ) : (
                                  <Sparkles className="w-3.5 h-3.5 text-orange-500" />
                                )}
                                Motion Effect
                              </span>
                              <div className="flex bg-gray-200/80 p-0.5 rounded-lg text-[10px] font-bold">
                                <button
                                  type="button"
                                  onClick={() => updateScene(idx, { motion_type: 'camera' })}
                                  className={`px-2 py-0.5 rounded-md transition-all cursor-pointer ${
                                    scene.motion_type === 'camera' ? 'bg-white text-blue-700 shadow-xs' : 'text-gray-600'
                                  }`}
                                >
                                  Camera
                                </button>
                                <button
                                  type="button"
                                  onClick={() => updateScene(idx, { motion_type: 'ai' })}
                                  className={`px-2 py-0.5 rounded-md transition-all cursor-pointer ${
                                    scene.motion_type === 'ai' ? 'bg-white text-orange-600 shadow-xs' : 'text-gray-600'
                                  }`}
                                >
                                  AI Motion
                                </button>
                              </div>
                            </div>

                            {scene.motion_type === 'camera' ? (
                              <select
                                value={scene.camera_motion}
                                onChange={(e) => updateScene(idx, { camera_motion: e.target.value })}
                                className="w-full text-xs font-semibold bg-white border border-gray-200 rounded-lg p-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500"
                              >
                                {CAMERA_MOTIONS.map(m => (
                                  <option key={m.id} value={m.id}>
                                    {m.label} ({m.desc})
                                  </option>
                                ))}
                              </select>
                            ) : (
                              <div className="space-y-2">
                                <select
                                  value={scene.ai_motion}
                                  onChange={(e) => updateScene(idx, { ai_motion: e.target.value })}
                                  className="w-full text-xs font-semibold bg-white border border-gray-200 rounded-lg p-1.5 focus:outline-none focus:ring-1 focus:ring-orange-500"
                                >
                                  {AI_MOTIONS.map(m => (
                                    <option key={m.id} value={m.id}>
                                      {m.label} ({m.desc})
                                    </option>
                                  ))}
                                </select>
                                <div className="flex items-center justify-between text-[10px] font-bold text-gray-500">
                                  <span>Intensity:</span>
                                  <div className="flex gap-1">
                                    {(['low', 'medium', 'high'] as const).map(lvl => (
                                      <button
                                        key={lvl}
                                        type="button"
                                        onClick={() => updateScene(idx, { ai_intensity: lvl })}
                                        className={`px-2 py-0.5 rounded uppercase text-[9px] cursor-pointer ${
                                          scene.ai_intensity === lvl
                                            ? 'bg-orange-500 text-white font-extrabold'
                                            : 'bg-gray-200 text-gray-600'
                                        }`}
                                      >
                                        {lvl}
                                      </button>
                                    ))}
                                  </div>
                                </div>
                              </div>
                            )}
                          </div>

                          {/* Transition to next scene */}
                          <div className="bg-gray-50/70 p-3 rounded-xl border border-gray-100">
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-[11px] font-bold text-gray-700 flex items-center gap-1">
                                <Move className="w-3.5 h-3.5 text-blue-600" />
                                Next Scene Transition
                              </span>
                              <span className="text-[10px] text-gray-400 font-semibold">
                                {idx === scenes.length - 1 ? 'Outro Fade' : `Scene ${idx + 1} ➔ ${idx + 2}`}
                              </span>
                            </div>

                            <select
                              value={scene.transition}
                              onChange={(e) => updateScene(idx, { transition: e.target.value })}
                              className="w-full text-xs font-semibold bg-white border border-gray-200 rounded-lg p-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500"
                            >
                              {TRANSITIONS.map(t => (
                                <option key={t.id} value={t.id}>
                                  {t.label}
                                </option>
                              ))}
                            </select>

                            <div className="flex items-center justify-between mt-2 text-[10px] font-bold text-gray-500">
                              <span>Scene Duration:</span>
                              <div className="flex items-center gap-2">
                                <input
                                  type="range"
                                  min="2"
                                  max="12"
                                  step="0.5"
                                  value={scene.duration}
                                  onChange={(e) => updateScene(idx, { duration: parseFloat(e.target.value) })}
                                  className="w-20 accent-blue-600 cursor-pointer"
                                />
                                <span className="w-8 text-right font-black text-gray-700">{scene.duration}s</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Audio & Subtitles Customization (1 col) */}
        <div className="space-y-6">
          {/* Card: Voiceover Narration (Female & Male Only) */}
          <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
                  <Volume2 className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-gray-900">Voice Narration</h4>
                  <p className="text-[11px] text-gray-400">Female, Male or custom audio</p>
                </div>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={voiceEnabled}
                  onChange={(e) => setVoiceEnabled(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-9 h-5 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>

            {voiceEnabled && (
              <div className="space-y-4 pt-2 border-t border-gray-100">
                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-2">
                    Select Voice Narration Style
                  </label>
                  <div className="grid grid-cols-2 gap-2.5">
                    <button
                      type="button"
                      onClick={() => setSelectedVoice('en-US-JennyNeural')}
                      className={`p-3 rounded-xl border text-left transition-all cursor-pointer flex flex-col gap-1 ${
                        selectedVoice === 'en-US-JennyNeural'
                          ? 'border-pink-500 bg-pink-50/60 ring-2 ring-pink-100 shadow-xs'
                          : 'border-gray-200 bg-gray-50/70 hover:bg-gray-100'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-black text-gray-900 flex items-center gap-1.5">
                          <span className="w-2.5 h-2.5 rounded-full bg-pink-500 inline-block"></span>
                          Female Voice
                        </span>
                        {selectedVoice === 'en-US-JennyNeural' && (
                          <Check className="w-3.5 h-3.5 text-pink-600" />
                        )}
                      </div>
                      <span className="text-[10px] text-gray-500 font-semibold">Jenny • Warm & Natural</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => setSelectedVoice('en-US-GuyNeural')}
                      className={`p-3 rounded-xl border text-left transition-all cursor-pointer flex flex-col gap-1 ${
                        selectedVoice === 'en-US-GuyNeural'
                          ? 'border-blue-500 bg-blue-50/60 ring-2 ring-blue-100 shadow-xs'
                          : 'border-gray-200 bg-gray-50/70 hover:bg-gray-100'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-black text-gray-900 flex items-center gap-1.5">
                          <span className="w-2.5 h-2.5 rounded-full bg-blue-500 inline-block"></span>
                          Male Voice
                        </span>
                        {selectedVoice === 'en-US-GuyNeural' && (
                          <Check className="w-3.5 h-3.5 text-blue-600" />
                        )}
                      </div>
                      <span className="text-[10px] text-gray-500 font-semibold">Guy • Confident & Clear</span>
                    </button>
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between text-xs font-bold text-gray-700 mb-1">
                    <span>Voice Volume</span>
                    <span className="text-blue-600 font-black">{Math.round(narrationVolume * 100)}%</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="1.5"
                    step="0.05"
                    value={narrationVolume}
                    onChange={(e) => setNarrationVolume(parseFloat(e.target.value))}
                    className="w-full accent-blue-600 cursor-pointer"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1">
                    Or Upload Custom Voice Audio
                  </label>
                  <input
                    ref={audioInputRef}
                    type="file"
                    accept="audio/mp3,audio/wav,audio/m4a"
                    className="text-xs text-gray-500 file:mr-2 file:py-1 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer"
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        handleCustomAudioUpload(e.target.files[0]);
                      }
                    }}
                  />
                  {customAudioUrl && (
                    <div className="mt-2 text-[11px] font-bold text-emerald-600 flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Custom audio uploaded & linked
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Card: Subtitle & Typography Customization */}
          <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center">
                  <Type className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-gray-900">Subtitles & Captions</h4>
                  <p className="text-[11px] text-gray-400">SRT synchronization & styling</p>
                </div>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={subtitleEnabled}
                  onChange={(e) => setSubtitleEnabled(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-9 h-5 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-purple-600"></div>
              </label>
            </div>

            {subtitleEnabled && (
              <div className="space-y-3.5 pt-2 border-t border-gray-100">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-gray-700 mb-1">Font Family</label>
                    <select
                      value={subtitleFont}
                      onChange={(e) => setSubtitleFont(e.target.value)}
                      style={{
                        fontFamily: getSubtitleFontFamily(subtitleFont),
                        fontWeight: getSubtitleFontWeight(subtitleFont),
                      }}
                      className="w-full text-xs font-semibold bg-gray-50 border border-gray-200 rounded-lg p-2 focus:outline-none focus:ring-1 focus:ring-purple-500 cursor-pointer"
                    >
                      {SUBTITLE_FONTS.map(f => (
                        <option
                          key={f.id}
                          value={f.id}
                          style={{ fontFamily: f.family, fontWeight: f.weight }}
                        >
                          {f.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-gray-700 mb-1">Font Size</label>
                    <select
                      value={subtitleFontSize}
                      onChange={(e) => setSubtitleFontSize(e.target.value as any)}
                      className="w-full text-xs font-semibold bg-gray-50 border border-gray-200 rounded-lg p-2 focus:outline-none focus:ring-1 focus:ring-purple-500 cursor-pointer"
                    >
                      <option value="small">Small (28pt)</option>
                      <option value="medium">Medium (36pt)</option>
                      <option value="large">Large (48pt)</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1">Text Color</label>
                  <div className="flex items-center gap-2">
                    {SUBTITLE_COLOR_PRESETS.map(p => (
                      <button
                        key={p.color}
                        type="button"
                        onClick={() => setSubtitleColor(p.color)}
                        className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-bold border transition-all cursor-pointer ${
                          subtitleColor.toUpperCase() === p.color.toUpperCase()
                            ? 'border-purple-600 bg-purple-50 text-purple-700 ring-1 ring-purple-400'
                            : 'border-gray-200 bg-gray-50 text-gray-700 hover:bg-gray-100'
                        }`}
                      >
                        <span className="w-2.5 h-2.5 rounded-full border border-black/20" style={{ backgroundColor: p.color }}></span>
                        {p.label}
                      </button>
                    ))}
                    <input
                      type="color"
                      value={subtitleColor}
                      onChange={(e) => setSubtitleColor(e.target.value)}
                      title="Custom Color"
                      className="w-7 h-7 rounded border border-gray-200 cursor-pointer shrink-0"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-gray-700 mb-1">Position</label>
                    <div className="grid grid-cols-3 gap-1 bg-gray-50 p-1 rounded-lg border border-gray-200">
                      {(['top', 'center', 'bottom'] as const).map(pos => (
                        <button
                          key={pos}
                          type="button"
                          onClick={() => setSubtitlePosition(pos)}
                          className={`py-1.5 text-xs font-bold rounded-md transition-all cursor-pointer capitalize text-center ${
                            subtitlePosition === pos
                              ? 'bg-purple-600 text-white shadow-xs'
                              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-200/60'
                          }`}
                        >
                          {pos === 'top' ? 'Top' : pos === 'center' ? 'Center' : 'Bottom'}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-gray-700 mb-1">Background Capsule</label>
                    <select
                      value={subtitleBg}
                      onChange={(e) => setSubtitleBg(e.target.value as any)}
                      className="w-full text-xs font-semibold bg-gray-50 border border-gray-200 rounded-lg p-2 focus:outline-none focus:ring-1 focus:ring-purple-500 cursor-pointer"
                    >
                      <option value="translucent">Translucent Pill</option>
                      <option value="solid">Solid Dark Box</option>
                      <option value="none">No Box (Shadow Only)</option>
                    </select>
                  </div>
                </div>

                {/* Subtitle Live Canvas Screen Preview */}
                <div className="mt-3 space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-bold text-gray-600 uppercase tracking-wider flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-purple-500 animate-pulse"></span>
                      Sample Screen Preview
                    </span>
                    <span className="text-[10px] font-mono text-purple-700 bg-purple-50 border border-purple-100 px-2 py-0.5 rounded-full font-semibold">
                      {subtitleFont} • {subtitlePosition.toUpperCase()}
                    </span>
                  </div>

                  {/* Mock Video Canvas Frame */}
                  <div 
                    className="relative w-full h-44 rounded-xl border border-neutral-800 bg-neutral-950 overflow-hidden flex flex-col justify-between p-3 select-none shadow-inner transition-all duration-300"
                    style={{
                      backgroundImage: 'radial-gradient(ellipse at 50% 50%, rgba(30, 41, 59, 0.5) 0%, rgba(10, 10, 15, 0.98) 100%)',
                    }}
                  >
                    {/* Subtle cinematic backdrop glow */}
                    <div className="absolute inset-0 pointer-events-none opacity-20 flex items-center justify-center">
                      <div className="w-full h-full bg-gradient-to-tr from-blue-900/40 via-transparent to-purple-900/30"></div>
                    </div>

                    {/* Canvas Header Bar */}
                    <div className="flex items-center justify-between text-[10px] text-neutral-400 z-10 pointer-events-none">
                      <span className="bg-black/50 backdrop-blur-xs px-2 py-0.5 rounded text-[10px] border border-white/10 text-neutral-300 flex items-center gap-1.5 font-medium">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                        Video Canvas ({aspectRatio})
                      </span>
                      <span className="bg-black/50 backdrop-blur-xs px-2 py-0.5 rounded text-[10px] border border-white/10 text-neutral-300 font-mono">
                        Font: <span className="text-purple-300 font-bold">{subtitleFont}</span>
                      </span>
                    </div>

                    {/* Subtitle Positioning Container: accurately placed at Top, Center, or Bottom */}
                    <div
                      className={`w-full flex justify-center transition-all duration-300 ease-out z-10 ${
                        subtitlePosition === 'top'
                          ? 'mt-1 mb-auto'
                          : subtitlePosition === 'center'
                          ? 'my-auto'
                          : 'mt-auto mb-1'
                      }`}
                    >
                      <span
                        style={{
                          fontFamily: getSubtitleFontFamily(subtitleFont),
                          fontWeight: getSubtitleFontWeight(subtitleFont),
                          letterSpacing: getSubtitleLetterSpacing(subtitleFont),
                          color: subtitleColor,
                          fontSize: subtitleFontSize === 'small' ? '12px' : subtitleFontSize === 'large' ? '16px' : '14px',
                          textShadow: subtitleBg === 'none'
                            ? '0px 2px 4px rgba(0,0,0,0.95), 0px 0px 8px rgba(0,0,0,0.85)'
                            : '0px 1px 2px rgba(0,0,0,0.6)',
                        }}
                        className={`inline-block px-3.5 py-1.5 rounded-lg text-center max-w-[92%] transition-all duration-200 ${
                          subtitleBg === 'translucent'
                            ? 'bg-black/70 backdrop-blur-md border border-white/20 shadow-lg'
                            : subtitleBg === 'solid'
                            ? 'bg-neutral-950 border border-white/30 shadow-xl'
                            : ''
                        }`}
                      >
                        Sample Synchronized Subtitle Preview
                      </span>
                    </div>

                    {/* Canvas Footer Bar */}
                    <div className="flex items-center justify-between text-[10px] text-neutral-400 z-10 pointer-events-none">
                      <span className="text-[10px] text-neutral-400 font-mono">
                        Size: <span className="text-white font-medium">{subtitleFontSize.toUpperCase()}</span>
                      </span>
                      <span className="text-[10px] text-neutral-400 font-mono">
                        Position: <span className="text-purple-300 font-bold capitalize">{subtitlePosition}</span>
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Card: Recent Projects */}
          {recentProjects.length > 0 && (
            <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm space-y-3">
              <h4 className="text-sm font-bold text-gray-900">Recent Videos</h4>
              <div className="space-y-2">
                {recentProjects.slice(0, 5).map(proj => {
                  const projUrl = resolveMediaUrl(proj.video_url);
                  const isSelected = currentJob?.video_url === proj.video_url;

                  return (
                    <div
                      key={proj.id}
                      onClick={() => {
                        if (proj.video_url) {
                          setCurrentJob({
                            job_id: proj.id,
                            project_id: proj.id,
                            status: 'completed',
                            progress: 100,
                            current_step: 'Completed',
                            video_url: proj.video_url,
                          });
                          window.scrollTo({ top: 0, behavior: 'smooth' });
                        }
                      }}
                      className={`p-3 rounded-xl border transition-all cursor-pointer flex items-center justify-between ${
                        isSelected 
                          ? 'border-emerald-500 bg-emerald-50/60 shadow-xs' 
                          : 'border-gray-100 hover:bg-gray-50'
                      }`}
                    >
                      <div className="overflow-hidden pr-2 flex items-center gap-2.5">
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
                          isSelected ? 'bg-emerald-600 text-white' : 'bg-emerald-50 text-emerald-700'
                        }`}>
                          <Play className={`w-3.5 h-3.5 ${isSelected ? 'fill-white' : 'fill-emerald-700'}`} />
                        </div>
                        <div>
                          <div className="text-xs font-bold text-gray-800 truncate">{proj.title}</div>
                          <div className="text-[10px] text-gray-400">
                            {proj.duration ? `${Math.round(proj.duration)}s` : ''} • {proj.scenes_count} scenes • Click to play
                          </div>
                        </div>
                      </div>
                      {proj.video_url && (
                        <a
                          href={`http://localhost:8000/api/image-to-video/download/${proj.id}`}
                          download
                          onClick={e => e.stopPropagation()}
                          className="p-1.5 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors cursor-pointer"
                          title="Download MP4"
                        >
                          <Download className="w-4 h-4" />
                        </a>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Script & Narration Studio Modal (AI Generation & Custom User Script Facility) */}
      {showScriptModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-4 max-h-[90vh] flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-gray-100 pb-3">
              <div>
                <h3 className="text-lg font-black text-gray-900 flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-purple-600" />
                  Script & Narration Studio
                </h3>
                <p className="text-xs text-gray-500 mt-0.5">
                  Generate high-retention narration with AI or enter your own custom script.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setShowScriptModal(false)}
                className="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Mode Switch Tabs: AI Script vs Custom Script */}
            <div className="flex bg-gray-100 p-1 rounded-xl gap-1">
              <button
                type="button"
                onClick={() => setScriptModalTab('ai')}
                className={`flex-1 py-2 text-xs font-bold rounded-lg flex items-center justify-center gap-1.5 transition-all cursor-pointer ${
                  scriptModalTab === 'ai'
                    ? 'bg-white text-purple-700 shadow-xs'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <Sparkles className="w-3.5 h-3.5 text-purple-600" />
                ✨ AI Script Generator
              </button>
              <button
                type="button"
                onClick={() => setScriptModalTab('custom')}
                className={`flex-1 py-2 text-xs font-bold rounded-lg flex items-center justify-center gap-1.5 transition-all cursor-pointer ${
                  scriptModalTab === 'custom'
                    ? 'bg-white text-blue-700 shadow-xs'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <Type className="w-3.5 h-3.5 text-blue-600" />
                📝 Provide Custom Script
              </button>
            </div>

            {/* Tab 1: AI Script Generation */}
            {scriptModalTab === 'ai' && (
              <div className="space-y-4 overflow-y-auto pr-1 flex-1">
                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1">
                    Video Topic, Theme or Prompt
                  </label>
                  <input
                    type="text"
                    value={aiTopic}
                    onChange={(e) => setAiTopic(e.target.value)}
                    placeholder="e.g., Great Standing Buddha Statue - Peace, Wisdom and Compassion..."
                    className="w-full text-xs font-medium p-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-purple-500 focus:outline-none"
                  />
                  {getSuggestedTopic() && (
                    <div className="flex items-center gap-1.5 mt-1.5 text-[11px] text-gray-500">
                      <span>Suggested from uploaded images:</span>
                      <button
                        type="button"
                        onClick={() => setAiTopic(getSuggestedTopic())}
                        className="text-purple-600 font-bold hover:underline cursor-pointer"
                      >
                        "{getSuggestedTopic()}"
                      </button>
                    </div>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-gray-700 mb-1">
                      Narration Tone
                    </label>
                    <select
                      value={aiTone}
                      onChange={(e) => setAiTone(e.target.value)}
                      className="w-full text-xs font-semibold bg-gray-50 border border-gray-200 rounded-xl p-2.5 focus:outline-none focus:ring-2 focus:ring-purple-500 cursor-pointer"
                    >
                      <option value="Inspiring">Inspiring & Uplifting</option>
                      <option value="Educational">Educational & Informative</option>
                      <option value="Cinematic">Cinematic & Dramatic</option>
                      <option value="Storytelling">Storytelling & Narrative</option>
                      <option value="Promotional">Energetic & Promotional</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-gray-700 mb-1">
                      Scene Count
                    </label>
                    <div className="p-2.5 bg-gray-50 border border-gray-200 rounded-xl text-xs font-semibold text-gray-700 flex items-center justify-between">
                      <span>{scenes.length} Scenes</span>
                      <span className="text-[10px] text-purple-600 font-bold">~4s per scene</span>
                    </div>
                  </div>
                </div>

                <button
                  type="button"
                  disabled={isGeneratingScript || scenes.length === 0}
                  onClick={() => handleGenerateAiScript()}
                  className="w-full py-2.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-xl text-xs font-bold shadow-xs transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
                >
                  {isGeneratingScript ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      Generating narration script with AI...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4" />
                      {generatedAiScenes.length > 0 ? 'Regenerate Script with AI' : 'Generate Script with AI'}
                    </>
                  )}
                </button>

                {/* Generated Scenes Preview */}
                {generatedAiScenes.length > 0 && (
                  <div className="space-y-3 pt-2 border-t border-gray-100">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-black text-gray-800">
                        Generated Script Preview ({generatedAiScenes.length} scenes)
                      </span>
                      <span className="text-[10px] text-gray-500">
                        You can edit any line before applying
                      </span>
                    </div>

                    <div className="space-y-2.5 max-h-56 overflow-y-auto pr-1">
                      {generatedAiScenes.map((item, idx) => (
                        <div key={idx} className="p-3 bg-purple-50/50 rounded-xl border border-purple-100 space-y-1.5">
                          <div className="flex items-center justify-between">
                            <span className="text-[11px] font-black text-purple-900">
                              Scene {item.scene_index || idx + 1}: {item.headline || `Image ${idx + 1}`}
                            </span>
                          </div>
                          <textarea
                            value={item.text}
                            onChange={(e) => {
                              const updated = [...generatedAiScenes];
                              updated[idx] = { ...updated[idx], text: e.target.value };
                              setGeneratedAiScenes(updated);
                            }}
                            rows={2}
                            className="w-full text-xs font-medium p-2 bg-white border border-purple-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-purple-500 resize-none"
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Tab 2: Custom User Script */}
            {scriptModalTab === 'custom' && (
              <div className="space-y-3 overflow-y-auto pr-1 flex-1">
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="block text-xs font-bold text-gray-700">
                      Enter or Paste Your Script
                    </label>
                    <span className="text-[10px] font-semibold text-blue-600">
                      {bulkScript.split('\n').filter(l => l.trim()).length} lines entered for {scenes.length} scenes
                    </span>
                  </div>
                  <p className="text-[11px] text-gray-500 mb-2">
                    Write each scene narration on a new line or paragraph. Each line will automatically be distributed to your uploaded scenes in order.
                  </p>
                  <textarea
                    value={bulkScript}
                    onChange={(e) => setBulkScript(e.target.value)}
                    rows={8}
                    placeholder={`Image 1: Welcome to the beautiful sanctuary of peace.\nImage 2: Observe the calming presence and mindful posture.\nImage 3: Experience the timeless wisdom and serene journey.`}
                    className="w-full text-xs font-medium p-3 bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  />
                </div>
              </div>
            )}

            {/* Footer Buttons */}
            <div className="flex items-center justify-end gap-2 pt-3 border-t border-gray-100">
              <button
                type="button"
                onClick={() => setShowScriptModal(false)}
                className="px-4 py-2 border border-gray-200 text-gray-700 rounded-xl text-xs font-bold hover:bg-gray-50 cursor-pointer"
              >
                Cancel
              </button>
              {scriptModalTab === 'ai' ? (
                <button
                  type="button"
                  disabled={generatedAiScenes.length === 0}
                  onClick={applyGeneratedAiScript}
                  className="px-5 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-xl text-xs font-bold shadow-sm transition-all cursor-pointer disabled:opacity-40"
                >
                  Apply AI Script to Scenes
                </button>
              ) : (
                <button
                  type="button"
                  onClick={applyBulkScript}
                  disabled={!bulkScript.trim()}
                  className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold shadow-sm transition-all cursor-pointer disabled:opacity-40"
                >
                  Apply Custom Script to Scenes
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Scene Preview Modal */}
      {previewingScene && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-xl w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-black text-gray-900">Scene Motion Preview</h3>
                <p className="text-xs text-gray-500">
                  {previewingScene.motion_type === 'camera' 
                    ? `Camera Motion: ${previewingScene.camera_motion}` 
                    : `AI Motion: ${previewingScene.ai_motion} (${previewingScene.ai_intensity})`}
                </p>
              </div>
              <button
                onClick={() => {
                  setPreviewingScene(null);
                  setScenePreviewUrl(null);
                }}
                className="p-1 text-gray-400 hover:text-gray-600 rounded-lg cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="w-full bg-black rounded-xl overflow-hidden aspect-video flex items-center justify-center relative">
              {isPreviewLoading ? (
                <div className="flex flex-col items-center gap-2 text-white text-xs font-bold">
                  <RefreshCw className="w-6 h-6 animate-spin text-blue-400" />
                  <span>Rendering animated motion preview...</span>
                </div>
              ) : scenePreviewUrl ? (
                <video
                  key={scenePreviewUrl}
                  src={resolveMediaUrl(scenePreviewUrl)}
                  controls
                  autoPlay
                  loop
                  className="w-full h-full object-contain"
                />
              ) : (
                <img
                  src={resolveMediaUrl(previewingScene.image_url)}
                  alt="Scene"
                  className="w-full h-full object-cover"
                />
              )}

              {/* Subtitle Overlay in Scene Preview */}
              {subtitleEnabled && previewingScene.text && !isPreviewLoading && (
                <div
                  className={`absolute inset-x-0 px-4 pointer-events-none flex justify-center z-10 transition-all ${
                    subtitlePosition === 'top'
                      ? 'top-4'
                      : subtitlePosition === 'center'
                      ? 'top-1/2 -translate-y-1/2'
                      : 'bottom-4'
                  }`}
                >
                  <span
                    style={{
                      fontFamily: getSubtitleFontFamily(subtitleFont),
                      fontWeight: getSubtitleFontWeight(subtitleFont),
                      letterSpacing: getSubtitleLetterSpacing(subtitleFont),
                      color: subtitleColor,
                      fontSize: subtitleFontSize === 'small' ? '12px' : subtitleFontSize === 'large' ? '16px' : '14px',
                      textShadow: subtitleBg === 'none'
                        ? '0px 2px 4px rgba(0,0,0,0.95), 0px 0px 8px rgba(0,0,0,0.85)'
                        : '0px 1px 2px rgba(0,0,0,0.6)',
                    }}
                    className={`inline-block px-3 py-1.5 rounded-lg text-center max-w-[90%] shadow-lg ${
                      subtitleBg === 'translucent'
                        ? 'bg-black/70 backdrop-blur-md border border-white/20'
                        : subtitleBg === 'solid'
                        ? 'bg-neutral-950 border border-white/30'
                        : ''
                    }`}
                  >
                    {previewingScene.text}
                  </span>
                </div>
              )}
            </div>

            <p className="text-xs text-gray-600 font-medium italic text-center">
              "{previewingScene.text}"
            </p>

            <div className="flex justify-end">
              <button
                onClick={() => {
                  setPreviewingScene(null);
                  setScenePreviewUrl(null);
                }}
                className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-800 rounded-xl text-xs font-bold cursor-pointer"
              >
                Close Preview
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
