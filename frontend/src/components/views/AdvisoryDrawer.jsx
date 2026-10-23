import React, { useState, useEffect, useRef } from 'react';
import { api } from '../../api/client';
import { Bot, Sparkles, Send, X, RefreshCw } from 'lucide-react';

export default function AdvisoryDrawer({ isOpen, onClose, creatorId }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: `👋 Hey! I am your AI Growth Advisor, grounded directly in your PostgreSQL metrics for **${creatorId}**. I know your average engagement rate, peak posting windows, and scheduled drafts. Click any quick prompt or ask me anything!`,
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

  const handleSend = async (textToSend) => {
    const text = textToSend || input;
    if (!text.trim() || isLoading) return;

    setMessages(prev => [...prev, { role: 'user', content: text }]);
    setInput('');
    setIsLoading(true);

    try {
      const res = await api.chatAdvisor(creatorId, text);
      setMessages(prev => [...prev, { role: 'assistant', content: res.reply }]);
      if (res.suggested_followups && res.suggested_followups.length > 0) {
        setChips(res.suggested_followups);
      }
    } catch (err) {
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: `❌ Could not reach advisory engine: ${err.message}` },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/30 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="w-full max-w-md bg-white border-l border-slate-200 h-full flex flex-col shadow-2xl animate-in slide-in-from-right duration-200">
        {/* Drawer Header */}
        <div className="h-16 px-5 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold text-sm">
              <Bot className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">AI Growth Advisor</h3>
              <span className="text-[11px] text-slate-500 font-medium">Grounded in PostgreSQL metrics</span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Messages Body */}
        <div className="flex-1 p-4 overflow-y-auto space-y-3">
          {messages.map((m, idx) => (
            <div
              key={idx}
              className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}
            >
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-3 text-xs leading-relaxed ${
                  m.role === 'user'
                    ? 'bg-indigo-600 text-white rounded-br-xs'
                    : 'bg-slate-100 text-slate-800 border border-slate-200/80 rounded-bl-xs'
                }`}
              >
                <div className="whitespace-pre-wrap">{m.content}</div>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex items-center gap-2 text-xs text-indigo-600 bg-indigo-50 p-3 rounded-xl border border-indigo-100 w-fit">
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              <span>Analyzing performance signals...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Prompt Chips */}
        <div className="p-3 border-t border-slate-100 bg-slate-50/50 flex flex-wrap gap-1.5 max-h-32 overflow-y-auto">
          {chips.map((chip, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(chip)}
              className="text-[11px] font-semibold text-indigo-700 bg-white border border-indigo-200/80 hover:bg-indigo-50 px-2.5 py-1 rounded-full transition shadow-xs text-left"
            >
              {chip}
            </button>
          ))}
        </div>

        {/* Input Box */}
        <div className="p-3 border-t border-slate-200 bg-white">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex items-center gap-2"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask your advisor anything..."
              className="flex-1 text-xs bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2.5 outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="p-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl shadow-xs transition disabled:opacity-40"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
