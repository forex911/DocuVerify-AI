import { apiClient } from './api';
import { AuditLogEntry } from '../types';

export interface AuditListParams {
  entity_type?: string;
  entity_id?: string;
  event_type?: string;
  limit?: number;
}

export const auditService = {
  getAuditLogs: async (params?: AuditListParams): Promise<AuditLogEntry[]> => {
    const res = await apiClient.get<AuditLogEntry[]>('/audit', { params });
    return res.data;
  },
};

