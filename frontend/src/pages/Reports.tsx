import React, { useEffect, useState } from 'react';
import { useOrganization } from '../contexts/OrganizationContext';
import { reportApi } from '../lib/reportApi';
import { Report, ReportType } from '../types/report';

export default function Reports() {
  const { currentOrganization } = useOrganization();
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (currentOrganization) {
      loadReports();
    }
  }, [currentOrganization]);

  const loadReports = async () => {
    if (!currentOrganization) return;
    try {
      const data = await reportApi.getReports(currentOrganization.id);
      setReports(data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!currentOrganization) return;
    try {
      await reportApi.createReport(currentOrganization.id, {
        name: 'New Overview Report',
        report_type: ReportType.PROJECT_OVERVIEW,
        configuration: {}
      });
      loadReports();
    } catch (error) {
      console.error(error);
    }
  };

  if (loading) return <div className="p-8">Loading reports...</div>;

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Reports</h1>
        <button 
          onClick={handleCreate}
          className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
        >
          Create Report
        </button>
      </div>

      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {reports.map(report => (
            <li key={report.id}>
              <div className="px-4 py-4 sm:px-6 hover:bg-gray-50 cursor-pointer">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-indigo-600 truncate">{report.name}</p>
                  <div className="ml-2 flex-shrink-0 flex">
                    <p className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                      {report.report_type}
                    </p>
                  </div>
                </div>
                <div className="mt-2 sm:flex sm:justify-between">
                  <div className="sm:flex">
                    <p className="flex items-center text-sm text-gray-500">
                      {report.description || 'No description'}
                    </p>
                  </div>
                  <div className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0">
                    <p>Created {new Date(report.created_at).toLocaleDateString()}</p>
                  </div>
                </div>
              </div>
            </li>
          ))}
          {reports.length === 0 && (
            <li className="px-4 py-8 text-center text-gray-500">
              No reports created yet.
            </li>
          )}
        </ul>
      </div>
    </div>
  );
}
