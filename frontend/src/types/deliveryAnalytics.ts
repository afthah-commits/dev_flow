export interface DeliveryMetrics {
  deployment_frequency: number;
  successful_deployment_rate: number;
  failed_deployment_rate: number;
  avg_deployment_duration_seconds: number;
  release_frequency: number;
  avg_release_cycle_time_days: number;
  pipeline_success_rate: number;
  rollback_frequency: number;
  avg_lead_time_days: number;
}

export interface DoraMetrics {
  deployment_frequency: string;
  lead_time_for_changes: string;
  change_failure_rate: string;
  mean_time_to_recovery: string;
}
