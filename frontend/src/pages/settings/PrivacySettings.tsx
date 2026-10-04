import React, { useEffect, useState } from 'react';
import { privacyApi } from '../../lib/governanceApi';

export default function PrivacySettings() {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    privacyApi.getMyData().then(setData).catch(console.error);
  }, []);

  const handleExport = async () => {
    try {
      await privacyApi.requestExport();
      alert("Data export requested.");
    } catch (e) {
      console.error(e);
    }
  };

  const handleDelete = async () => {
    if (confirm("Are you sure you want to request account deletion? This action cannot be easily undone.")) {
      try {
        await privacyApi.requestDeletion();
        alert("Account deletion requested.");
      } catch (e) {
        console.error(e);
      }
    }
  };

  if (!data) return <div className="p-8">Loading...</div>;

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Privacy & Data Management</h1>
      
      <div className="bg-white shadow sm:rounded-lg mb-8">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">Your Data</h3>
          <div className="mt-2 text-sm text-gray-500">
            <p>We collect the following data to provide our services:</p>
            <ul className="list-disc pl-5 mt-2">
              {data.data_collected?.map((item: string, i: number) => <li key={i}>{item}</li>)}
            </ul>
          </div>
          <div className="mt-5">
            <button
              onClick={handleExport}
              className="inline-flex items-center justify-center px-4 py-2 border border-transparent font-medium rounded-md text-indigo-700 bg-indigo-100 hover:bg-indigo-200 sm:text-sm"
            >
              Request Data Export
            </button>
          </div>
        </div>
      </div>

      <div className="bg-red-50 shadow sm:rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-red-800">Danger Zone</h3>
          <div className="mt-2 text-sm text-red-700">
            <p>Once you delete your account, there is no going back. Please be certain.</p>
          </div>
          <div className="mt-5">
            <button
              onClick={handleDelete}
              className="inline-flex items-center justify-center px-4 py-2 border border-transparent font-medium rounded-md text-white bg-red-600 hover:bg-red-700 sm:text-sm"
            >
              Request Account Deletion
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
