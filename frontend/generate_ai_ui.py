import os

content = """import React, { useEffect, useState, useRef } from 'react';
import { aiApi } from '../lib/aiApi';
import { AIConversation, AIMessage, TaskSuggestion } from '../types/ai';
import { Project } from '../types/project';
import { taskApi } from '../lib/taskApi';
import { TaskStatus } from '../types/task';

interface Props {
  project: Project;
}

export function ProjectAI({ project }: Props) {
  const [conversations, setConversations] = useState<AIConversation[]>([]);
  const [activeConv, setActiveConv] = useState<AIConversation | null>(null);
  const [messages, setMessages] = useState<AIMessage[]>([]);
  
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // For Task Generation
  const [proposedTask, setProposedTask] = useState<TaskSuggestion | null>(null);

  useEffect(() => {
    loadConversations();
  }, [project.id]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const loadConversations = async () => {
    try {
      const res = await aiApi.listConversations(project.id);
      setConversations(res);
      if (res.length > 0 && !activeConv) {
        loadConversation(res[0].id);
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
      const res = await aiApi.createConversation("New Conversation", project.id);
      setConversations([res, ...conversations]);
      setActiveConv(res);
      setMessages([]);
    } catch (e) {
      setError("Failed to create conversation");
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async (text: string) => {
    if (!text.trim()) return;
    
    let convId = activeConv?.id;
    if (!convId) {
      try {
        const newC = await aiApi.createConversation(text.substring(0, 30) + '...', project.id);
        setConversations([newC, ...conversations]);
        setActiveConv(newC);
        convId = newC.id;
      } catch (e) {
        setError("Failed to initialize conversation");
        return;
      }
    }

    const tempMsg: AIMessage = { id: 'temp', role: 'user', content: text, created_at: new Date().toISOString() };
    setMessages(prev => [...prev, tempMsg]);
    setInput('');
    setLoading(true);
    setError(null);

    try {
      const aiReply = await aiApi.sendMessage(convId, text);
      setMessages(prev => {
        // replace temp with real? We just reload from server or append directly.
        // Actually, let's just append the real reply and keep the temp as is (it's close enough visually)
        return [...prev, aiReply];
      });
    } catch (e: any) {
      setError(e.response?.data?.detail || "AI Provider failed.");
      setMessages(prev => prev.filter(m => m.id !== 'temp')); // rollback
    } finally {
      setLoading(false);
    }
  };

  const handleQuickAction = async (action: string) => {
    if (action === 'summary') {
      handleSend("Give me a concise project summary based on current tasks and GitHub activity.");
    } else if (action === 'next') {
      handleSend("What should I work on next?");
    } else if (action === 'readme') {
      handleSend("Generate a draft README.md for this project.");
    } else if (action === 'task') {
      const instruction = prompt("Describe the task you want to generate:");
      if (!instruction) return;
      
      setLoading(true);
      setError(null);
      try {
        const res = await aiApi.suggestTask(project.id, instruction);
        if (res.structured_data) {
          setProposedTask(res.structured_data as TaskSuggestion);
        }
      } catch (e: any) {
         setError(e.response?.data?.detail || "Failed to generate task.");
      } finally {
         setLoading(false);
      }
    }
  };

  const handleCreateTask = async () => {
    if (!proposedTask) return;
    try {
      await taskApi.createTask(project.id, {
        title: proposedTask.title,
        description: proposedTask.description,
        status: TaskStatus.TODO,
        priority: proposedTask.priority as any
      });
      setProposedTask(null);
      alert("Task created successfully!");
    } catch (e) {
      alert("Failed to create task");
    }
  };

  return (
    <div className="flex flex-col md:flex-row h-[600px] border border-gray-800 rounded-lg overflow-hidden bg-gray-900">
      {/* Sidebar */}
      <div className="w-full md:w-64 border-r border-gray-800 flex flex-col bg-gray-950">
        <div className="p-4 border-b border-gray-800">
          <button 
            onClick={handleNewConversation}
            className="w-full py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm font-medium transition-colors"
          >
            + New Chat
          </button>
        </div>
        <div className="flex-1 overflow-y-auto">
          {conversations.map(c => (
            <button
              key={c.id}
              onClick={() => loadConversation(c.id)}
              className={`w-full text-left px-4 py-3 text-sm truncate border-b border-gray-800/50 transition-colors ${
                activeConv?.id === c.id ? 'bg-gray-800 text-white' : 'text-gray-400 hover:bg-gray-900'
              }`}
            >
              {c.title}
            </button>
          ))}
        </div>
      </div>

      {/* Main Chat */}
      <div className="flex-1 flex flex-col relative">
        {/* Quick Actions Header */}
        <div className="p-3 border-b border-gray-800 bg-gray-900/50 flex flex-wrap gap-2">
          <button onClick={() => handleQuickAction('summary')} className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 text-xs rounded-full border border-gray-700 transition-colors">
            Project Summary
          </button>
          <button onClick={() => handleQuickAction('next')} className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 text-xs rounded-full border border-gray-700 transition-colors">
            What's Next?
          </button>
          <button onClick={() => handleQuickAction('readme')} className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 text-xs rounded-full border border-gray-700 transition-colors">
            Generate README
          </button>
          <button onClick={() => handleQuickAction('task')} className="px-3 py-1.5 bg-blue-900/40 hover:bg-blue-900/60 text-blue-300 text-xs rounded-full border border-blue-800 transition-colors">
            Generate Task (AI)
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {messages.length === 0 && !loading && (
            <div className="h-full flex items-center justify-center text-gray-500 flex-col">
              <span className="text-4xl mb-4">🤖</span>
              <p>I am DevFlow AI. How can I help with {project.name}?</p>
            </div>
          )}
          
          {messages.map((m, idx) => (
            <div key={idx} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] rounded-2xl px-5 py-3 ${
                m.role === 'user' 
                  ? 'bg-blue-600 text-white rounded-br-none' 
                  : 'bg-gray-800 text-gray-200 rounded-bl-none border border-gray-700'
              }`}>
                <div className="text-xs font-semibold mb-1 opacity-70 uppercase tracking-wider">
                  {m.role === 'user' ? 'You' : 'AI Assistant'}
                </div>
                <div className="whitespace-pre-wrap text-sm leading-relaxed">{m.content}</div>
              </div>
            </div>
          ))}
          
          {loading && (
            <div className="flex justify-start">
              <div className="bg-gray-800 text-gray-400 rounded-2xl rounded-bl-none px-5 py-3 border border-gray-700 flex items-center space-x-2">
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-100"></div>
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-200"></div>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Error overlay */}
        {error && (
          <div className="absolute bottom-20 left-4 right-4 bg-red-900/90 text-red-200 p-3 rounded text-sm border border-red-700 shadow-lg">
            {error}
          </div>
        )}

        {/* Task Preview Overlay */}
        {proposedTask && (
          <div className="absolute inset-0 bg-gray-900/95 z-10 flex items-center justify-center p-6">
            <div className="bg-gray-800 border border-gray-700 rounded-xl p-6 max-w-md w-full shadow-2xl">
              <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                <span>✨</span> AI Task Suggestion
              </h3>
              <div className="space-y-4 mb-6">
                <div>
                  <label className="text-xs text-gray-400 uppercase tracking-wider">Title</label>
                  <input value={proposedTask.title} onChange={e => setProposedTask({...proposedTask, title: e.target.value})} className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-white mt-1" />
                </div>
                <div>
                  <label className="text-xs text-gray-400 uppercase tracking-wider">Description</label>
                  <textarea value={proposedTask.description} onChange={e => setProposedTask({...proposedTask, description: e.target.value})} className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-white mt-1 h-24" />
                </div>
                <div className="flex gap-4">
                  <div className="flex-1">
                    <label className="text-xs text-gray-400 uppercase tracking-wider">Priority</label>
                    <select value={proposedTask.priority} onChange={e => setProposedTask({...proposedTask, priority: e.target.value})} className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-white mt-1">
                      <option value="LOW">Low</option>
                      <option value="MEDIUM">Medium</option>
                      <option value="HIGH">High</option>
                      <option value="CRITICAL">Critical</option>
                    </select>
                  </div>
                </div>
              </div>
              <div className="flex justify-end space-x-3">
                <button onClick={() => setProposedTask(null)} className="px-4 py-2 text-gray-400 hover:text-white transition-colors">Cancel</button>
                <button onClick={handleCreateTask} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium transition-colors">Create Task</button>
              </div>
            </div>
          </div>
        )}

        {/* Input Area */}
        <div className="p-4 border-t border-gray-800 bg-gray-950">
          <div className="flex space-x-2">
            <input 
              type="text" 
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSend(input)}
              placeholder="Ask the AI assistant..." 
              disabled={loading}
              className="flex-1 bg-gray-900 border border-gray-800 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-blue-500 disabled:opacity-50 transition-colors"
            />
            <button 
              onClick={() => handleSend(input)}
              disabled={loading || !input.trim()}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium disabled:opacity-50 transition-colors"
            >
              Send
            </button>
          </div>
          <div className="text-center mt-2 text-[10px] text-gray-500">
            AI can make mistakes. Verify important information.
          </div>
        </div>
      </div>
    </div>
  );
}
"""
with open("c:/personal_projects/devflow/frontend/src/components/ProjectAI.tsx", "w", encoding="utf-8") as f: f.write(content)

print("ProjectAI created")
