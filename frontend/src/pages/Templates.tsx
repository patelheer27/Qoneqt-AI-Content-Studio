import React from 'react';
import { Layout, Star, Plus } from 'lucide-react';

export default function Templates() {
  const templates = [
    { title: 'Educational', tag: 'YouTube', color: 'bg-blue-100 text-blue-600', icon: Layout },
    { title: 'News Style', tag: 'TikTok', color: 'bg-red-100 text-red-600', icon: Layout },
    { title: 'Product Showcase', tag: 'Instagram', color: 'bg-purple-100 text-purple-600', icon: Layout },
    { title: 'Explainer Video', tag: 'LinkedIn', color: 'bg-teal-100 text-teal-600', icon: Layout },
  ];

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-3xl font-extrabold text-gray-900 mb-2">Templates</h2>
          <p className="text-gray-500">Jumpstart your video creation with pre-built styles.</p>
        </div>
        <button className="flex items-center gap-2 px-6 py-3 bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 font-semibold rounded-xl shadow-sm transition-all">
          <Plus className="w-5 h-5" />
          New Template
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {templates.map((tpl, i) => (
          <div key={i} className="bg-white rounded-2xl border border-gray-200 overflow-hidden shadow-sm hover:shadow-lg transition-all group cursor-pointer">
            <div className={`h-40 ${tpl.color} flex flex-col items-center justify-center opacity-80 group-hover:opacity-100 transition-opacity relative`}>
              <tpl.icon className="w-12 h-12 mb-2 opacity-50" />
              <div className="absolute top-3 right-3 bg-white/50 backdrop-blur text-xs font-bold px-2 py-1 rounded text-gray-900">
                {tpl.tag}
              </div>
            </div>
            <div className="p-5">
              <h3 className="font-bold text-gray-900 text-lg mb-1">{tpl.title}</h3>
              <p className="text-sm text-gray-500 mb-4">Optimized for high engagement</p>
              <button className="w-full py-2 bg-gray-50 hover:bg-blue-50 text-blue-600 font-semibold rounded-lg text-sm transition-colors">
                Use Template
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
