import React, { useState } from 'react';
import { Wand2, LayoutTemplate, MonitorPlay, Clock, Mic2, Loader2 } from 'lucide-react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const API_URL = 'http://localhost:8000/api';

export default function CreateVideo() {
  const navigate = useNavigate();
  const [topic, setTopic] = useState('');
  const [platform, setPlatform] = useState('YouTube Shorts');
  const [audience, setAudience] = useState('General Audience');
  const [goal, setGoal] = useState('Educate');
  const [aspectRatio, setAspectRatio] = useState('9:16');
  const [duration, setDuration] = useState('60 sec');
  const [tone, setTone] = useState('Educational');
  const [language, setLanguage] = useState('English');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleGenerate = async () => {
    if (!topic.trim()) {
      setError('Please enter a topic first.');
      return;
    }
    setError('');
    setIsLoading(true);
    try {
      // 1. Create project
      const projectRes = await axios.post(`${API_URL}/projects/`, {
        topic,
        audience,
        goal,
        platform,
        aspect_ratio: aspectRatio,
        duration: parseInt(duration),
        tone,
        language
      });
      
      const projectId = projectRes.data.id;
      
      // 2. Call AI Director
      await axios.post(`${API_URL}/projects/${projectId}/director`);
      
      // Navigate directly to the project details and storyboard review page
      navigate(`/projects/${projectId}`);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'An error occurred during generation.');
    } finally {
      setIsLoading(false);
    }
  }
  
  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="mb-10">
        <h2 className="text-3xl font-extrabold text-gray-900 mb-2">Create New Video</h2>
        <p className="text-gray-500">Tell us what you want to create, and the AI Director will handle the rest.</p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-600 rounded-xl">
          {error}
        </div>
      )}

      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden mb-8">
        <div className="bg-gray-50 px-6 py-4 border-b border-gray-200 flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold">1</div>
          <h3 className="text-lg font-bold text-gray-900">The Idea</h3>
        </div>
        
        <div className="p-6">
          <div className="mb-6">
            <div className="flex justify-between items-center mb-2">
              <label className="block text-sm font-semibold text-gray-700">What do you want to create a video about?</label>
              <span className="text-xs text-blue-600 font-medium">Click any topic below to auto-fill</span>
            </div>
            <textarea 
              rows={4}
              className="w-full rounded-xl border border-gray-300 px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all resize-none shadow-sm text-gray-800"
              placeholder="e.g. How to brew authentic espresso at home, Why the Roman Empire collapsed, 5 Daily habits of high-performing leaders..."
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
            />
            {/* Topic Inspiration Chips */}
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <span className="text-xs text-gray-400 font-semibold mr-1">Trending ideas:</span>
              {[
                '☕ How to Brew Authentic Espresso at Home',
                '🏛️ Why the Roman Empire Really Collapsed',
                '🌱 Photosynthesis: The Hidden Science of Plants',
                '💻 Quantum Computing Explained Simply',
                '🧘 5 Morning Habits for High Productivity'
              ].map((chip, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setTopic(chip.replace(/^[\uD800-\uDBFF\uDC00-\uDFFF\s]+/, '').trim())}
                  className="text-xs px-3 py-1.5 bg-gray-50 hover:bg-blue-50 hover:text-blue-700 hover:border-blue-300 text-gray-600 border border-gray-200 rounded-lg transition-colors font-medium">
                  {chip}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Audience</label>
              <select 
                value={audience} onChange={e => setAudience(e.target.value)}
                className="w-full rounded-xl border border-gray-300 px-4 py-3 bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none shadow-sm">
                <option>General Audience</option>
                <option>Students</option>
                <option>Professionals</option>
                <option>Developers</option>
                <option>Business Owners</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Goal</label>
              <select 
                value={goal} onChange={e => setGoal(e.target.value)}
                className="w-full rounded-xl border border-gray-300 px-4 py-3 bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none shadow-sm">
                <option>Educate</option>
                <option>Explain</option>
                <option>Entertain</option>
                <option>Promote</option>
                <option>Inspire</option>
                <option>Convert</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden mb-8">
        <div className="bg-gray-50 px-6 py-4 border-b border-gray-200 flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold">2</div>
          <h3 className="text-lg font-bold text-gray-900">Format & Style</h3>
        </div>
        
        <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-6">
          <div>
            <label className="flex items-center gap-2 text-sm font-semibold text-gray-700 mb-3">
              <MonitorPlay className="w-4 h-4 text-gray-400" /> Platform
            </label>
            <div className="grid grid-cols-2 gap-3">
              {['YouTube', 'YouTube Shorts', 'Instagram Reels', 'TikTok', 'LinkedIn'].map(p => (
                <button 
                  key={p}
                  type="button"
                  onClick={() => {
                    setPlatform(p);
                    if (p === 'YouTube') {
                      setAspectRatio('16:9');
                    } else if (p === 'YouTube Shorts' || p === 'Instagram Reels' || p === 'TikTok') {
                      setAspectRatio('9:16');
                    }
                  }}
                  className={`px-3 py-2 rounded-lg border text-sm font-medium transition-colors ${platform === p ? 'bg-blue-50 border-blue-600 text-blue-700 font-semibold shadow-sm' : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'}`}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="flex items-center gap-2 text-sm font-semibold text-gray-700 mb-3">
              <LayoutTemplate className="w-4 h-4 text-gray-400" /> Aspect Ratio
            </label>
            <div className="flex gap-3">
              {['16:9', '9:16', '1:1', '4:5'].map(r => (
                <button 
                  key={r} 
                  type="button"
                  onClick={() => setAspectRatio(r)}
                  className={`px-4 py-2 rounded-lg border text-sm font-medium transition-colors ${aspectRatio === r ? 'bg-blue-50 border-blue-600 text-blue-700 font-semibold' : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'}`}>
                  {r}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="flex items-center gap-2 text-sm font-semibold text-gray-700 mb-3">
              <Clock className="w-4 h-4 text-gray-400" /> Target Duration
            </label>
            <select 
              value={duration} onChange={e => setDuration(e.target.value)}
              className="w-full rounded-xl border border-gray-300 px-4 py-3 bg-white focus:ring-2 focus:ring-blue-500 outline-none shadow-sm">
              <option>30 sec</option>
              <option>60 sec</option>
              <option>90 sec</option>
              <option>2 min</option>
              <option>3 min</option>
            </select>
          </div>

          <div>
            <label className="flex items-center gap-2 text-sm font-semibold text-gray-700 mb-3">
              <Mic2 className="w-4 h-4 text-gray-400" /> Tone
            </label>
            <select 
              value={tone} onChange={e => setTone(e.target.value)}
              className="w-full rounded-xl border border-gray-300 px-4 py-3 bg-white focus:ring-2 focus:ring-blue-500 outline-none shadow-sm">
              <option>Professional</option>
              <option>Educational</option>
              <option>Energetic</option>
              <option>Cinematic</option>
              <option>Casual</option>
            </select>
          </div>
        </div>
      </div>

      <div className="flex justify-end">
        <button 
          onClick={handleGenerate}
          disabled={isLoading}
          className="flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white font-bold rounded-xl shadow-lg shadow-orange-200 transition-all transform hover:scale-105 disabled:opacity-50 disabled:hover:scale-100 disabled:cursor-not-allowed">
          {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Wand2 className="w-5 h-5" />}
          {isLoading ? 'Generating Strategy...' : 'Generate AI Video Strategy'}
        </button>
      </div>
    </div>
  );
}
