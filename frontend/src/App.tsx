import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Home, Video, Folder, Image, Layout, Settings, Sparkles } from 'lucide-react';
import React from 'react';

import Dashboard from './pages/Dashboard';
import CreateVideo from './pages/CreateVideo';
import Projects from './pages/Projects';
import ProjectDetails from './pages/ProjectDetails';
import Assets from './pages/Assets';
import Templates from './pages/Templates';

function SidebarLink({ to, icon: Icon, label }: { to: string, icon: any, label: string }) {
  const location = useLocation();
  const isActive = location.pathname === to || (to !== '/' && location.pathname.startsWith(to));
  
  return (
    <Link 
      to={to} 
      className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 font-medium ${
        isActive 
        ? 'bg-blue-600 text-white shadow-md shadow-blue-200' 
        : 'text-gray-500 hover:text-blue-600 hover:bg-blue-50'
      }`}
    >
      <Icon className="w-5 h-5" />
      <span>{label}</span>
    </Link>
  );
}

function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen bg-gray-50/50">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-100 flex flex-col shadow-sm z-10">
        <div className="p-6">
          <Link to="/" className="flex items-center gap-2 group">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-orange-500 rounded-xl flex items-center justify-center shadow-lg group-hover:scale-105 transition-transform">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-extrabold text-gray-900 tracking-tight leading-none">AI Video</h1>
              <p className="text-xs font-bold text-gray-400 uppercase tracking-wider">Studio</p>
            </div>
          </Link>
        </div>
        
        <nav className="flex-1 px-4 py-4 space-y-1">
          <SidebarLink to="/" icon={Home} label="Dashboard" />
          <SidebarLink to="/create" icon={Video} label="Create Video" />
          <SidebarLink to="/projects" icon={Folder} label="Projects" />
          <SidebarLink to="/assets" icon={Image} label="Assets" />
          <SidebarLink to="/templates" icon={Layout} label="Templates" />
        </nav>
        
        <div className="p-4 border-t border-gray-100">
          <SidebarLink to="/settings" icon={Settings} label="Settings" />
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-blue-50/30 via-gray-50/50 to-gray-50/50">
        {children}
      </main>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <DashboardLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/create" element={<CreateVideo />} />
          <Route path="/projects" element={<Projects />} />
          <Route path="/projects/:id" element={<ProjectDetails />} />
          <Route path="/assets" element={<Assets />} />
          <Route path="/templates" element={<Templates />} />
          <Route path="/settings" element={<div className="p-8"><h2 className="text-2xl font-bold">Settings</h2></div>} />
        </Routes>
      </DashboardLayout>
    </BrowserRouter>
  );
}

export default App;
