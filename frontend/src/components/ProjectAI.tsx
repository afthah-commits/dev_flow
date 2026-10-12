import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { aiApi } from '../lib/aiApi';
import { AIConversation, AIMessage, TaskSuggestion } from '../types/ai';
import { Project } from '../types/project';
import { taskApi } from '../lib/taskApi';
import { TaskStatus } from '../types/task';
import {
  Sparkles,
  Send,
  Plus,
  Trash2,
  CheckCircle2,
  AlertCircle,
  Calendar,
  ExternalLink,
  Layers,
  ArrowRight,
  Bot,
  User as UserIcon
} from 'lucide-react';

interface Props {
  project: Project;
}

// Lightweight Markdown & Entity Formatter
function FormattedMessage({ content }: { content: string }) {
  const lines = content.split('\n');

  return (
    <div className="space-y-2 text-sm leading-relaxed text-gray-200">
      {lines.map((line, idx) => {
        // Headers
        if (line.startsWith('### ')) {
          return <h4 key={idx} className="text-base font-bold text-white mt-3 mb-1">{line.slice(4)}</h4>;
        }
        if (line.startsWith('## ')) {
          return <h3 key={idx} className="text-lg font-bold text-white mt-4 mb-2">{line.slice(3)}</h3>;
        }
        if (line.startsWith('# ')) {
          return <h2 key={idx} className="text-xl font-bold text-white mt-4 mb-2">{line.slice(2)}</h2>;
        }

        // Bullet lists
        if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
          const bulletText = line.trim().slice(2);
          return (
            <div key={idx} className="flex items-start gap-2 ml-2">
              <span className="text-indigo-400 mt-1.5 text-xs">•</span>
              <span className="flex-1">{renderFormattedText(bulletText)}</span>
            </div>
          );
        }

        // Numbered lists
        const numberedMatch = line.trim().match(/^(\d+)\.\s+(.*)$/);
        if (numberedMatch) {
          return (
            <div key={idx} className="flex items-start gap-2 ml-2">
              <span className="text-indigo-400 font-semibold text-xs mt-0.5">{numberedMatch[1]}.</span>
              <span className="flex-1">{renderFormattedText(numberedMatch[2])}</span>
            </div>
          );
        }

        // Empty lines
        if (!line.trim()) {
          return <div key={idx} className="h-1.5" />;
        }

        // Regular line
        return <p key={idx} className="leading-relaxed">{renderFormattedText(line)}</p>;
      })}
    </div>
  );
}

// Inline formatting: **bold**, `code`, and task keys like PROJ-123
function renderFormattedText(text: string) {
  const regex = /(\*\*.*?\*\*|`.*?`|[A-Z0-9]+-\d+)/g;
  const parts = text.split(regex);

  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i} className="font-semibold text-white">{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return <code key={i} className="px-1.5 py-0.5 bg-gray-900 border border-gray-700/80 rounded text-xs font-mono text-indigo-300">{part.slice(1, -1)}</code>;
    }
    if (/^[A-Z0-9]+-\d+$/.test(part)) {
      return (
        <span key={i} className="inline-flex items-center px-1.5 py-0.2 rounded bg-indigo-950/80 border border-indigo-700/60 text-indigo-300 text-xs font-mono font-medium mx-0.5">
          {part}
        </span>
      );
    }
    return part;
  });
}

export function ProjectAI({ project }: Props) {
  const navigate = useNavigate();
  const [conversations, setConversations] = useState<AIConversation[]>([]);
  const [activeConv, setActiveConv] = useState<AIConversation | null>(null);
  const [messages, setMessages] = useState<AIMessage[]>([]);
  
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<{ provider: string; configured: boolean; model: string } | null>(null);
  const [applyingBatch, setApplyingBatch] = useState(false);
  const [batchCreatedCount, setBatchCreatedCount] = useState<number | null>(null);

  const chatEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // For Manual Task Generation Dialog
  const [proposedTask, setProposedTask] = useState<TaskSuggestion | null>(null);

  useEffect(() => {
    loadConversations();
    if (typeof aiApi?.getStatus === 'function') {
      try {
        const p = aiApi.getStatus();
        if (p && typeof p.then === 'function') {
          p.then(setStatus).catch(() => {
            setStatus({ provider: 'mock', configured: true, model: 'mock' });
          });
        }
      } catch {
        setStatus({ provider: 'mock', configured: true, model: 'mock' });
      }
    } else {
      setStatus({ provider: 'mock', configured: true, model: 'mock' });
    }
  }, [project.id]);

  useEffect(() => {
    if (typeof chatEndRef.current?.scrollIntoView === 'function') {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, loading]);

  const loadConversations = async () => {
    try {
      const res = await aiApi.listConversations(project.id);
      const list = Array.isArray(res) ? res : ((res as any)?.items || []);
      setConversations(list);
      if (list.length > 0 && !activeConv) {
        loadConversation(list[0].id);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const loadConversation = async (id: string) => {
    try {
      setLoading(true);
      setError(null);
      const res = await aiApi.getConversation(id);
      setActiveConv(res);
      setMessages(res.messages || []);
    } catch (e) {
      setError("Failed to load conversation");
    } finally {
      setLoading(false);
    }
  };

  const handleNewConversation = async () => {
    try {
      setLoading(true);
      const res = await aiApi.createConversation("Project Assistant", project.id);
      setConversations([res, ...conversations]);
      setActiveConv(res);
      setMessages([]);
    } catch (e) {
      setError("Failed to create conversation");
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteConversation = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this conversation?")) return;
    try {
      await aiApi.deleteConversation(id);
      const updated = conversations.filter(c => c.id !== id);
      setConversations(updated);
      if (activeConv?.id === id) {
        if (updated.length > 0) {
          loadConversation(updated[0].id);
        } else {
          setActiveConv(null);
          setMessages([]);
        }
      }
    } catch (err) {
      setError("Failed to delete conversation");
    }
  };

  const handleSend = async (text: string) => {
    if (!text.trim() || loading) return;
    
    let convId = activeConv?.id;
    if (!convId) {
      try {
        const newC = await aiApi.createConversation(text.substring(0, 32) + '...', project.id);
        setConversations([newC, ...conversations]);
        setActiveConv(newC);
        convId = newC.id;
      } catch (e) {
        setError("Failed to initialize conversation");
        return;
      }
    }

    const tempMsg: AIMessage = { id: 'temp-' + Date.now(), role: 'user', content: text, created_at: new Date().toISOString() };
    setMessages(prev => [...prev, tempMsg]);
    setInput('');
    setLoading(true);
    setError(null);

    try {
      const aiReply = await aiApi.sendMessage(convId, text);
      setMessages(prev => {
        const withoutTemp = prev.filter(m => m.id !== tempMsg.id);
        return [...withoutTemp, tempMsg, aiReply];
      });
    } catch (e: any) {
      setError(e.response?.data?.detail || "AI Assistant request failed. Please try again.");
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  };

  const handleQuickAction = async (action: string) => {
    if (action === 'task') {
      const instruction = window.prompt("Describe the task you want to generate:");
      if (!instruction) return;
      
      setLoading(true);
      setError(null);
      try {
        const res = await aiApi.suggestTask(project.id, instruction);
        if (res?.structured_data) {
          setProposedTask(res.structured_data as TaskSuggestion);
        }
      } catch (e: any) {
        setError(e.response?.data?.detail || "Failed to generate task.");
      } finally {
        setLoading(false);
      }
    }
  };

  const handleCreateAllBreakdownTasks = async (subtasks: Array<{ title: string; priority?: string; points?: number; description?: string }>) => {
    if (!subtasks || subtasks.length === 0 || applyingBatch) return;
    setApplyingBatch(true);
    try {
      let created = 0;
      for (const st of subtasks) {
        await taskApi.create(project.id, {
          title: st.title,
          description: st.description || `Created via AI breakdown for ${project.name}`,
          status: TaskStatus.TODO,
          priority: (st.priority as any) || 'MEDIUM',
          labels: ['ai-breakdown']
        });
        created++;
      }
      setBatchCreatedCount(created);
      setTimeout(() => setBatchCreatedCount(null), 4000);
    } catch (err) {
      alert("Failed to create all breakdown tasks. Some tasks may not have been created.");
    } finally {
      setApplyingBatch(false);
    }
  };

  const handleCreateTask = async () => {
    if (!proposedTask) return;
    try {
      await taskApi.create(project.id, {
        title: proposedTask.title,
        description: proposedTask.description,
        status: TaskStatus.TODO,
        priority: proposedTask.priority as any,
        labels: proposedTask.labels || []
      });
      setProposedTask(null);
      alert("Task created successfully!");
    } catch (e) {
      alert("Failed to create task");
    }
  };

  const quickPrompts = [
    { label: "🎯 What should I work on today?", prompt: "What should I work on today?" },
    { label: "⚠️ Show overdue tasks", prompt: "Show me overdue tasks." },
    { label: "📊 Summarize this project", prompt: "Summarize my current project." },
    { label: "⏳ Explain project delay", prompt: "Explain why this project is delayed." },
    { label: "🧩 Break down payment feature", prompt: "Break the payment integration feature into smaller tasks." }
  ];

  return (
    <div className="flex flex-col md:flex-row h-[700px] border border-gray-800 rounded-xl overflow-hidden bg-gray-950 shadow-2xl">
      {/* Sidebar: Conversation History */}
      <div className="w-full md:w-72 border-r border-gray-800 flex flex-col bg-gray-900/90">
        <div className="p-3.5 border-b border-gray-800 flex items-center justify-between gap-2">
          <button 
            onClick={handleNewConversation}
            className="flex-1 flex items-center justify-center gap-2 py-2 px-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold shadow transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Chat</span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto divide-y divide-gray-800/40">
          {conversations.length === 0 ? (
            <div className="p-4 text-center text-xs text-gray-500">
              No conversations yet. Start a new chat to begin.
            </div>
          ) : (
            conversations.map(c => (
              <div
                key={c.id}
                onClick={() => loadConversation(c.id)}
                className={`group flex items-center justify-between px-3.5 py-3 text-xs cursor-pointer transition-colors ${
                  activeConv?.id === c.id 
                    ? 'bg-indigo-950/40 text-white border-l-2 border-indigo-500' 
                    : 'text-gray-400 hover:bg-gray-800/60 hover:text-gray-200'
                }`}
              >
                <div className="truncate flex-1 pr-2">
                  <div className="font-medium truncate">{c.title}</div>
                  <div className="text-[10px] text-gray-500 mt-0.5">
                    {new Date(c.created_at).toLocaleDateString()}
                  </div>
                </div>
                <button
                  onClick={(e) => handleDeleteConversation(c.id, e)}
                  title="Delete chat"
                  className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-400 text-gray-500 rounded transition-opacity"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))
          )}
        </div>

        {/* Assistant Scope Note */}
        <div className="p-3 border-t border-gray-800/80 bg-gray-950/60 text-[11px] text-gray-400">
          <div className="font-semibold text-gray-300 flex items-center gap-1.5 mb-1">
            <Layers className="w-3.5 h-3.5 text-indigo-400" />
            <span>Scope: {project.name}</span>
          </div>
          <p className="text-[10px] text-gray-500 leading-tight">
            Queries and actions are securely isolated to your organization & project.
          </p>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col relative bg-gray-900/40">
        {/* Header Bar */}
        <div className="px-4 py-3 border-b border-gray-800 bg-gray-900/80 flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
              <Bot className="w-4 h-4" />
            </div>
            <div>
              <div className="text-sm font-semibold text-white flex items-center gap-2">
                DevFlow Project Assistant
                <span className="text-[10px] font-normal px-1.5 py-0.2 rounded bg-indigo-900/60 text-indigo-300 border border-indigo-700/50">
                  Advisory + Actions
                </span>
              </div>
              <div className="text-[11px] text-gray-400">
                Natural-language tasks, project status, focus agenda, and epic breakdowns.
              </div>
            </div>
          </div>

          {/* AI Provider Status Pill */}
          <div className="flex items-center gap-2">
            {status?.provider === 'gemini' ? (
              <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
                status.configured 
                  ? 'bg-emerald-950/60 text-emerald-300 border-emerald-800/80' 
                  : 'bg-amber-950/60 text-amber-300 border-amber-800/80'
              }`}>
                <span className={`w-2 h-2 rounded-full ${status.configured ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`}></span>
                <span>{status.configured ? `Gemini 2.5 Flash` : `Gemini (Key Pending)`}</span>
              </div>
            ) : status?.provider === 'openai' ? (
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-blue-950/60 text-blue-300 border border-blue-800/80">
                <span className="w-2 h-2 rounded-full bg-blue-400"></span>
                <span>OpenAI ({status.model})</span>
              </div>
            ) : (
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-gray-800/80 text-gray-300 border border-gray-700">
                <span className="w-2 h-2 rounded-full bg-gray-400"></span>
                <span>Local Project Assistant</span>
              </div>
            )}
          </div>
        </div>

        {/* Quick Action Suggestion Chips */}
        <div className="px-4 py-2 border-b border-gray-800/60 bg-gray-950/40 overflow-x-auto flex items-center gap-2 scrollbar-none">
          <button
            onClick={() => handleQuickAction('task')}
            className="px-2.5 py-1 bg-indigo-900/50 hover:bg-indigo-900/70 text-indigo-200 text-xs rounded-full border border-indigo-700 whitespace-nowrap transition-colors flex items-center gap-1"
          >
            <Sparkles className="w-3 h-3 text-indigo-400" />
            <span>Generate Task (AI)</span>
          </button>
          <span className="text-[11px] text-gray-500 font-medium whitespace-nowrap">|</span>
          {quickPrompts.map((qp, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(qp.prompt)}
              disabled={loading}
              className="px-2.5 py-1 rounded-full text-xs bg-gray-800/80 hover:bg-gray-700 text-gray-300 hover:text-white border border-gray-700/60 whitespace-nowrap transition-colors disabled:opacity-50"
            >
              {qp.label}
            </button>
          ))}
        </div>

        {/* Batch Created Toast */}
        {batchCreatedCount !== null && (
          <div className="absolute top-24 right-4 z-20 bg-emerald-900/90 border border-emerald-700 text-emerald-100 text-xs px-3.5 py-2 rounded-lg shadow-xl flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-300" />
            <span>Successfully created {batchCreatedCount} tasks in project backlog!</span>
          </div>
        )}

        {/* Messages Stream */}
        <div className="flex-1 overflow-y-auto p-4 space-y-5">
          {messages.length === 0 && !loading && (
            <div className="h-full flex items-center justify-center text-center p-6 flex-col">
              <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mb-3">
                <Sparkles className="w-6 h-6" />
              </div>
              <h3 className="text-base font-semibold text-white mb-1">
                I am DevFlow AI. How can I help with {project.name}?
              </h3>
              <p className="text-xs text-gray-400 max-w-md mb-6 leading-relaxed">
                Ask naturally to create tasks, find overdue work, summarize project progress, or break down features into concrete subtasks.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-w-lg w-full text-left">
                {quickPrompts.slice(0, 4).map((qp, i) => (
                  <button
                    key={i}
                    onClick={() => handleSend(qp.prompt)}
                    className="p-2.5 rounded-lg bg-gray-900 border border-gray-800 hover:border-indigo-500/50 hover:bg-gray-850 text-xs text-gray-300 hover:text-white transition-all text-left flex items-start gap-2"
                  >
                    <ArrowRight className="w-3.5 h-3.5 text-indigo-400 mt-0.5 shrink-0" />
                    <span>{qp.prompt}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m, idx) => (
            <div key={idx} className={`flex gap-3 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              {m.role !== 'user' && (
                <div className="w-7 h-7 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shrink-0 mt-0.5">
                  <Bot className="w-4 h-4" />
                </div>
              )}
              
              <div className={`max-w-[85%] sm:max-w-[80%] rounded-2xl px-4 py-3.5 space-y-3 ${
                m.role === 'user'
                  ? 'bg-indigo-600 text-white rounded-br-sm shadow'
                  : 'bg-gray-850 text-gray-200 rounded-bl-sm border border-gray-800 shadow-md'
              }`}>
                {/* Author Label */}
                <div className="flex items-center justify-between text-[11px] font-semibold opacity-70 uppercase tracking-wider mb-1">
                  <span>{m.role === 'user' ? 'You' : 'DevFlow Assistant'}</span>
                  <span className="text-[10px] font-normal lowercase opacity-70">
                    {new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>

                {/* Formatted Text Content */}
                {m.role === 'user' ? (
                  <div className="whitespace-pre-wrap text-sm leading-relaxed">{m.content}</div>
                ) : (
                  <FormattedMessage content={m.content} />
                )}

                {/* Interactive Action Confirmation Cards */}
                {m.action_data?.type === 'task_created' && m.action_data.tasks && (
                  <div className="mt-3 space-y-2 pt-2 border-t border-gray-700/60">
                    <div className="text-xs font-semibold text-emerald-400 flex items-center gap-1.5">
                      <CheckCircle2 className="w-4 h-4" />
                      <span>{m.action_data.tasks.length === 1 ? 'Task Successfully Created' : `${m.action_data.tasks.length} Tasks Created`}</span>
                    </div>

                    {m.action_data.tasks.map((t, tIdx) => (
                      <div key={tIdx} className="bg-gray-900/90 border border-emerald-900/60 rounded-xl p-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2.5">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            {t.task_key && (
                              <span className="px-2 py-0.5 rounded text-xs font-mono font-bold bg-indigo-950 text-indigo-300 border border-indigo-700">
                                {t.task_key}
                              </span>
                            )}
                            <span className="text-sm font-semibold text-white">{t.title}</span>
                          </div>
                          <div className="flex items-center gap-2 text-[11px] text-gray-400">
                            {t.priority && (
                              <span className={`px-1.5 py-0.2 rounded font-medium ${
                                t.priority === 'CRITICAL' ? 'bg-red-950 text-red-300 border border-red-800' :
                                t.priority === 'HIGH' ? 'bg-amber-950 text-amber-300 border border-amber-800' :
                                'bg-gray-800 text-gray-300'
                              }`}>
                                {t.priority}
                              </span>
                            )}
                            {t.due_date && (
                              <span className="flex items-center gap-1 text-gray-400">
                                <Calendar className="w-3 h-3 text-indigo-400" />
                                {new Date(t.due_date).toLocaleDateString()}
                              </span>
                            )}
                            {t.project_name && (
                              <span className="text-gray-500">• {t.project_name}</span>
                            )}
                          </div>
                        </div>

                        <button
                          onClick={() => navigate(`/projects/${t.project_id || project.id}`)}
                          className="shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600/30 hover:bg-indigo-600/50 border border-indigo-500/40 text-xs font-medium text-indigo-200 transition-colors"
                        >
                          <span>Open Board</span>
                          <ExternalLink className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                {/* Epic Breakdown Card */}
                {m.action_data?.type === 'epic_breakdown' && m.action_data.tasks && (
                  <div className="mt-3 space-y-2.5 pt-2 border-t border-gray-700/60">
                    <div className="flex items-center justify-between">
                      <div className="text-xs font-semibold text-indigo-300 flex items-center gap-1.5">
                        <Layers className="w-4 h-4 text-indigo-400" />
                        <span>Epic Breakdown: {m.action_data.epic_title}</span>
                      </div>
                      <button
                        onClick={() => handleCreateAllBreakdownTasks(m.action_data!.tasks!)}
                        disabled={applyingBatch}
                        className="flex items-center gap-1.5 px-3 py-1 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-xs font-medium transition-colors disabled:opacity-50"
                      >
                        <Plus className="w-3 h-3" />
                        <span>{applyingBatch ? 'Creating...' : 'Create All in Backlog'}</span>
                      </button>
                    </div>

                    <div className="space-y-1.5">
                      {m.action_data.tasks.map((st, sIdx) => (
                        <div key={sIdx} className="bg-gray-900/80 border border-gray-800 rounded-lg p-2.5 flex items-center justify-between text-xs">
                          <div>
                            <div className="font-medium text-gray-200">{st.title}</div>
                            {st.description && <div className="text-[11px] text-gray-500">{st.description}</div>}
                          </div>
                          <div className="flex items-center gap-2 shrink-0">
                            <span className="px-1.5 py-0.5 rounded text-[10px] bg-gray-800 text-gray-300">
                              {st.priority || 'MEDIUM'}
                            </span>
                            {st.points && (
                              <span className="px-1.5 py-0.5 rounded text-[10px] bg-indigo-950 text-indigo-300 font-mono">
                                {st.points} pts
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {m.role === 'user' && (
                <div className="w-7 h-7 rounded-lg bg-indigo-600 flex items-center justify-center text-white shrink-0 mt-0.5 shadow">
                  <UserIcon className="w-4 h-4" />
                </div>
              )}
            </div>
          ))}

          {/* Typing/Thinking Animation */}
          {loading && (
            <div className="flex gap-3 justify-start">
              <div className="w-7 h-7 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shrink-0">
                <Bot className="w-4 h-4" />
              </div>
              <div className="bg-gray-850 text-gray-400 rounded-2xl rounded-bl-sm px-4 py-3 border border-gray-800 flex items-center space-x-2">
                <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce [animation-delay:0.2s]"></div>
                <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce [animation-delay:0.4s]"></div>
                <span className="text-xs text-gray-400 ml-2">DevFlow Assistant is thinking...</span>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Error Notification */}
        {error && (
          <div className="mx-4 mb-2 bg-red-950/90 text-red-200 px-3.5 py-2.5 rounded-lg text-xs border border-red-800/80 flex items-center justify-between shadow-lg">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
              <span>{error}</span>
            </div>
            <button onClick={() => setError(null)} className="text-red-400 hover:text-red-200 text-xs font-semibold">
              Dismiss
            </button>
          </div>
        )}

        {/* Manual Task Suggestion Modal Preview */}
        {proposedTask && (
          <div className="absolute inset-0 bg-gray-950/90 z-30 flex items-center justify-center p-4">
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 max-w-md w-full shadow-2xl space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-gray-800">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-indigo-400" />
                  <span>AI Task Suggestion</span>
                </h3>
                <button onClick={() => setProposedTask(null)} className="text-gray-400 hover:text-white text-xs">✕</button>
              </div>

              <div className="space-y-3">
                <div>
                  <label className="text-[11px] text-gray-400 uppercase font-semibold">Title</label>
                  <input
                    value={proposedTask.title}
                    onChange={e => setProposedTask({...proposedTask, title: e.target.value})}
                    className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm text-white mt-1 focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="text-[11px] text-gray-400 uppercase font-semibold">Description</label>
                  <textarea
                    value={proposedTask.description}
                    onChange={e => setProposedTask({...proposedTask, description: e.target.value})}
                    rows={3}
                    className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm text-white mt-1 focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="text-[11px] text-gray-400 uppercase font-semibold">Priority</label>
                  <select
                    value={proposedTask.priority}
                    onChange={e => setProposedTask({...proposedTask, priority: e.target.value})}
                    className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm text-white mt-1"
                  >
                    <option value="LOW">Low</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="HIGH">High</option>
                    <option value="CRITICAL">Critical</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-gray-800">
                <button
                  onClick={() => setProposedTask(null)}
                  className="px-3 py-1.5 text-xs text-gray-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateTask}
                  className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-xs font-semibold"
                >
                  Create Task
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Input Bar */}
        <div className="p-3.5 border-t border-gray-800 bg-gray-950">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend(input);
            }}
            className="flex items-center gap-2"
          >
            <input 
              ref={inputRef}
              type="text" 
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Ask the AI assistant..."
              disabled={loading}
              className="flex-1 bg-gray-900 border border-gray-800 hover:border-gray-700 rounded-xl px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 disabled:opacity-50 transition-colors"
            />
            <button 
              type="submit"
              disabled={loading || !input.trim()}
              className="flex items-center gap-1.5 bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2.5 rounded-xl text-sm font-semibold disabled:opacity-40 transition-colors shrink-0 shadow"
            >
              <Send className="w-4 h-4" />
              <span>Send</span>
            </button>
          </form>

          <div className="flex items-center justify-between mt-2 text-[10px] text-gray-500">
            <span>Natural language instructions are converted into real project actions.</span>
            <span>Enterprise RBAC & organization isolation enforced.</span>
          </div>
        </div>
      </div>
    </div>
  );
}
