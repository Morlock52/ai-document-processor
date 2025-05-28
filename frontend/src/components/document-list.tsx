'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { format } from 'date-fns';
import {
  FileText,
  Download,
  Trash2,
  RefreshCw,
  CheckCircle,
  XCircle,
  Clock,
  Loader2,
  Calendar,
  FileCheck,
  Table,
} from 'lucide-react';
import { documentApi } from '@/lib/api';
import { Button } from '@/components/ui/button';
import type { Document, DocumentListResponse } from '@/types';
import { Progress } from '@/components/ui/progress';
import { useToast } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';

const statusConfig = {
  pending: {
    icon: Clock,
    color: 'bg-gradient-to-r from-yellow-400 to-orange-500',
    textColor: 'text-yellow-700 dark:text-yellow-400',
    bgColor: 'bg-yellow-50 dark:bg-yellow-950/20',
    text: 'Pending'
  },
  processing: {
    icon: Loader2,
    color: 'bg-gradient-to-r from-blue-400 to-indigo-500',
    textColor: 'text-blue-700 dark:text-blue-400',
    bgColor: 'bg-blue-50 dark:bg-blue-950/20',
    text: 'Processing'
  },
  completed: {
    icon: CheckCircle,
    color: 'bg-gradient-to-r from-emerald-400 to-teal-500',
    textColor: 'text-emerald-700 dark:text-emerald-400',
    bgColor: 'bg-emerald-50 dark:bg-emerald-950/20',
    text: 'Completed'
  },
  failed: {
    icon: XCircle,
    color: 'bg-gradient-to-r from-red-400 to-pink-500',
    textColor: 'text-red-700 dark:text-red-400',
    bgColor: 'bg-red-50 dark:bg-red-950/20',
    text: 'Failed'
  },
};

interface DocumentListProps {
  templateMode?: boolean;
}

export function DocumentList({ templateMode = false }: DocumentListProps) {
  const [selectedDocs, setSelectedDocs] = useState<number[]>([]);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const { data, isLoading, refetch } = useQuery<DocumentListResponse>({
    queryKey: ['documents'],
    queryFn: () => documentApi.list({ limit: 50 }),
    refetchInterval: 5000, // Poll every 5 seconds
  });

  const deleteMutation = useMutation({
    mutationFn: documentApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      toast({
        title: 'Document deleted',
        description: 'The document has been deleted successfully.',
      });
    },
    onError: (error: unknown) => {
      toast({
        title: 'Delete failed',
        description: error instanceof Error ? error.message : 'An error occurred',
        variant: 'destructive',
      });
    },
  });

  const downloadExcel = async (documentId: number, filename: string) => {
    try {
      const blob = await documentApi.downloadExcel(documentId);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${filename.replace('.pdf', '')}_extracted.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error: unknown) {
      toast({
        title: 'Download failed',
        description: error instanceof Error ? error.message : 'An error occurred',
        variant: 'destructive',
      });
    }
  };

  const batchDownload = async () => {
    if (selectedDocs.length === 0) return;

    try {
      const blob = await documentApi.batchDownloadExcel(selectedDocs);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `batch_export_${format(new Date(), 'yyyyMMdd_HHmmss')}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error: unknown) {
      toast({
        title: 'Batch download failed',
        description: error instanceof Error ? error.message : 'An error occurred',
        variant: 'destructive',
      });
    }
  };

  const downloadTemplate = async () => {
    try {
      const completedDocs = documents.filter((doc: Document) => doc.status === 'completed');
      if (completedDocs.length === 0) {
        toast({
          title: 'No completed documents',
          description: 'Upload and process some documents first to generate a template.',
          variant: 'destructive',
        });
        return;
      }

      const blob = await documentApi.downloadTemplate(completedDocs.map((doc: Document) => doc.id));
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `template_export_${format(new Date(), 'yyyyMMdd_HHmmss')}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      toast({
        title: 'Template downloaded',
        description: 'Excel template with all detected fields has been downloaded.',
      });
    } catch (error: unknown) {
      toast({
        title: 'Template download failed',
        description: error instanceof Error ? error.message : 'An error occurred',
        variant: 'destructive',
      });
    }
  };

  const toggleSelection = (id: number) => {
    setSelectedDocs((prev) =>
      prev.includes(id) ? prev.filter((d) => d !== id) : [...prev, id]
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  const documents: Document[] = data?.documents || [];
  const completedDocs = selectedDocs.filter((id) =>
    documents.find((d: Document) => d.id === id && d.status === 'completed')
  );

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 text-white">
            <FileCheck className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-2xl font-bold">Document Library</h2>
            <p className="text-sm text-muted-foreground">
              {documents.length} {documents.length === 1 ? 'document' : 'documents'} • {completedDocs.length} ready for download
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {templateMode && documents.filter((doc: Document) => doc.status === 'completed').length > 0 && (
            <Button
              onClick={downloadTemplate}
              className="px-6 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white rounded-xl shadow-lg hover:shadow-xl transition-all duration-300"
            >
              <Table className="h-4 w-4 mr-2" />
              Download Template
            </Button>
          )}
          {!templateMode && completedDocs.length > 0 && (
            <Button
              onClick={batchDownload}
              className="px-6 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white rounded-xl shadow-lg hover:shadow-xl transition-all duration-300"
            >
              <Download className="h-4 w-4 mr-2" />
              Download Selected ({completedDocs.length})
            </Button>
          )}
          <Button
            onClick={() => refetch()}
            variant="outline"
            className="px-4 py-2 rounded-xl border-2 hover:bg-gray-50 dark:hover:bg-gray-800 transition-all duration-300"
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {documents.length === 0 ? (
        <div className="text-center py-16 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-900 rounded-3xl">
          <div className="flex items-center justify-center w-20 h-20 mx-auto mb-6 bg-gradient-to-br from-gray-300 to-gray-400 dark:from-gray-600 dark:to-gray-700 rounded-2xl">
            <FileText className="w-10 h-10 text-gray-600 dark:text-gray-300" />
          </div>
          <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">No documents yet</h3>
          <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto">
            Upload your first PDF document to get started with AI-powered data extraction.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Header with select all */}
          <div className="flex items-center gap-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-2xl">
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                id="select-all-documents"
                name="select-all"
                className="w-4 h-4 rounded border-gray-300 dark:border-gray-600 text-indigo-600 focus:ring-indigo-500 dark:focus:ring-indigo-400"
                onChange={(e) => {
                  if (e.target.checked) {
                    setSelectedDocs(documents.map((d: Document) => d.id));
                  } else {
                    setSelectedDocs([]);
                  }
                }}
                checked={
                  documents.length > 0 &&
                  selectedDocs.length === documents.length
                }
              />
              <label htmlFor="select-all-documents" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Select all documents
              </label>
            </div>
          </div>

          {/* Document cards */}
          <div className="grid gap-4">
            {documents.map((doc: Document) => {
              const status = statusConfig[doc.status as keyof typeof statusConfig];
              const StatusIcon = status.icon;
              return (
                <div
                  key={doc.id}
                  className="group relative overflow-hidden p-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl hover:shadow-lg transition-all duration-300"
                >
                  <div className="flex items-start gap-4">
                    {/* Checkbox */}
                    <div className="pt-1">
                      <input
                        type="checkbox"
                        id={`select-document-${doc.id}`}
                        name={`document-${doc.id}`}
                        className="w-4 h-4 rounded border-gray-300 dark:border-gray-600 text-indigo-600 focus:ring-indigo-500 dark:focus:ring-indigo-400"
                        checked={selectedDocs.includes(doc.id)}
                        onChange={() => toggleSelection(doc.id)}
                      />
                    </div>

                    {/* Document icon */}
                    <div className="flex items-center justify-center w-12 h-12 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 text-white flex-shrink-0">
                      <FileText className="w-6 h-6" />
                    </div>

                    {/* Document details */}
                    <div className="flex-1 min-w-0 space-y-3">
                      <div className="flex items-center justify-between">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white truncate pr-4">
                          {doc.original_filename}
                        </h3>

                        {/* Actions */}
                        <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                          {doc.status === 'completed' && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => downloadExcel(doc.id, doc.original_filename)}
                              className="h-9 w-9 p-0 hover:bg-emerald-50 dark:hover:bg-emerald-950/20 hover:text-emerald-600 dark:hover:text-emerald-400 rounded-xl"
                              title="Download Excel"
                            >
                              <Download className="h-4 w-4" />
                            </Button>
                          )}
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => deleteMutation.mutate(doc.id)}
                            className="h-9 w-9 p-0 hover:bg-red-50 dark:hover:bg-red-950/20 hover:text-red-600 dark:hover:text-red-400 rounded-xl"
                            title="Delete document"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>

                      {/* Status and progress */}
                      <div className="flex items-center gap-4">
                        <div className={cn(
                          'flex items-center gap-2 px-3 py-1 rounded-xl text-sm font-medium',
                          status.bgColor,
                          status.textColor
                        )}>
                          <StatusIcon className={cn(
                            'w-4 h-4',
                            doc.status === 'processing' && 'animate-spin'
                          )} />
                          <span>{status.text}</span>
                        </div>

                        {doc.status === 'processing' && (
                          <div className="flex-1 max-w-xs">
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-xs text-gray-600 dark:text-gray-400">Processing...</span>
                              <span className="text-xs text-gray-600 dark:text-gray-400">{Math.round(doc.progress * 100)}%</span>
                            </div>
                            <Progress value={doc.progress * 100} className="h-2" />
                          </div>
                        )}
                      </div>

                      {/* Metadata */}
                      <div className="flex items-center gap-6 text-sm text-gray-600 dark:text-gray-400">
                        {doc.page_count && (
                          <div className="flex items-center gap-1">
                            <FileText className="w-4 h-4" />
                            <span>{doc.page_count} pages</span>
                          </div>
                        )}
                        <div className="flex items-center gap-1">
                          <Calendar className="w-4 h-4" />
                          <span>{format(new Date(doc.created_at), 'MMM d, h:mm a')}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}