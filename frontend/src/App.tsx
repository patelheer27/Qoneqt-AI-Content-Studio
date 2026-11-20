import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { 
  Home, Video, Folder, Image, Layout, Settings, Sparkles, 
  ShieldCheck, LogOut, CheckCircle2, RefreshCw 
} from 'lucide-react';
import React from 'react';

import Dashboard from './pages/Dashboard';
import CreateVideo from './pages/CreateVideo';
import Projects from './pages/Projects';
import ProjectDetails from './pages/ProjectDetails';
import Assets from './pages/Assets';
import Templates from './pages/Templates';
import SecurityCenter from './pages/SecurityCenter';
import Login from './pages/Login';
import { AuthProvider, useAuth } from './context/AuthContext';

function SidebarLink({ to, icon: Icon, label, badge }: { to: string; icon: any; label: string; badge?: string }) {
  const location = useLocation();
  const isActive = location.pathname === to || (to !== '/' && location.pathname.startsWith(to));
  
  return (
    <Link 
      to={to} 
      className={`flex items-center justify-between px-3.5 py-2.5 rounded-xl transition-all duration-150 text-sm font-medium ${
        isActive 
        ? 'bg-indigo-600 text-white shadow-xs font-semibold' 
        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/70'
      }`}
    >
      <div className="flex items-center gap-3">
        <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-white' : 'text-slate-400 group-hover:text-slate-600'}`} />
        <span>{label}</span>
      </div>
      {badge && (
        <span className={`text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded-md ${
          isActive 
            ? 'bg-white/20 text-white' 
            : 'bg-orange-50 text-orange-600 border border-orange-200/70'
        }`}>
          {badge}
        </span>
      )}
    </Link>
  );
}

function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();

  return (
    <div className="flex h-screen bg-slate-50 text-slate-900 antialiased font-sans overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-slate-200/80 flex flex-col z-20 shrink-0">
        <div className="p-5 pb-3">
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-9 h-9 bg-gradient-to-tr from-indigo-600 via-indigo-500 to-orange-500 rounded-xl flex items-center justify-center shadow-md shadow-indigo-500/20 group-hover:scale-105 transition-transform shrink-0">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-base font-extrabold text-slate-900 tracking-tight leading-none">Qoneqt AI</h1>
              <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mt-0.5">Content Studio</p>
            </div>
          </Link>
          <div className="mt-3 flex items-center gap-1.5 text-[11px] font-medium text-slate-500">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>Studio Engine v2.4</span>
          </div>
        </div>
        
        <nav className="flex-1 px-3 py-2 space-y-1 overflow-y-auto">
          <SidebarLink to="/" icon={Home} label="Dashboard" />
          <SidebarLink to="/create" icon={Video} label="Create Video" />
          <SidebarLink to="/projects" icon={Folder} label="Projects" />
          <SidebarLink to="/assets" icon={Image} label="Image-to-Video" />
          <SidebarLink to="/templates" icon={Layout} label="Templates" />
          
          <div className="pt-4 pb-1.5">
            <div className="px-3 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
              Security & Privacy
            </div>
          </div>
          <SidebarLink to="/security" icon={ShieldCheck} label="Security Center" badge="Verified" />
        </nav>
        
        {/* User Account & Logout Footer */}
        <div className="p-3 border-t border-slate-100 space-y-1.5">
          {user && (
            <div className="p-2.5 bg-slate-50/80 rounded-xl border border-slate-200/60 flex items-center justify-between">
              <div className="overflow-hidden pr-2">
                <div className="text-xs font-semibold text-slate-800 truncate">{user.email}</div>
                <div className="text-[10px] text-emerald-600 font-medium flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> Authenticated
                </div>
              </div>
              <button
                onClick={logout}
                title="Log Out"
                className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors cursor-pointer"
              >
                <LogOut className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
          <SidebarLink to="/settings" icon={Settings} label="Settings" />
        </div>
      </aside>

      {/* Main Content with soft aesthetic ambient backdrop */}
      <main 
        className="flex-1 overflow-auto bg-slate-50 relative"
        style={{
          backgroundImage: 'radial-gradient(ellipse 90% 50% at 50% -10%, rgba(99, 102, 241, 0.04) 0%, rgba(248, 250, 252, 0) 70%)'
        }}
      >
        {children}
      </main>
    </div>
  );
}

function MainContent() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="h-screen w-screen flex flex-col items-center justify-center bg-gray-50 gap-3">
        <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-orange-500 rounded-2xl flex items-center justify-center shadow-lg animate-pulse">
          <Sparkles className="w-6 h-6 text-white" />
        </div>
        <div className="flex items-center gap-2 text-xs font-bold text-gray-500">
          <RefreshCw className="w-4 h-4 animate-spin text-blue-600" />
          <span>Validating Qoneqt Session...</span>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Login />;
  }

  return (
    <DashboardLayout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/create" element={<CreateVideo />} />
        <Route path="/projects" element={<Projects />} />
        <Route path="/projects/:id" element={<ProjectDetails />} />
        <Route path="/assets" element={<Assets />} />
        <Route path="/image-to-video" element={<Assets />} />
        <Route path="/templates" element={<Templates />} />
        <Route path="/security" element={<SecurityCenter />} />
        <Route path="/settings" element={<div className="p-8"><h2 className="text-2xl font-bold">Settings</h2></div>} />
      </Routes>
    </DashboardLayout>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <MainContent />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
