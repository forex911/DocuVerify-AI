// ==========================================
// DocuVerifyAI - Core Domain Types
// ==========================================

export type SeverityLevel = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';

export type ReviewStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'ACCEPTED_WITH_EXCEPTION';

export type DocumentType = 'invoice' | 'packing_list' | 'bill_of_lading' | 'unknown';

export type DocumentStatus = 'PENDING' | 'EXTRACTED' | 'FAILED' | 'VERIFIED' | 'REVIEW_REQUIRED';

export type WorkflowStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'ESCALATED';

// Field Source & Extracted Field
export interface ExtractedField {
  value: any;
  confidence: number;
  page_number: number;
  source_text: string;
  bounding_box?: [number, number, number, number] | null;
  is_ambiguous?: boolean;
}

export interface CanonicalItem {
  sku?: string | null;
  description: string;
  quantity: number | string;
  unit: string;
  unit_price?: number | string | null;
  line_total?: number | string | null;
  package_count?: number | null;
  gross_weight?: number | null;
  net_weight?: number | null;
  page_number?: number;
  source_text?: string;
}

export interface CanonicalDocument {
  document_id: string;
  document_type: DocumentType;
  order_reference?: ExtractedField | null;
  customer_name?: ExtractedField | null;
  customer_address?: ExtractedField | null;
  consignee?: ExtractedField | null;
  shipper?: ExtractedField | null;
  currency?: ExtractedField | null;
  subtotal?: ExtractedField | null;
  tax?: ExtractedField | null;
  freight?: ExtractedField | null;
  grand_total?: ExtractedField | null;
  destination?: ExtractedField | null;
  port_of_loading?: ExtractedField | null;
  port_of_discharge?: ExtractedField | null;
  package_count?: ExtractedField | null;
  gross_weight?: ExtractedField | null;
  net_weight?: ExtractedField | null;
  line_items: CanonicalItem[];
  missing_required_fields: string[];
  extraction_warnings: string[];
}

// Ingested Document
export interface DocumentItem {
  id: string;
  order_id?: string | null;
  group_id?: string | null;
  filename: string;
  original_filename: string;
  file_hash: string;
  file_size: number;
  mime_type: string;
  document_type: DocumentType;
  status: DocumentStatus;
  page_count: number;
  error_message?: string | null;
  created_at: string;
  updated_at?: string | null;
  canonical_document?: CanonicalDocument | null;
  requires_manual_extraction?: boolean;
  extraction_method?: string | null;
}

// Order Item & Order
export interface OrderItem {
  id?: string;
  sku: string;
  description: string;
  quantity: number;
  unit: string;
  unit_price: number;
  line_total: number;
}

export interface Order {
  id: string;
  order_number: string;
  customer_name: string;
  currency: string;
  quantity: number;
  unit_price: number;
  subtotal: number;
  tax: number;
  freight: number;
  grand_total: number;
  destination: string;
  package_count?: number | null;
  notes?: string | null;
  is_authoritative: boolean;
  version: number;
  created_at: string;
  updated_at?: string | null;
  items: OrderItem[];
}

// Discrepancy & Evidence
export interface Discrepancy {
  id: string;
  workflow_id?: string | null;
  document_id: string;
  order_id?: string | null;
  rule_id: string;
  field_name: string;
  severity: SeverityLevel;
  description: string;
  expected_value?: string | null;
  actual_value?: string | null;
  source_text?: string | null;
  page_number?: number | null;
  bounding_box?: [number, number, number, number] | null;
  explanation?: string | null;
  review_status: ReviewStatus;
  review_comment?: string | null;
  reviewer_id?: string | null;
  reviewed_at?: string | null;
  created_at: string;
}

// Workflow & Agent Trace
export interface AgentTrace {
  id: string;
  workflow_id: string;
  agent_name: string;
  step_name: string;
  status: string;
  input_summary?: string | null;
  output_summary?: string | null;
  error_message?: string | null;
  created_at: string;
}

export interface WorkflowSummary {
  workflow_id: string;
  target_id?: string | null;
  status: WorkflowStatus;
  details?: Record<string, any> | null;
  error?: string | null;
  created_at: string;
  completed_at?: string | null;
}

export interface WorkflowDetail {
  workflow_id: string;
  workflow_status: WorkflowStatus;
  order_id?: string | null;
  document_ids: string[];
  requires_human_review: boolean;
  discrepancies: Discrepancy[];
  final_investigation_report?: {
    summary?: string;
    total_discrepancies?: number;
    critical_count?: number;
    high_count?: number;
    recommended_action?: string;
    suggested_questions?: string[];
    risk_level?: string;
    confidence_assessment?: string;
    [key: string]: any;
  } | null;
  agent_logs_count: number;
}

// Audit Log
export interface AuditLogEntry {
  id: string;
  event_type: string;
  entity_type: string;
  entity_id: string;
  actor_id: string;
  details: Record<string, any>;
  created_at: string;
}

// Dashboard
export interface DashboardSummary {
  total_documents: number;
  documents_awaiting_review: number;
  open_discrepancies: number;
  resolved_discrepancies: number;
  critical_discrepancies: number;
  high_discrepancies: number;
  medium_discrepancies: number;
  low_discrepancies: number;
  total_orders: number;
  document_type_breakdown: Record<string, number>;
  recent_activity: AuditLogEntry[];
}

