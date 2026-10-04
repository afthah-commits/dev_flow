import React from 'react';
import { LayoutDashboard, CheckSquare, MessageSquare, Book, FileText, Bot } from 'lucide-react';

export default function ClientDashboard() {
  return (
    <div className="flex h-screen bg-slate-50 text-slate-900 font-sans">
      <div className="w-64 bg-white border-r border-slate-200 flex flex-col">
        <div className="h-16 flex items-center px-6 border-b border-slate-200">
          <h1 className="font-bold text-xl text-slate-800">Client Portal</h1>
        </div>
        
        <div className="flex-1 py-6 px-3 space-y-1">
          <button className="w-full flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md bg-indigo-50 text-indigo-700">
            <LayoutDashboard className="w-5 h-5" /> Dashboard
          </button>
          <button className="w-full flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md text-slate-600 hover:bg-slate-50 hover:text-slate-900">
            <CheckSquare className="w-5 h-5" /> Projects & Tasks
          </button>
          <button className="w-full flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md text-slate-600 hover:bg-slate-50 hover:text-slate-900">
            <MessageSquare className="w-5 h-5" /> My Requests
          </button>
          <button className="w-full flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md text-slate-600 hover:bg-slate-50 hover:text-slate-900">
            <Book className="w-5 h-5" /> Knowledge Base
          </button>
        </div>
        
        <div className="p-4 border-t border-slate-200">
          <div className="bg-indigo-900 text-white p-4 rounded-lg shadow-sm">
            <div className="flex items-center gap-2 font-semibold mb-2">
              <Bot className="w-4 h-4 text-indigo-300" /> AI Assistant
            </div>
            <p className="text-xs text-indigo-200 leading-relaxed mb-3">
              Get an instant summary of your active projects and open requests.
            </p>
            <button className="w-full bg-indigo-500 hover:bg-indigo-600 text-white text-xs font-medium py-1.5 rounded">
              Generate Summary
            </button>
          </div>
        </div>
      </div>
      
      <div className="flex-1 overflow-auto bg-slate-50">
        <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-8">
          <h2 className="text-xl font-semibold text-slate-800">Welcome Back</h2>
          <div className="flex items-center gap-4">
            <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-700 font-bold text-sm">
              C
            </div>
          </div>
        </header>
        
        <main className="p-8 max-w-5xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
              <div className="text-sm font-medium text-slate-500 mb-1">Active Projects</div>
              <div className="text-3xl font-bold text-slate-900">2</div>
            </div>
            <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
              <div className="text-sm font-medium text-slate-500 mb-1">Open Requests</div>
              <div className="text-3xl font-bold text-slate-900">1</div>
            </div>
            <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
              <div className="text-sm font-medium text-slate-500 mb-1">Recent Updates</div>
              <div className="text-3xl font-bold text-slate-900">5</div>
            </div>
          </div>

          <h3 className="font-semibold text-lg text-slate-800 mb-4">Recent Activity</h3>
          <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
            <div className="p-4 border-b border-slate-100 flex items-start gap-4">
              <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
                <FileText className="w-5 h-5" />
              </div>
              <div>
                <div className="text-slate-900 font-medium">Weekly Report Published</div>
                <div className="text-sm text-slate-500">The engineering team published the weekly progress report for Alpha Project.</div>
              </div>
            </div>
            <div className="p-4 flex items-start gap-4">
              <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
                <CheckSquare className="w-5 h-5" />
              </div>
              <div>
                <div className="text-slate-900 font-medium">Task Completed</div>
                <div className="text-sm text-slate-500">"Update staging environment" was marked as done.</div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
