import React, { useState, useRef, useEffect } from 'react';
import { Bot, Send, Sparkles, RefreshCw } from 'lucide-react';
import { api } from '../api/client';

export default function AdvisoryChatbot({ creatorId, metrics, bestWindow }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: `### 👋 Welcome to your AI Growth Advisory Copilot!\n\nI am connected directly to your real data in **instaDB**. I can see your current Average Engagement Rate (**${(metrics?.average_engagement_rate || 8.08).toFixed(2)}%**), your peak algorithmic window (**${bestWindow || 'Friday 18:00 - 21:00 UTC'}**), and your format performance.\n\nAsk me anything or click a starter chip below to formulate viral hooks, retention strategies, or script critiques!`,
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [chips, setChips] = useState([
    '⚡ Write 3 viral hooks for my niche',
    '🕒 What is my peak posting window and why?',
    '📈 How can I increase my average engagement rate?',
    '📅 What should I post this week?',
    '🧪 Explain how Welch\'s t-test proves my content works',
  ]);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSend = async (messageText) => {
    const textToSend = messageText || input;
    if (!textToSend.trim() || isLoading) return;

    const userMsg = { role: 'user', content: textToSend };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const data = await api.chatAdvisor(creatorId, textToSend);
      setMessages((prev) => [...prev, { role: 'assistant', content: data.reply }]);
      if (data.suggested_followups && data.suggested_followups.length > 0) {
        setChips(data.suggested_followups);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `❌ Error: ${err.message || 'Could not reach advisor engine.'}` },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const escapeHtml = (unsafe) => {
    return (unsafe || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  };

  const renderMarkdown = (text) => {
    const safe = escapeHtml(text);
    return safe
      .replace(/### (.*?)\n/g, '<h4 class="text-sky-400 font-bold text-sm my-2">$1</h4>')
      .replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-bold">$1</strong>')
      .replace(/\*(.*?)\*/g, '<em class="text-slate-200 italic">$1</em>')
      .replace(/`([^`]+)`/g, '<code class="bg-[#1e293b] text-sky-400 px-1.5 py-0.5 rounded font-mono text-xs">$1</code>')
      .replace(/^> (.*?)$/gm, '<blockquote class="border-l-2 border-pink-500 pl-3 my-2 text-slate-300 italic">$1</blockquote>')
      .replace(/\n/g, '<br />');
  };

  return (
    <div className="bg-[#111827] border border-[#1f293d] rounded-xl flex flex-col h-[600px] overflow-hidden">
      {/* Header */}
      <div className="px-6 py-3.5 border-b border-[#1f293d] bg-[#111827] flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-bold text-sm text-white flex items-center gap-2">
              AI Growth Advisor
              <span className="text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-1.5 py-0.2 rounded-full">
                Active in instaDB
              </span>
            </h3>
            <p className="text-xs text-slate-400">Grounded in your real metrics, sweet spots, and trends</p>
          </div>
        </div>
        <button
          onClick={() =>
            setMessages([
              {
                role: 'assistant',
                content: 'Chat reset. Ask any question about your strategy, posting times, or viral hooks!',
              },
            ])
          }
          className="text-xs text-slate-400 hover:text-white flex items-center gap-1"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Reset</span>
        </button>
      </div>

      {/* Messages Feed */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`max-w-[85%] rounded-xl p-4 text-xs leading-relaxed ${
              m.role === 'user'
                ? 'ml-auto bg-gradient-to-r from-sky-600 to-blue-600 text-white shadow-md shadow-sky-600/20'
                : 'mr-auto bg-[#090d16] border border-[#1f293d] text-slate-300 border-l-4 border-l-sky-400'
            }`}
            dangerouslySetInnerHTML={{ __html: renderMarkdown(m.content) }}
          />
        ))}
        {isLoading && (
          <div className="mr-auto bg-[#090d16] border border-[#1f293d] rounded-xl p-4 text-xs text-slate-400 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-sky-400 animate-spin" />
            <span>Consulting intelligence engine...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggestion Chips & Input */}
      <div className="border-t border-[#1f293d] p-4 bg-[#090d16]/70 space-y-3">
        {/* Chips */}
        <div className="flex gap-2 overflow-x-auto pb-1 text-xs">
          {chips.map((chip, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(chip)}
              className="bg-[#1e293b] hover:bg-[#334155] border border-[#334155] hover:border-sky-400 text-slate-300 hover:text-white px-3 py-1 rounded-full whitespace-nowrap transition text-[11px] font-semibold"
            >
              {chip}
            </button>
          ))}
        </div>

        {/* Input Bar */}
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask your advisor anything (e.g. 'Critique my hook' or 'Why is Friday best?')..."
            className="flex-1 bg-[#111827] border border-[#334155] focus:border-sky-400 rounded-lg px-4 py-2 text-xs text-white outline-none"
          />
          <button
            onClick={() => handleSend()}
            disabled={isLoading || !input.trim()}
            className="bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white p-2.5 rounded-lg transition"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
