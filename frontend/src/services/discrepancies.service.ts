import { apiClient } from './api';
import { Discrepancy, ReviewStatus } from '../types';

export interface DiscrepancyListParams {
  document_id?: string;
  order_id?: string;
  severity?: string;
  review_status?: string;
  rule_id?: string;
}

export interface ReviewDecisionPayload {
  action: ReviewStatus;
  comment: string;
  reviewer_id?: string;
}

export const discrepanciesService = {
  getDiscrepancies: async (params?: DiscrepancyListParams): Promise<Discrepancy[]> => {
    const res = await apiClient.get<Discrepancy[]>('/discrepancies', { params });
    return res.data;
  },

  getDiscrepancy: async (discrepancyId: string): Promise<Discrepancy> => {
    const res = await apiClient.get<Discrepancy>(`/discrepancies/${discrepancyId}`);
    return res.data;
  },

  submitDecision: async (discrepancyId: string, payload: ReviewDecisionPayload) => {
    const res = await apiClient.post(`/discrepancies/${discrepancyId}/decision`, payload);
    return res.data;
  },
};

