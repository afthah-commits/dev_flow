import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import DeliveryAnalytics from './DeliveryAnalytics';
import { deliveryAnalyticsApi } from '../lib/deliveryAnalyticsApi';

vi.mock('../lib/deliveryAnalyticsApi');

describe('DeliveryAnalytics Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    vi.mocked(deliveryAnalyticsApi.getDeliveryMetrics).mockReturnValue(new Promise(() => {}));
    vi.mocked(deliveryAnalyticsApi.getDoraMetrics).mockReturnValue(new Promise(() => {}));

    render(
      <BrowserRouter>
        <DeliveryAnalytics />
      </BrowserRouter>
    );

    expect(screen.getByText(/Loading delivery telemetry/i)).toBeInTheDocument();
  });

  it('renders loaded delivery and DORA metrics', async () => {
    vi.mocked(deliveryAnalyticsApi.getDeliveryMetrics).mockResolvedValue({
      release_frequency: 4,
      avg_release_cycle_time_days: 3.5,
      deployment_frequency: 12,
      pipeline_success_rate: 98.5,
      successful_deployment_rate: 96.0,
      failed_deployment_rate: 4.0,
      rollback_frequency: 1,
      avg_lead_time_days: 2.1,
      avg_deployment_duration_seconds: 180
    });
    vi.mocked(deliveryAnalyticsApi.getDoraMetrics).mockResolvedValue({
      deployment_frequency: 'Daily',
      lead_time_for_changes: '2 days',
      change_failure_rate: '3%',
      mean_time_to_recovery: '30 mins'
    });

    render(
      <BrowserRouter>
        <DeliveryAnalytics />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Engineering Delivery Metrics')).toBeInTheDocument();
      expect(screen.getByText('3.5 days')).toBeInTheDocument();
      expect(screen.getByText('98.5%')).toBeInTheDocument();
      expect(screen.getByText('Daily')).toBeInTheDocument();
      expect(screen.getByText('30 mins')).toBeInTheDocument();
    });
  });

  it('handles API rejection gracefully without white-screen or returning null', async () => {
    vi.mocked(deliveryAnalyticsApi.getDeliveryMetrics).mockRejectedValue(new Error('500 Internal Server Error'));
    vi.mocked(deliveryAnalyticsApi.getDoraMetrics).mockRejectedValue(new Error('500 Internal Server Error'));

    render(
      <BrowserRouter>
        <DeliveryAnalytics />
      </BrowserRouter>
    );

    await waitFor(() => {
      // Must not crash or return null
      expect(screen.getByText(/Showing baseline metrics/i)).toBeInTheDocument();
      expect(screen.getByText('Pipeline & Cycle Time')).toBeInTheDocument();
      expect(screen.getByText('DORA Metrics')).toBeInTheDocument();
    });
  });
});
