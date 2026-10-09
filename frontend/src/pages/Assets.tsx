import React from 'react';
import { Image, Upload, Search, Film, Music, Mic } from 'lucide-react';

export default function Assets() {
  return (
    <div className="p-8 max-w-7xl mx-auto h-full flex flex-col">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-3xl font-extrabold text-gray-900 mb-2">Assets Library</h2>
          <p className="text-gray-500">Manage your images, videos, audio, and generated media.</p>
        </div>
        <button className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl shadow-md transition-all">
          <Upload className="w-5 h-5" />
          Upload Asset
        </button>
      </div>

      <div className="flex gap-4 border-b border-gray-200 mb-6">
        <button className="px-4 py-2 border-b-2 border-blue-600 text-blue-600 font-medium">All Assets</button>
        <button className="px-4 py-2 border-b-2 border-transparent text-gray-500 hover:text-gray-700 font-medium flex items-center gap-2"><Image className="w-4 h-4"/> Images</button>
        <button className="px-4 py-2 border-b-2 border-transparent text-gray-500 hover:text-gray-700 font-medium flex items-center gap-2"><Film className="w-4 h-4"/> Videos</button>
        <button className="px-4 py-2 border-b-2 border-transparent text-gray-500 hover:text-gray-700 font-medium flex items-center gap-2"><Music className="w-4 h-4"/> Audio</button>
        <button className="px-4 py-2 border-b-2 border-transparent text-gray-500 hover:text-gray-700 font-medium flex items-center gap-2"><Mic className="w-4 h-4"/> Voiceovers</button>
      </div>

      <div className="flex-1 flex flex-col items-center justify-center text-center text-gray-500 mt-4 bg-gray-50 rounded-2xl border border-dashed border-gray-300 p-12">
        <Upload className="w-16 h-16 text-gray-300 mb-4" />
        <h3 className="text-xl font-bold text-gray-900 mb-2">Your library is empty</h3>
        <p className="mb-6 max-w-md">Upload your own media or let the AI Director generate visuals and audio for you.</p>
      </div>
    </div>
  );
}
