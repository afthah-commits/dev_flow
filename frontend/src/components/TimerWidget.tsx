import React, { useEffect, useState } from 'react';
import { timeApi } from '../lib/timeApi';
import { ActiveTimer } from '../types/time';
import { Play, Square, X } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';

export function TimerWidget() {
  const [timer, setTimer] = useState<ActiveTimer | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const location = useLocation();

  useEffect(() => {
    loadTimer();
  }, [location.pathname]); // Reload when navigating

  useEffect(() => {
    const handleStartTask = async (e: any) => {
      const { taskId, projectId, title } = e.detail;
      try {
        await timeApi.startTimer({ project_id: projectId, task_id: taskId, description: 'Working on: ' + title });
        loadTimer();
      } catch(err: any) {
        alert(err.response?.data?.detail || 'Failed to start timer');
      }
    };
    window.addEventListener('start_task_timer', handleStartTask);
    return () => window.removeEventListener('start_task_timer', handleStartTask);
  }, []);

  useEffect(() => {
    if (!timer) return;
    
    // Initial elapsed
    const started = new Date(timer.started_at).getTime();
    const now = new Date().getTime();
    setElapsed(Math.floor((now - started) / 1000));
    
    const interval = setInterval(() => {
      setElapsed((prev) => prev + 1);
    }, 1000);
    
    return () => clearInterval(interval);
  }, [timer]);

  const loadTimer = async () => {
    try {
      const data = await timeApi.getCurrentTimer();
      setTimer(data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleStop = async (e: React.MouseEvent) => {
    e.preventDefault();
    try {
      await timeApi.stopTimer();
      setTimer(null);
      // Optional: dispatch event so other components refresh
      window.dispatchEvent(new Event('timer_stopped'));
    } catch (e) {
      console.error(e);
    }
  };

  const handleDiscard = async (e: React.MouseEvent) => {
    e.preventDefault();
    try {
      await timeApi.discardTimer();
      setTimer(null);
    } catch (e) {
      console.error(e);
    }
  };

  if (!timer) return null;

  const formatTime = (secs: number) => {
    const h = Math.floor(secs / 3600);
    const m = Math.floor((secs % 3600) / 60);
    const s = secs % 60;
    if (h > 0) {
      return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
    }
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="fixed bottom-6 right-6 bg-gray-900 border border-blue-500 rounded-lg shadow-xl shadow-blue-900/20 p-3 flex items-center gap-4 z-50">
      <Link to="/time" className="flex items-center gap-3 group">
        <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></div>
        <div className="text-white font-mono font-medium text-lg min-w-[70px]">
          {formatTime(elapsed)}
        </div>
        <div className="text-xs text-gray-400 max-w-[150px] truncate hidden md:block">
          {timer.description || "Active Timer"}
        </div>
      </Link>
      
      <div className="flex items-center gap-2 border-l border-gray-700 pl-3">
        <button
          onClick={handleStop}
          className="p-1.5 rounded bg-gray-800 text-red-400 hover:bg-gray-700 hover:text-red-300"
          title="Stop Timer"
        >
          <Square size={16} fill="currentColor" />
        </button>
        <button
          onClick={handleDiscard}
          className="p-1.5 rounded bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white"
          title="Discard Timer"
        >
          <X size={16} />
        </button>
      </div>
    </div>
  );
}
