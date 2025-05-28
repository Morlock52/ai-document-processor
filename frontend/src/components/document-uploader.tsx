'use client';

import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X, AlertCircle, CheckCircle2, FileText, Sparkles, RotateCcw, Info } from 'lucide-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { documentApi } from '@/lib/api';
import { cn } from '@/lib/utils';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';

interface UploadedFile {
  file: File;
  id: string;
  status: 'pending' | 'uploading' | 'success' | 'error';
  progress: number;
  documentId?: number;
  error?: string;
  retryable?: boolean;
  retryCount?: number;
}

interface DocumentUploaderProps {
  templateMode?: boolean;
}

export function DocumentUploader({ templateMode = false }: DocumentUploaderProps) {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const uploadMutation = useMutation({
    mutationFn: async (uploadedFile: UploadedFile) => {
      // 📤 Enhanced upload with real-time progress tracking and detailed error handling
      const response = await documentApi.upload(
        uploadedFile.file,
        (progress) => {
          // Real-time progress updates during upload
          setFiles((prev) =>
            prev.map((f) =>
              f.id === uploadedFile.id
                ? { ...f, progress, status: 'uploading' }
                : f
            )
          );
        }
      );
      return { uploadedFile, response };
    },
    onSuccess: ({ uploadedFile, response }) => {
      // 🎉 Upload success with enhanced user feedback
      setFiles((prev) =>
        prev.map((f) =>
          f.id === uploadedFile.id
            ? { ...f, status: 'success', documentId: response.id, progress: 100 }
            : f
        )
      );

      queryClient.invalidateQueries({ queryKey: ['documents'] });

      // 🎊 Success toast with detailed information
      toast({
        title: '✅ Upload Complete',
        description: `"${uploadedFile.file.name}" uploaded successfully and processing will begin automatically.`,
        variant: 'default',
      });

      // 🚀 Auto-start processing with template mode and enhanced error handling
      documentApi.process(
        response.id,
        templateMode ? { template_mode: true } : undefined
      ).catch((err) => {
        console.error('🚨 PROCESSING_AUTO_START_FAILED:', err);

        // Show processing start failure but don't mark upload as failed
        toast({
          title: '⚠️ Processing Start Failed',
          description: err.userMessage || 'Failed to start processing automatically. You can manually start processing from the document list.',
          variant: 'destructive',
        });
      });
    },
    onError: (error: unknown, uploadedFile) => {
      // 🚨 Enhanced error handling with user-friendly messages and retry options
      const apiError = error as { userMessage?: string; message?: string; retryable?: boolean; requestId?: string; status?: number };
      const userMessage = apiError?.userMessage || 'Upload failed. Please try again.';
      const technicalMessage = apiError?.message || 'An unexpected error occurred';
      const isRetryable = apiError?.retryable !== false;

      console.error('❌ UPLOAD_ERROR:', {
        filename: uploadedFile.file.name,
        error: technicalMessage,
        userMessage,
        requestId: apiError?.requestId,
        retryable: isRetryable
      });

      setFiles((prev) =>
        prev.map((f) =>
          f.id === uploadedFile.id
            ? {
                ...f,
                status: 'error',
                error: userMessage,
                progress: 0,
                retryable: isRetryable,
                retryCount: (f.retryCount || 0)
              }
            : f
        )
      );

      // 🚨 Enhanced error toast with retry option if applicable
      toast({
        title: '❌ Upload Failed',
        description: (
          <div className="space-y-2">
            <p>{userMessage}</p>
            {isRetryable && (
              <p className="text-sm text-gray-500">
                You can try uploading the file again or check your internet connection.
              </p>
            )}
            {process.env.NODE_ENV === 'development' && (
              <details className="text-xs text-gray-400">
                <summary>Technical Details</summary>
                <p>Error: {technicalMessage}</p>
                <p>Request ID: {apiError?.requestId}</p>
                <p>Status: {apiError?.status}</p>
              </details>
            )}
          </div>
        ),
        variant: 'destructive',
      });
    },
  });

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles: UploadedFile[] = acceptedFiles.map((file) => ({
      file,
      id: Math.random().toString(36).substring(7),
      status: 'pending',
      progress: 0,
    }));

    setFiles((prev) => [...prev, ...newFiles]);

    // Start uploading each file
    newFiles.forEach((uploadedFile) => {
      setFiles((prev) =>
        prev.map((f) =>
          f.id === uploadedFile.id ? { ...f, status: 'uploading' } : f
        )
      );
      uploadMutation.mutate(uploadedFile);
    });
  }, [uploadMutation]);

  const removeFile = (id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id));
  };

  // 🔄 Retry failed upload with enhanced tracking
  const retryUpload = (uploadedFile: UploadedFile) => {
    const maxRetries = 3;
    const currentRetryCount = (uploadedFile.retryCount || 0) + 1;

    if (currentRetryCount > maxRetries) {
      toast({
        title: '❌ Max Retries Exceeded',
        description: `Maximum retry attempts (${maxRetries}) reached for "${uploadedFile.file.name}". Please try uploading a different file or check the file format.`,
        variant: 'destructive',
      });
      return;
    }

    console.log(`🔄 RETRY_UPLOAD: Attempting retry ${currentRetryCount}/${maxRetries} for "${uploadedFile.file.name}"`);

    // Update file status to pending and increment retry count
    setFiles((prev) =>
      prev.map((f) =>
        f.id === uploadedFile.id
          ? {
              ...f,
              status: 'pending',
              error: undefined,
              progress: 0,
              retryCount: currentRetryCount
            }
          : f
      )
    );

    // Show retry toast
    toast({
      title: '🔄 Retrying Upload',
      description: `Attempting to upload "${uploadedFile.file.name}" again (attempt ${currentRetryCount}/${maxRetries}).`,
      variant: 'default',
    });

    // Trigger upload mutation
    uploadMutation.mutate({
      ...uploadedFile,
      retryCount: currentRetryCount
    });
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    multiple: true,
    maxSize: 100 * 1024 * 1024, // 100MB
  });

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={cn(
          'relative overflow-hidden border-2 border-dashed rounded-3xl p-12 text-center cursor-pointer transition-all duration-300 group',
          isDragActive
            ? 'border-indigo-400 bg-gradient-to-br from-indigo-50 to-purple-50 dark:from-indigo-950/20 dark:to-purple-950/20 scale-[1.02] shadow-2xl'
            : 'border-gray-300 dark:border-gray-600 hover:border-indigo-300 dark:hover:border-indigo-500 hover:bg-gradient-to-br hover:from-gray-50 hover:to-indigo-50 dark:hover:from-gray-800 dark:hover:to-indigo-950/20 hover:shadow-xl'
        )}
      >
        <input {...getInputProps()} id="document-file-input" name="document-file" />

        {/* Background decoration */}
        <div className="absolute inset-0 bg-grid-slate-100 [mask-image:linear-gradient(0deg,white,rgba(255,255,255,0.6))] dark:bg-grid-slate-700/25 opacity-30"></div>

        <div className="relative z-10">
          <div className={cn(
            'mx-auto mb-6 transition-all duration-300',
            isDragActive ? 'scale-110 rotate-6' : 'group-hover:scale-105'
          )}>
            {isDragActive ? (
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-2xl blur opacity-75 animate-pulse"></div>
                <div className="relative flex items-center justify-center w-20 h-20 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl text-white shadow-xl">
                  <Sparkles className="w-10 h-10 animate-pulse" />
                </div>
              </div>
            ) : (
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-2xl blur opacity-20 group-hover:opacity-40 transition-opacity duration-300"></div>
                <div className="relative flex items-center justify-center w-20 h-20 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl text-white shadow-lg group-hover:shadow-xl transition-shadow duration-300">
                  <Upload className="w-10 h-10" />
                </div>
              </div>
            )}
          </div>

          {isDragActive ? (
            <div className="space-y-3">
              <p className="text-2xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                Drop your PDFs here!
              </p>
              <p className="text-indigo-600 dark:text-indigo-400 font-medium">
                Release to start processing
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                  Upload Your PDF Documents
                </p>
                <p className="text-gray-600 dark:text-gray-300 text-lg">
                  Drag & drop files here, or <span className="text-indigo-600 dark:text-indigo-400 font-semibold">click to browse</span>
                </p>
              </div>

              <div className="flex items-center justify-center gap-6 text-sm text-gray-500 dark:text-gray-400">
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4" />
                  <span>PDF files only</span>
                </div>
                <div className="w-1 h-1 bg-gray-400 rounded-full"></div>
                <div>Max 100MB each</div>
                <div className="w-1 h-1 bg-gray-400 rounded-full"></div>
                <div>Batch upload supported</div>
              </div>

              <div className="mt-6">
                <Button className="px-8 py-3 text-base font-semibold rounded-2xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 shadow-lg hover:shadow-xl transition-all duration-300">
                  Choose Files
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>

      {files.length > 0 && (
        <div className="space-y-6">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-8 h-8 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 text-white">
              <FileText className="w-4 h-4" />
            </div>
            <h3 className="text-xl font-bold">Upload Progress</h3>
            <div className="flex-1 h-px bg-gradient-to-r from-gray-200 to-transparent dark:from-gray-700"></div>
          </div>

          <div className="grid gap-4">
            {files.map((uploadedFile) => (
              <div
                key={uploadedFile.id}
                className="group relative overflow-hidden p-6 border border-gray-200 dark:border-gray-700 rounded-2xl bg-white dark:bg-gray-800 hover:shadow-lg transition-all duration-300"
              >
                <div className="flex items-center gap-4">
                  <div className={cn(
                    'flex items-center justify-center w-12 h-12 rounded-2xl text-white transition-all duration-300',
                    uploadedFile.status === 'success'
                      ? 'bg-gradient-to-br from-emerald-500 to-teal-600'
                      : uploadedFile.status === 'error'
                      ? 'bg-gradient-to-br from-red-500 to-pink-600'
                      : uploadedFile.status === 'uploading'
                      ? 'bg-gradient-to-br from-blue-500 to-indigo-600 animate-pulse'
                      : 'bg-gradient-to-br from-gray-400 to-gray-600'
                  )}>
                    {uploadedFile.status === 'success' ? (
                      <CheckCircle2 className="w-6 h-6" />
                    ) : uploadedFile.status === 'error' ? (
                      <AlertCircle className="w-6 h-6" />
                    ) : (
                      <File className="w-6 h-6" />
                    )}
                  </div>

                  <div className="flex-1 min-w-0 space-y-2">
                    <div className="flex items-center justify-between">
                      <p className="text-base font-semibold truncate text-gray-900 dark:text-white">
                        {uploadedFile.file.name}
                        {uploadedFile.retryCount && uploadedFile.retryCount > 0 && (
                          <span className="ml-2 text-xs text-orange-600 dark:text-orange-400 bg-orange-100 dark:bg-orange-900/20 px-2 py-1 rounded-full">
                            Retry #{uploadedFile.retryCount}
                          </span>
                        )}
                      </p>
                      <div className="flex items-center gap-2">
                        {uploadedFile.status === 'error' && uploadedFile.retryable && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => retryUpload(uploadedFile)}
                            className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity duration-200 hover:bg-orange-50 dark:hover:bg-orange-950/20 hover:text-orange-600 dark:hover:text-orange-400"
                            title="Retry upload"
                          >
                            <RotateCcw className="h-4 w-4" />
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeFile(uploadedFile.id)}
                          className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity duration-200 hover:bg-red-50 dark:hover:bg-red-950/20 hover:text-red-600 dark:hover:text-red-400"
                          title="Remove file"
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>

                    <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
                      <span>{(uploadedFile.file.size / 1024 / 1024).toFixed(2)} MB</span>
                      {uploadedFile.status === 'success' && (
                        <div className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-medium">
                          <CheckCircle2 className="w-4 h-4" />
                          <span>Upload Complete</span>
                        </div>
                      )}
                      {uploadedFile.status === 'uploading' && (
                        <div className="flex items-center gap-2 text-blue-600 dark:text-blue-400">
                          <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                          <span>Uploading...</span>
                        </div>
                      )}
                      {uploadedFile.status === 'error' && (
                        <div className="flex items-center gap-1 text-red-600 dark:text-red-400 font-medium">
                          <AlertCircle className="w-4 h-4" />
                          <span>Upload Failed</span>
                        </div>
                      )}
                    </div>

                    {uploadedFile.status === 'uploading' && (
                      <div className="space-y-1">
                        <Progress value={uploadedFile.progress} className="h-2 bg-gray-100 dark:bg-gray-700" />
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {uploadedFile.progress}% complete
                        </p>
                      </div>
                    )}

                    {uploadedFile.status === 'error' && uploadedFile.error && (
                      <div className="bg-red-50 dark:bg-red-950/20 px-3 py-2 rounded-lg border border-red-200 dark:border-red-800">
                        <div className="flex items-start gap-2">
                          <AlertCircle className="w-4 h-4 text-red-600 dark:text-red-400 mt-0.5 flex-shrink-0" />
                          <div className="flex-1 space-y-1">
                            <p className="text-sm text-red-600 dark:text-red-400 font-medium">
                              {uploadedFile.error}
                            </p>
                            {uploadedFile.retryable && (
                              <div className="flex items-center gap-2 text-xs text-red-500 dark:text-red-400">
                                <Info className="w-3 h-3" />
                                <span>Click the retry button to try uploading again</span>
                              </div>
                            )}
                            {!uploadedFile.retryable && (
                              <div className="flex items-center gap-2 text-xs text-red-500 dark:text-red-400">
                                <Info className="w-3 h-3" />
                                <span>This error cannot be retried automatically. Please check the file format or try a different file.</span>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}