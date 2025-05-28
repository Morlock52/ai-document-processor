import axios, { AxiosError, AxiosResponse, AxiosRequestConfig } from 'axios';
import type { DocumentListResponse, DocumentUploadResponse, ProcessingStatus } from '@/types';

// Use appropriate URL based on environment
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8005/api/v1';

// 🏥 Enhanced error types for better error handling and user feedback
export interface ApiError {
  message: string;
  code?: string;
  status?: number;
  timestamp?: string;
  requestId?: string;
  details?: Record<string, unknown>;
  retryable?: boolean;
  userMessage?: string;
}

export interface RetryConfig {
  maxRetries: number;
  retryDelay: number;
  retryCondition?: (error: AxiosError) => boolean;
}

// 🔧 Enhanced API client with comprehensive error handling and retry logic
class EnhancedApiClient {
  private axiosInstance;
  private requestTimeout = 30000; // 30 seconds default timeout
  private defaultRetryConfig: RetryConfig = {
    maxRetries: 3,
    retryDelay: 1000,
    retryCondition: (error: AxiosError) => {
      // Retry on network errors, timeouts, or 5xx status codes
      return !error.response ||
             error.code === 'ECONNABORTED' ||
             (error.response.status >= 500 && error.response.status < 600);
    }
  };

  constructor() {
    this.axiosInstance = axios.create({
      baseURL: API_BASE_URL,
      timeout: this.requestTimeout,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // 📊 Request interceptor for logging and monitoring
    this.axiosInstance.interceptors.request.use(
      (config) => {
        const requestId = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        (config as { metadata?: { startTime: number; requestId: string } }).metadata = { startTime: Date.now(), requestId };
        config.headers['X-Request-ID'] = requestId;

        if (process.env.NODE_ENV === 'development') {
          console.log(`🚀 API_REQUEST: ${config.method?.toUpperCase()} ${config.url}`, {
            requestId,
            params: config.params,
            data: config.data && config.data instanceof FormData ? '[FormData]' : config.data
          });
        }

        return config;
      },
      (error) => {
        console.error('❌ API_REQUEST_ERROR:', error);
        return Promise.reject(this.enhanceError(error));
      }
    );

    // 📊 Response interceptor for logging and error enhancement
    this.axiosInstance.interceptors.response.use(
      (response: AxiosResponse<unknown>) => {
        const config = response.config as AxiosRequestConfig & { metadata?: { startTime: number; requestId: string } };
        const duration = config.metadata ? Date.now() - config.metadata.startTime : 0;

        if (process.env.NODE_ENV === 'development') {
          console.log(`✅ API_RESPONSE: ${config.method?.toUpperCase()} ${config.url}`, {
            status: response.status,
            duration: `${duration}ms`,
            requestId: config.metadata?.requestId,
            dataSize: response.data ? JSON.stringify(response.data).length : 0
          });
        }

        return response;
      },
      (error: AxiosError) => {
        const config = error.config as AxiosRequestConfig & { metadata?: { startTime: number; requestId: string } };
        const duration = config?.metadata ? Date.now() - config.metadata.startTime : 0;

        console.error(`❌ API_ERROR: ${config?.method?.toUpperCase()} ${config?.url}`, {
          status: error.response?.status,
          duration: `${duration}ms`,
          requestId: config?.metadata?.requestId,
          message: error.message,
          code: error.code
        });

        return Promise.reject(this.enhanceError(error));
      }
    );
  }

  private enhanceError(error: AxiosError): ApiError {
    /**
     * 🔍 Enhanced error processing with user-friendly messages
     * Converts technical axios errors into structured, actionable error information
     */
    const config = error.config as AxiosRequestConfig & { metadata?: { requestId: string } };
    const requestId = config?.metadata?.requestId || 'unknown';

    // Determine if error is retryable
    const retryable = this.defaultRetryConfig.retryCondition!(error);

    // Extract error details from response
    const responseData = error.response?.data as { detail?: string; message?: string };
    const errorDetails = responseData?.detail || responseData?.message || error.message;

    // Create user-friendly error messages
    let userMessage = 'An unexpected error occurred. Please try again.';
    let technicalMessage = error.message;

    if (error.code === 'ECONNABORTED') {
      userMessage = 'Request timed out. Please check your internet connection and try again.';
      technicalMessage = `Request timeout after ${this.requestTimeout}ms`;
    } else if (error.code === 'ERR_NETWORK') {
      userMessage = 'Network error. Please check your internet connection.';
      technicalMessage = 'Network connection failed';
    } else if (error.response?.status === 400) {
      userMessage = 'Invalid request. Please check your input and try again.';
      technicalMessage = errorDetails || 'Bad request';
    } else if (error.response?.status === 401) {
      userMessage = 'Authentication required. Please refresh the page.';
      technicalMessage = 'Unauthorized access';
    } else if (error.response?.status === 403) {
      userMessage = 'Access denied. You don\'t have permission for this action.';
      technicalMessage = 'Forbidden access';
    } else if (error.response?.status === 404) {
      userMessage = 'Resource not found. The item may have been deleted.';
      technicalMessage = 'Resource not found';
    } else if (error.response?.status === 413) {
      userMessage = 'File too large. Please use a smaller file.';
      technicalMessage = 'Request entity too large';
    } else if (error.response?.status === 422) {
      userMessage = 'Invalid data format. Please check your input.';
      technicalMessage = errorDetails || 'Validation error';
    } else if (error.response?.status === 429) {
      userMessage = 'Too many requests. Please wait a moment and try again.';
      technicalMessage = 'Rate limit exceeded';
    } else if (error.response?.status && error.response.status >= 500) {
      userMessage = 'Server error. Our team has been notified. Please try again later.';
      technicalMessage = errorDetails || 'Internal server error';
    }

    return {
      message: technicalMessage,
      userMessage,
      code: error.code,
      status: error.response?.status,
      timestamp: new Date().toISOString(),
      requestId,
      retryable,
      details: {
        url: error.config?.url,
        method: error.config?.method,
        responseData: responseData,
        originalError: error.message
      }
    };
  }

  private async retryRequest<T>(
    requestFn: () => Promise<AxiosResponse<T>>,
    retryConfig: Partial<RetryConfig> = {}
  ): Promise<AxiosResponse<T>> {
    /**
     * 🔄 Intelligent retry mechanism with exponential backoff
     * Automatically retries failed requests based on error type and configuration
     */
    const config = { ...this.defaultRetryConfig, ...retryConfig };
    let lastError: ApiError;

    for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
      try {
        const response = await requestFn();

        if (attempt > 0) {
          console.log(`✅ RETRY_SUCCESS: Request succeeded on attempt ${attempt + 1}`);
        }

        return response;
      } catch (error) {
        lastError = error as ApiError;

        // Don't retry if this is the last attempt or error is not retryable
        if (attempt === config.maxRetries || !lastError.retryable) {
          break;
        }

        // Calculate delay with exponential backoff
        const delay = config.retryDelay * Math.pow(2, attempt);
        console.warn(`🔄 RETRY_ATTEMPT: Attempt ${attempt + 1}/${config.maxRetries + 1} failed, retrying in ${delay}ms`, {
          error: lastError.message,
          requestId: lastError.requestId
        });

        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }

    console.error(`❌ RETRY_EXHAUSTED: All ${config.maxRetries + 1} attempts failed`, {
      finalError: lastError!.message,
      requestId: lastError!.requestId
    });

    throw lastError!;
  }

  // 🚀 Enhanced HTTP methods with retry logic
  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.retryRequest(() => this.axiosInstance.get<T>(url, config));
    return response.data;
  }

  async post<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.retryRequest(() => this.axiosInstance.post<T>(url, data, config));
    return response.data;
  }

  async put<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.retryRequest(() => this.axiosInstance.put<T>(url, data, config));
    return response.data;
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.retryRequest(() => this.axiosInstance.delete<T>(url, config));
    return response.data;
  }

  // 📁 Special method for file uploads with progress tracking
  async uploadFile<T>(
    url: string,
    file: File,
    onProgress?: (progress: number) => void,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const formData = new FormData();
    formData.append('file', file);

    const uploadConfig: AxiosRequestConfig = {
      ...config,
      headers: {
        'Content-Type': 'multipart/form-data',
        ...config?.headers
      },
      timeout: 300000, // 5 minutes for file uploads
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      }
    };

    // No retry for file uploads to avoid duplicate uploads
    const response = await this.axiosInstance.post<T>(url, formData, uploadConfig);
    return response.data;
  }

  // 📥 Special method for blob downloads with better error handling
  async downloadBlob(url: string, config?: AxiosRequestConfig): Promise<Blob> {
    const response = await this.retryRequest(() =>
      this.axiosInstance.get(url, {
        ...config,
        responseType: 'blob',
        timeout: 300000 // 5 minutes for downloads
      })
    );
    return response.data;
  }
}

// Create enhanced API instance
export const api = new EnhancedApiClient();


// 📄 Enhanced Document API with comprehensive error handling and progress tracking
export const documentApi = {
  /**
   * 📤 Upload a document with progress tracking and enhanced error handling
   * Supports large files with timeout extension and detailed progress feedback
   */
  upload: async (file: File, onProgress?: (progress: number) => void): Promise<DocumentUploadResponse> => {
    try {
      console.log(`📤 UPLOAD_START: Uploading "${file.name}" (${(file.size / 1024 / 1024).toFixed(2)}MB)`);

      const result = await api.uploadFile('/documents/upload', file, onProgress);

      console.log(`✅ UPLOAD_SUCCESS: "${file.name}" uploaded successfully`, {
        documentId: (result as { id?: number }).id,
        filename: (result as { filename?: string }).filename
      });

      return result as DocumentUploadResponse;
    } catch (error) {
      const apiError = error as ApiError;
      console.error(`❌ UPLOAD_FAILED: "${file.name}" upload failed`, {
        error: apiError.message,
        userMessage: apiError.userMessage,
        requestId: apiError.requestId
      });
      throw apiError;
    }
  },

  /**
   * ⚙️ Process a document with template mode support and enhanced error handling
   */
  process: async (documentId: number, schema?: unknown): Promise<{ message: string; status: string }> => {
    try {
      console.log(`⚙️ PROCESS_START: Starting processing for document ${documentId}`, {
        templateMode: schema && (schema as { template_mode?: boolean }).template_mode,
        hasSchema: !!schema
      });

      const result = await api.post(`/documents/process/${documentId}`, { schema });

      console.log(`✅ PROCESS_STARTED: Document ${documentId} processing initiated successfully`);
      return result as { message: string; status: string };
    } catch (error) {
      const apiError = error as ApiError;
      console.error(`❌ PROCESS_FAILED: Document ${documentId} processing failed to start`, {
        error: apiError.message,
        userMessage: apiError.userMessage,
        requestId: apiError.requestId
      });
      throw apiError;
    }
  },

  /**
   * 📊 Get document status with enhanced error handling
   */
  getStatus: async (documentId: number): Promise<ProcessingStatus> => {
    try {
      const result = await api.get(`/documents/${documentId}/status`);
      return result as ProcessingStatus;
    } catch (error) {
      const apiError = error as ApiError;

      // Don't log 404s as errors for status checks (document might be deleted)
      if (apiError.status !== 404) {
        console.error(`❌ STATUS_CHECK_FAILED: Document ${documentId} status check failed`, {
          error: apiError.message,
          requestId: apiError.requestId
        });
      }

      throw apiError;
    }
  },

  /**
   * 📋 List documents with enhanced filtering and error handling
   */
  list: async (params?: { skip?: number; limit?: number; status?: string }): Promise<DocumentListResponse> => {
    try {
      const result = await api.get('/documents/', { params });

      console.log(`📋 LIST_SUCCESS: Retrieved ${(result as { documents?: unknown[] }).documents?.length || 0} documents`, {
        total: (result as { total?: number }).total,
        skip: params?.skip || 0,
        limit: params?.limit || 50,
        statusFilter: params?.status
      });

      return result as DocumentListResponse;
    } catch (error) {
      const apiError = error as ApiError;
      console.error(`❌ LIST_FAILED: Failed to retrieve document list`, {
        error: apiError.message,
        params,
        requestId: apiError.requestId
      });
      throw apiError;
    }
  },

  /**
   * 📥 Download Excel with enhanced error handling and progress tracking
   */
  downloadExcel: async (documentId: number, includeMetadata: boolean = true): Promise<Blob> => {
    try {
      console.log(`📥 DOWNLOAD_START: Downloading Excel for document ${documentId}`, {
        includeMetadata
      });

      const blob = await api.downloadBlob(`/documents/${documentId}/download/excel`, {
        params: { include_metadata: includeMetadata }
      });

      console.log(`✅ DOWNLOAD_SUCCESS: Excel downloaded for document ${documentId}`, {
        size: `${(blob.size / 1024).toFixed(2)}KB`
      });

      return blob;
    } catch (error) {
      const apiError = error as ApiError;
      console.error(`❌ DOWNLOAD_FAILED: Excel download failed for document ${documentId}`, {
        error: apiError.message,
        userMessage: apiError.userMessage,
        requestId: apiError.requestId
      });
      throw apiError;
    }
  },

  /**
   * 🗑️ Delete document with confirmation and enhanced error handling
   */
  delete: async (documentId: number): Promise<{ message: string }> => {
    try {
      console.log(`🗑️ DELETE_START: Deleting document ${documentId}`);

      const result = await api.delete(`/documents/${documentId}`);

      console.log(`✅ DELETE_SUCCESS: Document ${documentId} deleted successfully`);
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      return result as any;
    } catch (error) {
      const apiError = error as ApiError;
      console.error(`❌ DELETE_FAILED: Failed to delete document ${documentId}`, {
        error: apiError.message,
        userMessage: apiError.userMessage,
        requestId: apiError.requestId
      });
      throw apiError;
    }
  },

  /**
   * ⚙️ Batch process multiple documents with enhanced monitoring
   */
  batchProcess: async (documentIds: number[], schema?: unknown): Promise<{ message: string; job_ids: string[] }> => {
    try {
      console.log(`⚙️ BATCH_PROCESS_START: Processing ${documentIds.length} documents`, {
        documentIds,
        hasSchema: !!schema
      });

      const result = await api.post('/documents/batch/process', {
        document_ids: documentIds,
        schema,
      });

      console.log(`✅ BATCH_PROCESS_STARTED: Batch processing initiated for ${documentIds.length} documents`);
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      return result as any;
    } catch (error) {
      const apiError = error as ApiError;
      console.error(`❌ BATCH_PROCESS_FAILED: Batch processing failed`, {
        documentCount: documentIds.length,
        documentIds,
        error: apiError.message,
        userMessage: apiError.userMessage,
        requestId: apiError.requestId
      });
      throw apiError;
    }
  },

  /**
   * 📥 Batch download Excel files with enhanced error handling
   */
  batchDownloadExcel: async (documentIds: number[]): Promise<Blob> => {
    try {
      console.log(`📥 BATCH_DOWNLOAD_START: Downloading Excel for ${documentIds.length} documents`, {
        documentIds
      });

      const blob = await api.downloadBlob('/documents/batch/download/excel', {
        params: { document_ids: documentIds }
      });

      console.log(`✅ BATCH_DOWNLOAD_SUCCESS: Batch Excel downloaded`, {
        documentCount: documentIds.length,
        size: `${(blob.size / 1024).toFixed(2)}KB`
      });

      return blob;
    } catch (error) {
      const apiError = error as ApiError;
      console.error(`❌ BATCH_DOWNLOAD_FAILED: Batch Excel download failed`, {
        documentCount: documentIds.length,
        documentIds,
        error: apiError.message,
        userMessage: apiError.userMessage,
        requestId: apiError.requestId
      });
      throw apiError;
    }
  },

  /**
   * 📋 Download template Excel with enhanced error handling
   */
  downloadTemplate: async (documentIds: number[]): Promise<Blob> => {
    try {
      console.log(`📋 TEMPLATE_DOWNLOAD_START: Downloading template for ${documentIds.length} documents`, {
        documentIds
      });

      // Format parameters correctly for FastAPI
      const params = new URLSearchParams();
      documentIds.forEach(id => params.append('document_ids', id.toString()));

      const blob = await api.downloadBlob(`/documents/template/download/excel?${params.toString()}`);

      console.log(`✅ TEMPLATE_DOWNLOAD_SUCCESS: Template Excel downloaded`, {
        documentCount: documentIds.length,
        size: `${(blob.size / 1024).toFixed(2)}KB`
      });

      return blob;
    } catch (error) {
      const apiError = error as ApiError;
      console.error(`❌ TEMPLATE_DOWNLOAD_FAILED: Template download failed`, {
        documentCount: documentIds.length,
        documentIds,
        error: apiError.message,
        userMessage: apiError.userMessage,
        requestId: apiError.requestId
      });
      throw apiError;
    }
  },
};

// 🎯 Enhanced Schema API with comprehensive error handling
export const schemaApi = {
  /**
   * 🔍 Detect schema from sample image with enhanced error handling
   */
  detect: async (sampleImageBase64: string, description?: string): Promise<{ fields: unknown[]; type: string }> => {
    try {
      console.log('🔍 SCHEMA_DETECT_START: Analyzing sample image for schema detection', {
        imageSize: sampleImageBase64.length,
        hasDescription: !!description
      });

      const result = await api.post('/schemas/detect', {
        sample_image_base64: sampleImageBase64,
        description,
      });

      console.log('✅ SCHEMA_DETECT_SUCCESS: Schema detection completed', {
        fieldsDetected: (result as { fields?: unknown[] }).fields?.length || 0,
        schemaType: (result as { type?: string }).type
      });

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      return result as any;
    } catch (error) {
      const apiError = error as ApiError;
      console.error('❌ SCHEMA_DETECT_FAILED: Schema detection failed', {
        error: apiError.message,
        userMessage: apiError.userMessage,
        requestId: apiError.requestId
      });
      throw apiError;
    }
  },

  /**
   * 📋 List available schemas with enhanced error handling
   */
  list: async (): Promise<unknown[]> => {
    try {
      const result = await api.get('/schemas/');

      console.log(`📋 SCHEMA_LIST_SUCCESS: Retrieved ${(result as unknown[]).length || 0} schemas`);
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      return result as any;
    } catch (error) {
      const apiError = error as ApiError;
      console.error('❌ SCHEMA_LIST_FAILED: Failed to retrieve schemas', {
        error: apiError.message,
        requestId: apiError.requestId
      });
      throw apiError;
    }
  },

  /**
   * 💾 Save schema with enhanced error handling
   */
  save: async (schema: unknown): Promise<{ id: string; name: string }> => {
    try {
      console.log('💾 SCHEMA_SAVE_START: Saving new schema', {
        schemaType: (schema as { type?: string })?.type,
        fieldsCount: (schema as { fields?: unknown[] })?.fields?.length || 0
      });

      const result = await api.post('/schemas/', schema);

      console.log('✅ SCHEMA_SAVE_SUCCESS: Schema saved successfully', {
        schemaId: (result as { id?: string }).id,
        schemaName: (result as { name?: string }).name
      });

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      return result as any;
    } catch (error) {
      const apiError = error as ApiError;
      console.error('❌ SCHEMA_SAVE_FAILED: Failed to save schema', {
        error: apiError.message,
        userMessage: apiError.userMessage,
        requestId: apiError.requestId
      });
      throw apiError;
    }
  },
};

// 🔄 Enhanced SSE (Server-Sent Events) for real-time updates with error handling and reconnection
export class EnhancedEventSource {
  private eventSource: EventSource | null = null;
  private documentId: number;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private isConnected = false;
  private listeners: { [event: string]: ((data?: unknown) => void)[] } = {};

  constructor(documentId: number) {
    this.documentId = documentId;
    this.connect();
  }

  private connect() {
    try {
      const url = `${API_BASE_URL}/documents/${this.documentId}/stream`;
      console.log(`🔄 SSE_CONNECT: Connecting to real-time updates for document ${this.documentId}`);

      this.eventSource = new EventSource(url);

      this.eventSource.onopen = () => {
        console.log(`✅ SSE_CONNECTED: Real-time connection established for document ${this.documentId}`);
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.emit('connected', { documentId: this.documentId });
      };

      this.eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log(`📡 SSE_MESSAGE: Received update for document ${this.documentId}`, {
            status: data.status,
            progress: data.progress
          });
          this.emit('update', data);
        } catch (error) {
          console.error('❌ SSE_PARSE_ERROR: Failed to parse SSE message', {
            data: event.data,
            error: error
          });
        }
      };

      this.eventSource.onerror = (error) => {
        console.error(`❌ SSE_ERROR: Connection error for document ${this.documentId}`, error);
        this.isConnected = false;
        this.emit('error', error);

        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.attemptReconnect();
        } else {
          console.error(`🚨 SSE_RECONNECT_EXHAUSTED: Max reconnection attempts reached for document ${this.documentId}`);
          this.emit('reconnectFailed', { documentId: this.documentId, attempts: this.reconnectAttempts });
        }
      };

    } catch (error) {
      console.error(`❌ SSE_CONNECT_ERROR: Failed to establish SSE connection for document ${this.documentId}`, error);
      this.emit('connectionFailed', { documentId: this.documentId, error });
    }
  }

  private attemptReconnect() {
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

    console.log(`🔄 SSE_RECONNECT: Attempting reconnection ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${delay}ms`);

    setTimeout(() => {
      if (this.eventSource) {
        this.eventSource.close();
      }
      this.connect();
    }, delay);
  }

  /**
   * 📡 Add event listener with type safety
   */
  on(event: string, listener: (data?: unknown) => void) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(listener);
  }

  /**
   * 📡 Remove event listener
   */
  off(event: string, listener: (data?: unknown) => void) {
    if (this.listeners[event]) {
      this.listeners[event] = this.listeners[event].filter(l => l !== listener);
    }
  }

  /**
   * 📡 Emit event to all listeners
   */
  private emit(event: string, data?: unknown) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(listener => {
        try {
          listener(data);
        } catch (error) {
          console.error(`❌ SSE_LISTENER_ERROR: Error in ${event} listener`, error);
        }
      });
    }
  }

  /**
   * 🛑 Close SSE connection with cleanup
   */
  close() {
    console.log(`🛑 SSE_CLOSE: Closing real-time connection for document ${this.documentId}`);

    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }

    this.isConnected = false;
    this.listeners = {};

    console.log(`✅ SSE_CLOSED: Real-time connection closed for document ${this.documentId}`);
  }

  /**
   * 📊 Get connection status
   */
  getStatus() {
    return {
      connected: this.isConnected,
      documentId: this.documentId,
      reconnectAttempts: this.reconnectAttempts,
      maxReconnectAttempts: this.maxReconnectAttempts
    };
  }
}

/**
 * 🔄 Create enhanced event source with automatic error handling and reconnection
 */
export const createEventSource = (documentId: number) => {
  return new EnhancedEventSource(documentId);
};