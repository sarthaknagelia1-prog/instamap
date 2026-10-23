import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import MetricsStrip from './components/MetricsStrip';
import AdvisoryChatbot from './components/AdvisoryChatbot';
import ContentSchedule from './components/ContentSchedule';
import ApprovalsStudio from './components/ApprovalsStudio';
import TrendRadar from './components/TrendRadar';
import IngestionOnboard from './components/IngestionOnboard';
import UserGuideModal from './components/UserGuideModal';
import { api } from './api/client';
import { Bot, Calendar, ShieldCheck, Radio, BookOpen, UploadCloud } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('advisor');
  const [creators, setCreators] = useState([{ id: 'creator_sarthak', total_posts: 10 }]);
  const [selectedCreator, setSelectedCreator] = useState('creator_sarthak');
  const [metricsData, setMetricsData] = useState(null);
  const [plan, setPlan] = useState(null);
  const [approvals, setApprovals] = useState([]);
  const [isOnline, setIsOnline] = useState(true);
  const [isCycleRunning, setIsCycleRunning] = useState(false);
  const [isReplanning, setIsReplanning] = useState(false);
  const [isGuideOpen, setIsGuideOpen] = useState(false);
  const [alert, setAlert] = useState(null);

  const showAlert = (msg) => {
    setAlert(msg);
    setTimeout(() => setAlert(null), 6000);
  };

  const loadAllData = async (cid) => {
    const creator = cid || selectedCreator;
    try {
      const [m, p, a] = await Promise.all([
        api.getMetrics(creator).catch(() => null),
        api.getContentPlan(creator).catch(() => null),
        api.getApprovals(creator).catch(() => []),
      ]);
      setMetricsData(m);
      setPlan(p);
      setApprovals(a || []);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    // Check health
    api.getHealth()
      .then(() => setIsOnline(true))
      .catch(() => setIsOnline(false));

    // Load creators
    api.getCreators()
      .then((data) => {
        if (data && data.length > 0) {
          setCreators(data);
          const active = data.find((c) => c.total_posts > 0) || data[0];
          setSelectedCreator(active.id);
          loadAllData(active.id);
        }
      })
      .catch(() => {
        loadAllData('creator_sarthak');
      });
  }, []);

  const handleSelectCreator = (cid) => {
    setSelectedCreator(cid);
    loadAllData(cid);
  };

  const handleRunCycle = async () => {
    setIsCycleRunning(true);
    showAlert('Running autonomous orchestrator cycle...');
    try {
      const data = await api.runOrchestrator(selectedCreator);
      showAlert(`Autonomous cycle complete! Action: ${data.decision?.action || 'Success'}`);
      loadAllData(selectedCreator);
    } catch (e) {
      showAlert('Failed to run cycle: ' + e.message);
    } finally {
      setIsCycleRunning(false);
    }
  };

  const handleReplan = async () => {
    setIsReplanning(true);
    showAlert('Formulating fresh 7-day schedule...');
    try {
      const data = await api.generatePlan(selectedCreator, 1);
      setPlan(data);
      showAlert('New 7-day schedule active!');
    } catch (e) {
      showAlert('Failed to replan: ' + e.message);
    } finally {
      setIsReplanning(false);
    }
  };

  const handleDecideApproval = async (approvalId, decision) => {
    try {
      await api.decideApproval(approvalId, decision, `Decision via React Dashboard: ${decision}`);
      showAlert(`Item updated to ${decision}!`);
      const a = await api.getApprovals(selectedCreator);
      setApprovals(a || []);
    } catch (e) {
      showAlert('Error: ' + e.message);
    }
  };

  const handleDraftFromTrend = (topic) => {
    showAlert(`Draft generation initiated for trend: "${topic}"`);
    setActiveTab('approvals');
  };

  const tabs = [
    { id: 'advisor', label: 'AI Growth Advisor', icon: Bot, badge: 'Active' },
    { id: 'plan', label: '7-Day Schedule', icon: Calendar },
    { id: 'approvals', label: 'Review Studio', icon: ShieldCheck, count: approvals.filter((a) => a.status === 'pending').length },
    { id: 'trends', label: 'Trend Radar', icon: Radio },
    { id: 'onboard', label: 'Ingestion & Onboard', icon: UploadCloud },
  ];

  return (
    <div className="min-h-screen bg-[#090d16] text-[#f8fafc] flex flex-col font-sans">
      <Navbar
        creators={creators}
        selectedCreator={selectedCreator}
        onSelectCreator={handleSelectCreator}
        onRunCycle={handleRunCycle}
        isCycleRunning={isCycleRunning}
        onOpenGuide={() => setIsGuideOpen(true)}
        onOpenBriefing={() => window.open(`http://localhost:8000/reports/weekly/${selectedCreator}/html`, '_blank')}
        isOnline={isOnline}
      />

      <main className="max-w-[1400px] w-full mx-auto p-6 flex-1">
        {alert && (
          <div className="mb-4 bg-sky-500/10 border border-sky-500/30 text-sky-200 text-xs px-4 py-3 rounded-xl flex items-center justify-between">
            <span>{alert}</span>
            <button onClick={() => setAlert(null)} className="text-slate-400 hover:text-white">✕</button>
          </div>
        )}

        <MetricsStrip
          metrics={metricsData?.metrics}
          trends={metricsData?.trends}
          bestWindow={metricsData?.best_posting_window}
          pendingApprovalsCount={approvals.filter((a) => a.status === 'pending').length}
        />

        {/* Tab Navigation */}
        <div className="flex gap-2 border-b border-[#1f293d] mb-6 overflow-x-auto pb-1">
          {tabs.map((t) => {
            const Icon = t.icon;
            const isActive = activeTab === t.id;
            return (
              <button
                key={t.id}
                onClick={() => setActiveTab(t.id)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-xs font-semibold whitespace-nowrap transition ${
                  isActive
                    ? 'bg-sky-500/15 text-sky-400 border-b-2 border-sky-400'
                    : 'text-slate-400 hover:text-white hover:bg-[#1e293b]'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{t.label}</span>
                {t.badge && (
                  <span className="text-[10px] font-bold bg-sky-500/20 text-sky-300 px-1.5 py-0.2 rounded-full">
                    {t.badge}
                  </span>
                )}
                {t.count !== undefined && t.count > 0 && (
                  <span className="text-[10px] font-bold bg-amber-400 text-black px-1.5 py-0.2 rounded-full">
                    {t.count}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* Tab Content */}
        {activeTab === 'advisor' && (
          <AdvisoryChatbot
            creatorId={selectedCreator}
            metrics={metricsData?.metrics}
            bestWindow={metricsData?.best_posting_window}
          />
        )}

        {activeTab === 'plan' && (
          <ContentSchedule
            plan={plan}
            onReplan={handleReplan}
            isReplanning={isReplanning}
          />
        )}

        {activeTab === 'approvals' && (
          <ApprovalsStudio
            approvals={approvals}
            onDecide={handleDecideApproval}
            onRefresh={() => loadAllData()}
          />
        )}

        {activeTab === 'trends' && (
          <TrendRadar onDraftFromTrend={handleDraftFromTrend} />
        )}

        {activeTab === 'onboard' && (
          <IngestionOnboard
            selectedCreator={selectedCreator}
            onComplete={(cid) => {
              setSelectedCreator(cid);
              loadAllData(cid);
              setActiveTab('plan');
            }}
          />
        )}
      </main>

      <UserGuideModal isOpen={isGuideOpen} onClose={() => setIsGuideOpen(false)} />

      <footer className="border-t border-[#1f293d] px-6 py-4 text-xs text-slate-500 flex items-center justify-between bg-[#111827]">
        <div>InstaMap Growth Engine &bull; Standalone React Frontend Layer</div>
        <div>FastAPI Backend on Port 8000 &bull; PostgreSQL instaDB</div>
      </footer>
    </div>
  );
}
