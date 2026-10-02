import React, { useState, useEffect, useRef } from 'react';
import Header from './components/Header';
import Dashboard from './pages/Dashboard';
import ProjectsHistory from './pages/ProjectsHistory';
import PublishModal from './components/PublishModal';
import { api } from './services/api';

export default function App() {
  const [currentTab, setCurrentTab] = useState('dashboard');
  const [projects, setProjects] = useState([]);
  const [currentProject, setCurrentProject] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isPublishing, setIsPublishing] = useState(false);
  const [publishModalOpen, setPublishModalOpen] = useState(false);
  const [publishData, setPublishData] = useState(null);
  const [health, setHealth] = useState(null);
  const pollingRef = useRef(null);

  // Initial load: Fetch health and list projects
  useEffect(() => {
    loadHealth();
    loadProjects();
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, []);

  const loadHealth = async () => {
    try {
      const data = await api.getHealth();
      setHealth(data);
    } catch (e) {
      console.warn('Backend health check error:', e);
    }
  };

  const loadProjects = async () => {
    try {
      const list = await api.listProjects();
      setProjects(list);
      // If we don't have a current project yet, take the newest one
      if (list.length > 0 && !currentProject) {
        setCurrentProject(list[0]);
      }
    } catch (e) {
      console.warn('Failed to load projects list:', e);
    }
  };

  // Poll project status while processing
  useEffect(() => {
    if (pollingRef.current) clearInterval(pollingRef.current);

    if (currentProject && (currentProject.status === 'processing' || currentProject.status === 'created')) {
      pollingRef.current = setInterval(async () => {
        try {
          const updated = await api.getProject(currentProject.id);
          setCurrentProject(updated);

          if (updated.status === 'ready' || updated.status === 'failed' || updated.status === 'published') {
            setIsGenerating(false);
            clearInterval(pollingRef.current);
            loadProjects();
          }
        } catch (err) {
          console.error('Polling error:', err);
        }
      }, 1500);
    } else {
      setIsGenerating(false);
    }

    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [currentProject?.id, currentProject?.status]);

  // Handle generation start
  const handleGenerate = async (formData) => {
    setIsGenerating(true);
    try {
      // 1. Create project in DB
      const newProj = await api.createProject(formData);
      setCurrentProject(newProj);
      setCurrentTab('dashboard');

      // 2. Trigger pipeline execution
      await api.generateProject(newProj.id);

      // Refresh listing
      loadProjects();
    } catch (err) {
      console.error('Generation trigger failed:', err);
      setIsGenerating(false);
      alert(`Generation failed: ${err.message}`);
    }
  };

  // Handle regeneration
  const handleRegenerate = async () => {
    if (!currentProject) return;
    setIsGenerating(true);
    try {
      await api.generateProject(currentProject.id);
      const refreshed = await api.getProject(currentProject.id);
      setCurrentProject(refreshed);
    } catch (err) {
      console.error('Regenerate failed:', err);
      setIsGenerating(false);
    }
  };

  // Handle publish simulation
  const handlePublish = async () => {
    if (!currentProject) return;
    setIsPublishing(true);
    try {
      const pubRes = await api.publishProject(currentProject.id);
      setPublishData(pubRes);
      setPublishModalOpen(true);
      // Update local project status
      setCurrentProject(prev => prev ? { ...prev, status: 'published' } : prev);
      loadProjects();
    } catch (err) {
      alert(`Publishing failed: ${err.message}`);
    } finally {
      setIsPublishing(false);
    }
  };

  const stats = {
    total: projects.length,
    published: projects.filter(p => p.status === 'published').length,
    processing: projects.filter(p => p.status === 'processing').length,
  };

  return (
    <div className="min-h-screen bg-background text-text-primary flex flex-col font-sans">
      <Header
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        projectCount={projects.length}
        health={health}
      />

      <main className="flex-1 w-full mx-auto px-6 lg:px-10 pt-6">
        {currentTab === 'projects' ? (
          <ProjectsHistory
            projects={projects}
            onSelectProject={(proj) => {
              setCurrentProject(proj);
              setCurrentTab('dashboard');
            }}
            onPublishProject={handlePublish}
          />
        ) : (
          <Dashboard
            currentProject={currentProject}
            onGenerate={handleGenerate}
            isGenerating={isGenerating}
            onRegenerate={handleRegenerate}
            onPublish={handlePublish}
            isPublishing={isPublishing}
            stats={stats}
          />
        )}
      </main>

      {/* Publish Simulation Modal */}
      <PublishModal
        isOpen={publishModalOpen}
        onClose={() => setPublishModalOpen(false)}
        publishData={publishData}
        project={currentProject}
      />
    </div>
  );
}
