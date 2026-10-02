const API_BASE = '/api';

export const api = {
  async getHealth() {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error('Health check failed');
    return res.json();
  },

  async createProject(data) {
    const res = await fetch(`${API_BASE}/projects`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to create project');
    }
    return res.json();
  },

  async generateProject(projectId) {
    const res = await fetch(`${API_BASE}/projects/${projectId}/generate`, {
      method: 'POST',
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to trigger video generation');
    }
    return res.json();
  },

  async getProject(projectId) {
    const res = await fetch(`${API_BASE}/projects/${projectId}`);
    if (!res.ok) throw new Error('Failed to fetch project');
    return res.json();
  },

  async getProjectStatus(projectId) {
    const res = await fetch(`${API_BASE}/projects/${projectId}/status`);
    if (!res.ok) throw new Error('Failed to fetch project status');
    return res.json();
  },

  async listProjects() {
    const res = await fetch(`${API_BASE}/projects`);
    if (!res.ok) throw new Error('Failed to list projects');
    return res.json();
  },

  async publishProject(projectId) {
    const res = await fetch(`${API_BASE}/projects/${projectId}/publish`, {
      method: 'POST',
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to publish project');
    }
    return res.json();
  },

  getVideoUrl(projectId) {
    return `${API_BASE}/projects/${projectId}/video`;
  }
};
