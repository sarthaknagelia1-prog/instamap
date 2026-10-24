import React, { useState } from 'react';
import { api } from '../../api/client';
import {
  Lock,
  User,
  Building2,
  Key,
  ShieldCheck,
  Sparkles,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  Eye,
  EyeOff,
  Zap,
  RefreshCw
} from 'lucide-react';

export default function LoginView({ onLoginSuccess, showToast }) {
  const [username, setUsername] = useState('creator_sarthak');
  const [workspaceId, setWorkspaceId] = useState('default');
  const [apiKey, setApiKey] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  // Quick Preset Profiles for seamless multi-tenant testing
  const demoProfiles = [
    {
      title: 'Local Developer Pass',
      username: 'creator_sarthak',
      workspaceId: 'default',
      apiKey: '',
      role: 'Admin',
      badge: 'Quick Pass',
      desc: 'Default offline workspace with full creator management access.',
      color: 'border-indigo-200 hover:border-indigo-500 bg-indigo-50/40',
    },
    {
      title: 'Agency Master Admin',
      username: 'admin-1',
      workspaceId: 'system-admin',
      apiKey: 'test-admin-key',
      role: 'Master Admin',
      badge: 'Superuser',
      desc: 'Full visibility across all tenant workspaces and approval queues.',
      color: 'border-purple-200 hover:border-purple-500 bg-purple-50/40',
    },
    {
      title: 'Creator Studio Alpha',
      username: 'user-alpha',
      workspaceId: 'ws-alpha',
      apiKey: 'key-tenant-alpha',
      role: 'Creator Member',
      badge: 'Isolated Tenant',
      desc: 'Tenant-scoped workspace with protected analytics & drafts.',
      color: 'border-emerald-200 hover:border-emerald-500 bg-emerald-50/40',
    },
    {
      title: 'Growth Agency Beta',
      username: 'user-beta',
      workspaceId: 'ws-beta',
      apiKey: 'key-tenant-beta',
      role: 'Growth Strategist',
      badge: 'Isolated Tenant',
      desc: 'Client management environment with isolated datasets.',
      color: 'border-blue-200 hover:border-blue-500 bg-blue-50/40',
    },
  ];

  const handleLogin = async (e, customPayload = null) => {
    if (e) e.preventDefault();
    setErrorMsg('');
    setIsLoading(true);

    const payload = customPayload || {
      username: username.trim(),
      workspace_id: workspaceId.trim() || 'default',
      api_key: apiKey.trim() || undefined,
    };

    try {
      const res = await api.login(payload);
      // Persist credentials to localStorage
      if (res.access_token) {
        localStorage.setItem('instamap_token', res.access_token);
        localStorage.setItem('instamap_api_key', res.access_token);
      }
      localStorage.setItem('instamap_user', JSON.stringify(res));

      if (showToast) showToast(`Welcome back, ${res.user_id}! (${res.role})`, 'success');
      onLoginSuccess(res);
    } catch (err) {
      setErrorMsg(err.message || 'Authentication failed. Please verify credentials.');
      if (showToast) showToast(err.message, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectPreset = (profile) => {
    setUsername(profile.username);
    setWorkspaceId(profile.workspaceId);
    setApiKey(profile.apiKey);
    handleLogin(null, {
      username: profile.username,
      workspace_id: profile.workspaceId,
      api_key: profile.apiKey || undefined,
    });
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8 selection:bg-indigo-500 selection:text-white">
      {/* Brand Header */}
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-indigo-600 text-white font-black text-2xl shadow-md shadow-indigo-200 mb-3">
          ⚡
        </div>
        <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">
          InstaMap Engine
        </h2>
        <p className="mt-1.5 text-xs text-slate-500 font-medium">
          Autonomous Creator Intelligence & Multi-Tenant Growth Platform
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-xl">
        <div className="bg-white py-8 px-6 shadow-sm border border-slate-200 rounded-2xl sm:px-10 space-y-6">
          {/* Error Banner */}
          {errorMsg && (
            <div className="bg-rose-50 border border-rose-200 text-rose-700 px-4 py-3 rounded-xl text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Preset Profiles Picker */}
          <div>
            <div className="flex items-center justify-between mb-2.5">
              <span className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                <Zap className="w-3.5 h-3.5 text-indigo-600" />
                Quick 1-Click Workspace Profiles
              </span>
              <span className="text-[10px] text-slate-400 font-medium">Select a demo role</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {demoProfiles.map((p, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleSelectPreset(p)}
                  disabled={isLoading}
                  className={`p-3 text-left border rounded-xl transition-all duration-150 flex flex-col justify-between cursor-pointer ${p.color}`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-900">{p.title}</span>
                    <span className="text-[9px] font-black uppercase tracking-wider bg-white/90 px-1.5 py-0.5 rounded border border-slate-200">
                      {p.badge}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-600 mt-1 line-clamp-2">{p.desc}</p>
                  <div className="mt-2 text-[10px] text-indigo-700 font-mono font-bold flex items-center justify-between">
                    <span>ws: {p.workspaceId}</span>
                    <ArrowRight className="w-3 h-3" />
                  </div>
                </button>
              ))}
            </div>
          </div>

          <div className="relative flex py-2 items-center">
            <div className="flex-grow border-t border-slate-200"></div>
            <span className="flex-shrink mx-4 text-[11px] font-bold uppercase tracking-wider text-slate-400">
              Or Custom Sign In
            </span>
            <div className="flex-grow border-t border-slate-200"></div>
          </div>

          {/* Custom Sign-In Form */}
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Username / Creator Handle *
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <User className="w-4 h-4" />
                </div>
                <input
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="e.g. creator_sarthak or admin"
                  className="w-full text-xs pl-9 pr-3 py-2.5 bg-slate-50 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-indigo-500 font-mono"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Workspace ID <span className="text-slate-400 font-normal">(Tenant Scope)</span>
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <Building2 className="w-4 h-4" />
                </div>
                <input
                  type="text"
                  value={workspaceId}
                  onChange={(e) => setWorkspaceId(e.target.value)}
                  placeholder="default"
                  className="w-full text-xs pl-9 pr-3 py-2.5 bg-slate-50 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-indigo-500 font-mono"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Secret Token / API Key <span className="text-slate-400 font-normal">(Optional for dev)</span>
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <Key className="w-4 h-4" />
                </div>
                <input
                  type={showKey ? 'text' : 'password'}
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="Optional: test-admin-key or leave blank for local dev"
                  className="w-full text-xs pl-9 pr-10 py-2.5 bg-slate-50 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-indigo-500 font-mono"
                />
                <button
                  type="button"
                  onClick={() => setShowKey(!showKey)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600"
                >
                  {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white font-bold text-xs rounded-lg shadow-sm flex items-center justify-center gap-2 transition-colors cursor-pointer"
            >
              {isLoading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Authenticating Workspace...</span>
                </>
              ) : (
                <>
                  <Lock className="w-3.5 h-3.5" />
                  <span>Enter Creator Workspace</span>
                </>
              )}
            </button>
          </form>

          {/* Security Features footer */}
          <div className="pt-4 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
            <div className="flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>Multitenant Isolation (SEC-01)</span>
            </div>
            <span className="font-mono text-slate-400">RBAC Enabled</span>
          </div>
        </div>
      </div>
    </div>
  );
}
