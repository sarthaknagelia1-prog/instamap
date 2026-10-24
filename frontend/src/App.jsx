import React, { useState, useEffect } from 'react';
import { api } from './api/client';
import Sidebar from './components/shell/Sidebar';
import TopNav from './components/shell/TopNav';
import ToastContainer from './components/shell/ToastContainer';

import LoginView from './components/views/LoginView';
import OverviewDashboard from './components/views/OverviewDashboard';
import CreatorsView from './components/views/CreatorsView';
import DataImportView from './components/views/DataImportView';
import AnalyticsView from './components/views/AnalyticsView';
import ViralityPredictorView from './components/views/ViralityPredictorView';
import SimulationStudioView from './components/views/SimulationStudioView';
import StrategyView from './components/views/StrategyView';
import CalendarView from './components/views/CalendarView';
import DraftStudioView from './components/views/DraftStudioView';
import ExperimentsView from './components/views/ExperimentsView';
import TrendRadarView from './components/views/TrendRadarView';
import ApprovalsView from './components/views/ApprovalsView';
import AdvisoryDrawer from './components/views/AdvisoryDrawer';

export default function App() {
  const [currentUser, setCurrentUser] = useState(() => {
    try {
      const stored = localStorage.getItem('instamap_user');
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });

  const [activeView, setActiveView] = useState('overview');
  const [creators, setCreators] = useState([]);
  const [selectedCreator, setSelectedCreator] = useState('creator_sarthak');
  const [isOnline, setIsOnline] = useState(true);
  const [isCycleRunning, setIsCycleRunning] = useState(false);
  const [isAdvisorOpen, setIsAdvisorOpen] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const [toasts, setToasts] = useState([]);
  const [pendingApprovalsCount, setPendingApprovalsCount] = useState(0);

  const showToast = (message, type = 'info', title = '') => {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev, { id, message, type, title }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 5000);
  };

  const handleDismissToast = (id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const handleLoginSuccess = (user) => {
    setCurrentUser(user);
    if (user.allowed_creators && user.allowed_creators.length > 0) {
      setSelectedCreator(user.allowed_creators[0]);
    }
    refreshCreators();
  };

  const handleLogout = async () => {
    try {
      await api.logout();
    } catch {}
    localStorage.removeItem('instamap_token');
    localStorage.removeItem('instamap_api_key');
    localStorage.removeItem('instamap_user');
    setCurrentUser(null);
    showToast('Signed out of workspace.', 'info');
  };

  const refreshCreators = () => {
    api.getCreators()
      .then((data) => {
        if (data && data.length > 0) {
          setCreators(data);
          const hasSelected = data.some(c => c.id === selectedCreator);
          if (!hasSelected) setSelectedCreator(data[0].id);
        }
      })
      .catch(() => {});
  };

  const refreshPendingCount = (cid = selectedCreator) => {
    api.listApprovals({ creator_id: cid, status: 'pending' })
      .then((items) => setPendingApprovalsCount(items?.length || 0))
      .catch(() => setPendingApprovalsCount(0));
  };

  useEffect(() => {
    api.getHealth()
      .then(() => setIsOnline(true))
      .catch(() => setIsOnline(false));

    if (currentUser) {
      refreshCreators();
      refreshPendingCount();
    }

    const interval = setInterval(() => {
      api.getHealth()
        .then(() => setIsOnline(true))
        .catch(() => setIsOnline(false));
    }, 30000);

    return () => clearInterval(interval);
  }, [selectedCreator, currentUser]);

  const handleRunCycle = async () => {
    setIsCycleRunning(true);
    showToast('Autonomous orchestrator cycle initiated...', 'info');

    try {
      const res = await api.runOrchestrator(selectedCreator, 'manual');
      const actionName = res.decision?.action || 'completed';
      showToast(`Autonomous cycle finished! Decision: ${actionName}`, 'success');
      refreshPendingCount(selectedCreator);
    } catch (err) {
      showToast(`Cycle failed: ${err.message}`, 'error');
    } finally {
      setIsCycleRunning(false);
    }
  };

  const titles = {
    overview: 'Overview Dashboard',
    creators: 'Creator Profiles',
    import: 'Data Import & Readiness',
    analytics: 'Analytics & Posts',
    virality: 'Virality ML Predictor',
    simulation: 'Growth & Content Simulation',
    strategy: 'Growth Strategy',
    calendar: 'Content Calendar',
    drafts: 'Draft Studio',
    experiments: 'Experiments Lab',
    trends: 'Trend Radar',
    approvals: 'Approvals & History',
  };

  // If unauthenticated, present the Login & Workspace Switcher view
  if (!currentUser) {
    return (
      <>
        <LoginView onLoginSuccess={handleLoginSuccess} showToast={showToast} />
        <ToastContainer toasts={toasts} onDismiss={handleDismissToast} />
      </>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans flex antialiased">
      {/* Sidebar navigation */}
      <Sidebar
        activeView={activeView}
        setActiveView={setActiveView}
        isMobileOpen={isMobileOpen}
        setIsMobileOpen={setIsMobileOpen}
        pendingCount={pendingApprovalsCount}
        onOpenAdvisor={() => setIsAdvisorOpen(true)}
      />

      {/* Main layout column */}
      <div className="flex-1 flex flex-col lg:pl-64 min-w-0">
        <TopNav
          creators={creators}
          selectedCreator={selectedCreator}
          onSelectCreator={(cid) => {
            setSelectedCreator(cid);
            refreshPendingCount(cid);
            showToast(`Switched workspace to ${cid}`, 'info');
          }}
          activeViewTitle={titles[activeView] || 'InstaMap'}
          onOpenAdvisor={() => setIsAdvisorOpen(true)}
          onOpenBriefing={() => window.open(api.getWeeklyReportHtmlUrl(selectedCreator), '_blank')}
          onRunCycle={handleRunCycle}
          isCycleRunning={isCycleRunning}
          isOnline={isOnline}
          onToggleMobile={() => setIsMobileOpen(!isMobileOpen)}
          currentUser={currentUser}
          onLogout={handleLogout}
        />

        <main className="p-4 sm:p-6 lg:p-8 max-w-[1440px] w-full mx-auto flex-1">
          {activeView === 'overview' && (
            <OverviewDashboard
              creatorId={selectedCreator}
              onNavigate={setActiveView}
              onOpenAdvisor={() => setIsAdvisorOpen(true)}
              onRunCycle={handleRunCycle}
              isCycleRunning={isCycleRunning}
            />
          )}

          {activeView === 'creators' && (
            <CreatorsView
              currentCreatorId={selectedCreator}
              onSelectCreator={(cid) => {
                setSelectedCreator(cid);
                showToast(`Selected creator: ${cid}`, 'info');
              }}
              onNavigate={setActiveView}
            />
          )}

          {activeView === 'import' && (
            <DataImportView
              creatorId={selectedCreator}
              onImportSuccess={(cid) => {
                refreshCreators();
                setSelectedCreator(cid);
                setActiveView('overview');
              }}
              showToast={showToast}
            />
          )}

          {activeView === 'analytics' && (
            <AnalyticsView creatorId={selectedCreator} />
          )}

          {activeView === 'virality' && (
            <ViralityPredictorView creatorId={selectedCreator} showToast={showToast} />
          )}

          {activeView === 'simulation' && (
            <SimulationStudioView creatorId={selectedCreator} showToast={showToast} />
          )}

          {activeView === 'strategy' && (
            <StrategyView creatorId={selectedCreator} showToast={showToast} />
          )}

          {activeView === 'calendar' && (
            <CalendarView
              creatorId={selectedCreator}
              onNavigateToDrafts={() => setActiveView('drafts')}
              showToast={showToast}
            />
          )}

          {activeView === 'drafts' && (
            <DraftStudioView creatorId={selectedCreator} showToast={showToast} />
          )}

          {activeView === 'experiments' && (
            <ExperimentsView creatorId={selectedCreator} showToast={showToast} />
          )}

          {activeView === 'trends' && (
            <TrendRadarView
              onDraftFromTrend={(topic) => {
                showToast(`Draft initiated for "${topic}"!`, 'info');
                setActiveView('drafts');
              }}
              showToast={showToast}
            />
          )}

          {activeView === 'approvals' && (
            <ApprovalsView creatorId={selectedCreator} showToast={showToast} />
          )}
        </main>
      </div>

      {/* Slide-over AI Advisor Drawer */}
      <AdvisoryDrawer
        isOpen={isAdvisorOpen}
        onClose={() => setIsAdvisorOpen(false)}
        creatorId={selectedCreator}
      />

      {/* Toast Alert System */}
      <ToastContainer toasts={toasts} onDismiss={handleDismissToast} />
    </div>
  );
}
