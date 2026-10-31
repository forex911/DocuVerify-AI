import { apiClient } from './api';
import { WorkflowDetail, WorkflowSummary, AgentTrace } from '../types';

export interface InitiateWorkflowPayload {
  document_ids: string[];
  order_id?: string;
  run_async?: boolean;
}

export const workflowsService = {
  initiateWorkflow: async (payload: InitiateWorkflowPayload) => {
    const res = await apiClient.post<{
      workflow_id: string;
      workflow_status: string;
      order_id?: string;
      document_ids: string[];
      message: string;
    }>('/workflows/verify', payload);
    return res.data;
  },

  getWorkflows: async (status?: string, limit = 50): Promise<WorkflowSummary[]> => {
    const res = await apiClient.get<WorkflowSummary[]>('/workflows', {
      params: { status, limit },
    });
    return res.data;
  },

  getWorkflow: async (workflowId: string): Promise<WorkflowDetail> => {
    const res = await apiClient.get<WorkflowDetail>(`/workflows/${workflowId}`);
    return res.data;
  },

  getWorkflowAgents: async (
    workflowId: string
  ): Promise<{ workflow_id: string; agent_execution_count: number; agent_traces: AgentTrace[] }> => {
    const res = await apiClient.get(`/workflows/${workflowId}/agents`);
    return res.data;
  },

  runDeterministicVerification: async (payload: {
    order_id: string;
    document_ids?: string[];
    group_id?: string;
  }) => {
    const res = await apiClient.post('/verification/run', payload);
    return res.data;
  },
};

