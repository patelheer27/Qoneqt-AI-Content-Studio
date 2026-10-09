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
      className={`flex items-center justify-between px-4 py-3 rounded-xl transition-all duration-200 font-medium ${
        isActive 
        ? 'bg-blue-600 text-white shadow-md shadow-blue-200' 
        : 'text-gray-500 hover:text-blue-600 hover:bg-blue-50'
      }`}
    >
      <div className="flex items-center gap-3">
        <Icon className="w-5 h-5 shrink-0" />
        <span className="text-sm">{label}</span>
      </div>
      {badge && (
        <span className={`text-[10px] font-extrabold uppercase px-1.5 py-0.5 rounded ${
          isActive ? 'bg-white/20 text-white' : 'bg-blue-100 text-blue-700'
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
    <div className="flex h-screen bg-gray-50/50">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-100 flex flex-col shadow-sm z-10">
        <div className="p-6 pb-4">
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-orange-500 rounded-xl flex items-center justify-center shadow-lg group-hover:scale-105 transition-transform shrink-0">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-black text-gray-900 tracking-tight leading-none">Qoneqt AI</h1>
              <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mt-0.5">Content Studio</p>
            </div>
          </Link>
          <p className="text-[10px] font-semibold text-blue-600/80 mt-2 tracking-tight">
            From One Idea to a Publish-Ready Video.
          </p>
        </div>
        
        <nav className="flex-1 px-4 py-2 space-y-1 overflow-y-auto">
          <SidebarLink to="/" icon={Home} label="Dashboard" />
          <SidebarLink to="/create" icon={Video} label="Create Video" />
          <SidebarLink to="/projects" icon={Folder} label="Projects" />
          <SidebarLink to="/assets" icon={Image} label="Assets" />
          <SidebarLink to="/templates" icon={Layout} label="Templates" />
          
          <div className="pt-3 pb-1">
            <div className="px-4 text-[10px] font-extrabold text-gray-400 uppercase tracking-wider">
              Security & Privacy
            </div>
          </div>
          <SidebarLink to="/security" icon={ShieldCheck} label="Security Center" badge="New" />
        </nav>
        
        {/* User Account & Logout Footer */}
        <div className="p-4 border-t border-gray-100 space-y-2">
          {user && (
            <div className="p-2.5 bg-gray-50 rounded-xl border border-gray-100 flex items-center justify-between">
              <div className="overflow-hidden pr-2">
                <div className="text-xs font-bold text-gray-900 truncate">{user.email}</div>
                <div className="text-[10px] text-emerald-600 font-semibold flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> Verified OTP
                </div>
              </div>
              <button
                onClick={logout}
                title="Log Out"
                className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors cursor-pointer"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          )}
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
