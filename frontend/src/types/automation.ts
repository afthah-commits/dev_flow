export interface AutomationCondition {
    field?: string;
    operator?: string;
    value?: any;
    logical_operator?: 'ALL' | 'ANY' | 'NOT';
    conditions?: AutomationCondition[];
}

export interface AutomationAction {
    type: string;
    [key: string]: any;
}

export interface Automation {
    id: string;
    organization_id: string;
    created_by: string;
    name: string;
    description?: string;
    enabled: boolean;
    trigger_type: string;
    configuration?: any;
    conditions?: AutomationCondition;
    actions: AutomationAction[];
    execution_mode: string;
    created_at: string;
    updated_at?: string;
}

export interface AutomationExecution {
    id: string;
    automation_id: string;
    organization_id: string;
    trigger_event: string;
    status: string;
    started_at: string;
    completed_at?: string;
    duration_ms?: number;
    error_message?: string;
}
