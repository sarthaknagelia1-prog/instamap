import React from 'react';
import {
  LayoutDashboard,
  Users,
  UploadCloud,
  BarChart3,
  Compass,
  Calendar,
  PenTool,
  FlaskConical,
  Radio,
  ShieldCheck,
  Bot,
  Sparkles,
  ExternalLink,
  ChevronRight,
  Activity,
  Zap
} from 'lucide-react';

export default function Sidebar({ activeView, setActiveView, isMobileOpen, setIsMobileOpen, pendingCount = 0, onOpenAdvisor }) {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'creators', label: 'Creators', icon: Users },
    { id: 'import', label: 'Data Import & Readiness', icon: UploadCloud },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'virality', label: 'Virality ML Predictor', icon: Sparkles },
    { id: 'simulation', label: 'Simulation Studio', icon: Activity },
    { id: 'strategy', label: 'Growth Strategy', icon: Compass },
    { id: 'calendar', label: 'Content Calendar', icon: Calendar },
    { id: 'drafts', label: 'Draft Studio', icon: PenTool },
    { id: 'experiments', label: 'Experiments Lab', icon: FlaskConical },
    { id: 'trends', label: 'Trend Radar', icon: Radio },
    { id: 'approvals', label: 'Approvals & History', icon: ShieldCheck, badge: pendingCount > 0 ? pendingCount : null },
  ];

  const handleNavClick = (id) => {
    setActiveView(id);
    if (setIsMobileOpen) setIsMobileOpen(false);
  };

  return (
    <>
      {/* Mobile backdrop */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/40 backdrop-blur-sm lg:hidden"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      <aside className={`
        fixed top-0 bottom-0 left-0 z-50 w-64 bg-white border-r border-slate-200 flex flex-col transition-transform duration-200 ease-in-out
        lg:translate-x-0 ${isMobileOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        {/* Brand header */}
        <div className="h-16 px-6 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-2.5 cursor-pointer" onClick={() => handleNavClick('overview')}>
            <div className="w-9 h-9 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-black text-lg shadow-sm shadow-indigo-200">
              ⚡
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-extrabold text-slate-900 tracking-tight text-base">InstaMap</span>
                <span className="text-[10px] font-bold uppercase tracking-wider bg-indigo-50 text-indigo-700 px-1.5 py-0.5 rounded border border-indigo-100">
                  Engine
                </span>
              </div>
              <p className="text-[11px] text-slate-500 font-medium">Creator Growth Platform</p>
            </div>
          </div>
        </div>

        {/* Navigation list */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          <div className="px-3 pb-2 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
            Platform Menu
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeView === item.id;
            return (
              <button
                key={item.id}
                onClick={() => handleNavClick(item.id)}
                className={`
                  w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-semibold transition-colors text-left
                  ${isActive
                    ? 'bg-indigo-50 text-indigo-700 font-bold border border-indigo-100/80 shadow-xs'
                    : 'text-slate-600 hover:bg-slate-100/80 hover:text-slate-900'}
                `}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-indigo-600' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </div>
                {item.badge !== undefined && item.badge !== null && (
                  <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                    isActive ? 'bg-indigo-600 text-white' : 'bg-amber-100 text-amber-800'
                  }`}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* AI Advisory Drawer Card */}
        <div className="p-3 mx-3 mb-3 bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 rounded-xl border border-indigo-100/80">
          <div className="flex items-center gap-2 mb-1.5">
            <Sparkles className="w-4 h-4 text-indigo-600 animate-pulse" />
            <span className="text-xs font-bold text-indigo-950">AI Growth Advisor</span>
          </div>
          <p className="text-[11px] text-slate-600 mb-2.5 leading-relaxed">
            Grounded in your real PostgreSQL metrics, viral hooks & sweet spots.
          </p>
          <button
            onClick={onOpenAdvisor}
            className="w-full py-1.5 px-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-bold shadow-xs transition flex items-center justify-center gap-1.5"
          >
            <Bot className="w-3.5 h-3.5" />
            <span>Open Advisor Chat</span>
          </button>
        </div>

        {/* Footer info */}
        <div className="p-4 border-t border-slate-200 text-[11px] text-slate-500 flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="font-semibold text-slate-700">Zero-API Mode</span>
          </div>
          <span className="font-mono text-slate-400">PostgreSQL</span>
        </div>
      </aside>
    </>
  );
}
