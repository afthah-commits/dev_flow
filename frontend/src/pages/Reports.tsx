import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useOrganization } from '../contexts/OrganizationContext';
import { reportApi } from '../lib/reportApi';
import { Report, ReportType } from '../types/report';
import { FileText, Plus, AlertCircle, RefreshCw, Calendar, CheckCircle2, BarChart3, Clock, Users, ArrowUpRight } from 'lucide-react';

export default function Reports() {
  const { currentOrganization } = useOrganization();
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Create report modal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newReportName, setNewReportName] = useState('');
  const [newReportType, setNewReportType] = useState<ReportType>(ReportType.PROJECT_OVERVIEW);
  const [newReportDesc, setNewReportDesc] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (currentOrganization) {
      loadReports();
    }
  }, [currentOrganization]);

  const loadReports = async () => {
    if (!currentOrganization) return;
    setLoading(true);
    setError(null);
    try {
      const data = await reportApi.getReports(currentOrganization.id);
      const list = Array.isArray(data) ? data : ((data as any)?.items || []);
      setReports(list);
    } catch (err: any) {
      console.error('Failed to load reports:', err);
      const status = err?.response?.status;
      if (status === 403) {
        setError('Reports access is restricted to organization managers and administrators.');
      } else {
        setError(err?.response?.data?.detail || err.message || 'Failed to load organization reports.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCreateReport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentOrganization || !newReportName.trim()) return;

    setIsSubmitting(true);
    try {
      await reportApi.createReport(currentOrganization.id, {
        name: newReportName.trim(),
        report_type: newReportType,
        description: newReportDesc.trim() || undefined,
        configuration: {},
      });
      setShowCreateModal(false);
      setNewReportName('');
      setNewReportDesc('');
      setNewReportType(ReportType.PROJECT_OVERVIEW);
      await loadReports();
    } catch (err: any) {
      console.error('Failed to create report:', err);
      alert(err?.response?.data?.detail || 'Failed to create report. Ensure you have proper permissions.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const getReportTypeBadge = (type: ReportType) => {
    switch (type) {
      case ReportType.PROJECT_OVERVIEW:
        return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
      case ReportType.SPRINT_REPORT:
        return 'bg-purple-500/10 text-purple-400 border-purple-500/20';
      case ReportType.PRODUCTIVITY:
      case ReportType.TEAM_WORKLOAD:
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
      case ReportType.EXECUTIVE_SUMMARY:
        return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      default:
        return 'bg-gray-800 text-gray-300 border-gray-700';
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Top Header & Navigation Sub-tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-gray-800">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white flex items-center gap-2.5">
            <BarChart3 className="w-7 h-7 text-indigo-400" />
            Intelligence & Reports
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Generate and review cross-project executive summaries and daily engineering reports.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => loadReports()}
            className="p-2 text-gray-400 hover:text-white bg-gray-900 border border-gray-800 rounded-lg hover:bg-gray-800 transition-colors"
            title="Refresh reports"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium shadow-sm transition-colors"
          >
            <Plus className="w-4 h-4" />
            Create Report
          </button>
        </div>
      </div>

      {/* Reports Navigation Tabs */}
      <div className="flex flex-wrap items-center gap-2 text-sm border-b border-gray-800 pb-3">
        <Link
          to="/reports"
          className="px-3 py-1.5 rounded-md font-medium bg-indigo-600/20 text-indigo-300 border border-indigo-500/30"
        >
          Executive & Overview Reports
        </Link>
        <Link
          to="/daily-reports"
          className="px-3 py-1.5 rounded-md font-medium text-gray-400 hover:text-white hover:bg-gray-900 transition-colors"
        >
          My Daily Reports
        </Link>
        <Link
          to="/daily-reports/team"
          className="px-3 py-1.5 rounded-md font-medium text-gray-400 hover:text-white hover:bg-gray-900 transition-colors"
        >
          Team Reports
        </Link>
        <Link
          to="/daily-reports/weekly"
          className="px-3 py-1.5 rounded-md font-medium text-gray-400 hover:text-white hover:bg-gray-900 transition-colors"
        >
          Weekly Summary
        </Link>
        <Link
          to="/daily-reports/blockers"
          className="px-3 py-1.5 rounded-md font-medium text-gray-400 hover:text-white hover:bg-gray-900 transition-colors"
        >
          Blockers Tracker
        </Link>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-12 text-center text-gray-400 space-y-3">
          <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-sm font-medium text-gray-300">Loading organization reports...</p>
        </div>
      )}

      {/* Error / Permission State */}
      {!loading && error && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center space-y-4">
          <div className="w-12 h-12 rounded-full bg-amber-500/10 text-amber-400 flex items-center justify-center mx-auto">
            <AlertCircle className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Notice</h3>
            <p className="text-sm text-gray-400 max-w-md mx-auto mt-1">{error}</p>
          </div>
          <div className="flex items-center justify-center gap-3 pt-2">
            <button
              onClick={() => loadReports()}
              className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white text-sm font-medium rounded-lg transition-colors"
            >
              Retry
            </button>
            <Link
              to="/daily-reports"
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-lg transition-colors"
            >
              Go to Daily Reports
            </Link>
          </div>
        </div>
      )}

      {/* Reports List */}
      {!loading && !error && (
        <div className="space-y-4">
          {reports.length === 0 ? (
            <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-12 text-center space-y-4">
              <div className="w-14 h-14 rounded-full bg-indigo-500/10 text-indigo-400 flex items-center justify-center mx-auto">
                <FileText className="w-7 h-7" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white">No reports created yet</h3>
                <p className="text-sm text-gray-400 max-w-sm mx-auto mt-1">
                  Create executive overviews, delivery tracking reports, or sprint summaries for your workspace.
                </p>
              </div>
              <button
                onClick={() => setShowCreateModal(true)}
                className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium transition-colors"
              >
                <Plus className="w-4 h-4" />
                Create your first report
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {reports.map((report) => (
                <div
                  key={report.id}
                  className="bg-gray-900 border border-gray-800 hover:border-gray-700 rounded-xl p-5 flex flex-col justify-between transition-colors shadow-sm"
                >
                  <div className="space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="font-semibold text-white text-base truncate" title={report.name}>
                        {report.name}
                      </h3>
                      <span className={`px-2 py-0.5 text-xs font-medium rounded-full border shrink-0 ${getReportTypeBadge(report.report_type)}`}>
                        {report.report_type.replace('_', ' ')}
                      </span>
                    </div>
                    <p className="text-xs text-gray-400 line-clamp-2">
                      {report.description || 'No description provided.'}
                    </p>
                  </div>

                  <div className="pt-4 mt-3 border-t border-gray-800/80 flex items-center justify-between text-xs text-gray-500">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3.5 h-3.5" />
                      {new Date(report.created_at).toLocaleDateString()}
                    </span>
                    <button
                      onClick={() => alert(`Report ID: ${report.id}\nType: ${report.report_type}\nStatus: Active`)}
                      className="text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1 transition-colors"
                    >
                      View Details
                      <ArrowUpRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Modal for Creating a New Report */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="bg-gray-900 border border-gray-800 rounded-xl max-w-md w-full p-6 shadow-2xl space-y-5 animate-in fade-in duration-200">
            <div className="flex items-center justify-between pb-3 border-b border-gray-800">
              <h3 className="text-lg font-semibold text-white">Create New Report</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-gray-400 hover:text-white text-lg font-bold p-1"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateReport} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1">
                  Report Name <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Q4 Executive Sprint Summary"
                  value={newReportName}
                  onChange={(e) => setNewReportName(e.target.value)}
                  className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1">
                  Report Type
                </label>
                <select
                  value={newReportType}
                  onChange={(e) => setNewReportType(e.target.value as ReportType)}
                  className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value={ReportType.PROJECT_OVERVIEW}>Project Overview</option>
                  <option value={ReportType.SPRINT_REPORT}>Sprint Report</option>
                  <option value={ReportType.PRODUCTIVITY}>Productivity & Velocity</option>
                  <option value={ReportType.TEAM_WORKLOAD}>Team Workload</option>
                  <option value={ReportType.TIME_TRACKING}>Time Tracking</option>
                  <option value={ReportType.GITHUB_DELIVERY}>GitHub Delivery</option>
                  <option value={ReportType.RELEASE_DELIVERY}>Release Delivery</option>
                  <option value={ReportType.EXECUTIVE_SUMMARY}>Executive Summary</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1">
                  Description (Optional)
                </label>
                <textarea
                  rows={3}
                  placeholder="Briefly describe what this report covers..."
                  value={newReportDesc}
                  onChange={(e) => setNewReportDesc(e.target.value)}
                  className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500 resize-none"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-gray-800">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-400 hover:text-white bg-gray-800 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || !newReportName.trim()}
                  className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 rounded-lg transition-colors flex items-center gap-1.5"
                >
                  {isSubmitting ? (
                    <>
                      <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      Creating...
                    </>
                  ) : (
                    'Create Report'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
