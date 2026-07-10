import type { ReportType, ReportFormat } from '../utils/constants';

export interface GenerateReportRequest {
  type: ReportType;
  format: ReportFormat;
  parameters: ReportParameters;
}

export interface ReportParameters {
  alert_id?: string;
  actor_id?: string;
  date_from?: string;
  date_to?: string;
  include_evidence?: boolean;
  include_blockchain_seal?: boolean;
  query?: string;
}

export interface GenerateReportResponse {
  report_id: string;
  status: string;
  estimated_completion: string;
}

export interface Report {
  id: string;
  type: ReportType;
  format: ReportFormat;
  status: 'generating' | 'completed' | 'failed';
  file_size_bytes: number | null;
  download_url?: string;
  url_expires_at?: string;
  created_at: string;
  expires_at?: string;
  blockchain_tx?: string | null;
}

export interface ReportDetail extends Report {
  download_url: string;
  url_expires_at: string;
}
