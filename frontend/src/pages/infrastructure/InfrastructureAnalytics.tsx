import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const data = [
  { name: 'Jan', count: 40 },
  { name: 'Feb', count: 30 },
  { name: 'Mar', count: 20 },
  { name: 'Apr', count: 27 },
  { name: 'May', count: 18 },
  { name: 'Jun', count: 23 },
  { name: 'Jul', count: 34 },
];

export default function InfrastructureAnalytics() {
  return (
    <div className="p-6">
      <h1 className="text-2xl text-white mb-4">Infrastructure Analytics</h1>
      <div className="h-64 w-full">
        <ResponsiveContainer>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="count" fill="#8884d8" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
