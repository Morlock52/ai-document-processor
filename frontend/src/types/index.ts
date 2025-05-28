export interface Document {
  id: number;
  filename: string;
  original_filename: string;
  upload_path: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  page_count: number | null;
  extracted_data: unknown | null;
  processing_metadata: ProcessingMetadata | null;
  created_at: string;
  updated_at: string;
  progress: number;
}

export interface ProcessingMetadata {
  processing_time?: number;
  error_message?: string;
  confidence_scores?: Record<string, number>;
  page_statuses?: Record<number, string>;
}

export interface DocumentListResponse {
  documents: Document[];
  total: number;
  skip: number;
  limit: number;
  items?: Document[]; // Alternative property name used in some responses
}

export interface DocumentUploadResponse {
  id: number;
  filename: string;
  message: string;
}

export interface ProcessingStatus {
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  current_page?: number;
  total_pages?: number;
  message?: string;
}

export interface Schema {
  id?: string;
  name: string;
  description?: string;
  fields: SchemaField[];
}

export interface SchemaField {
  name: string;
  type: 'text' | 'number' | 'date' | 'boolean' | 'array';
  description?: string;
  required?: boolean;
  multiple?: boolean;
}