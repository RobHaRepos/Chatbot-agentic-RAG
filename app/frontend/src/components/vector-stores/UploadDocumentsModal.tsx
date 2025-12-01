import { useState } from 'react';
import { useUploadDocuments } from '@/hooks/useVectorStores';
import { handleError, showSuccess } from '@/lib/errorHandling';
import { ERROR_TEMPLATES } from '@/lib/errorTemplates';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { IconLabel } from '@/components/ui/icon-label';
import { Upload, X, FileText, Loader2, CheckCircle2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface UploadDocumentsModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  storeId: number;
  storeName: string;
}

/**
 * FIXED: Removed unnecessary useCallback (not passed to memoized components)
 */
export function UploadDocumentsModal({
  open,
  onOpenChange,
  storeId,
  storeName,
}: Readonly<UploadDocumentsModalProps>) {
  const [files, setFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadComplete, setUploadComplete] = useState(false);

  const uploadDocuments = useUploadDocuments();

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const droppedFiles = Array.from(e.dataTransfer.files);
    setFiles(prev => [...prev, ...droppedFiles]);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files);
      setFiles(prev => [...prev, ...selectedFiles]);
    }
  };

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (files.length === 0) return;

    setUploadProgress(0);
    setUploadComplete(false);

    try {
      await uploadDocuments.mutateAsync({
        storeId,
        files,
        onProgress: setUploadProgress,
      });
      
      setUploadComplete(true);
      showSuccess('Upload Complete', `Successfully uploaded ${files.length} file(s)`);
      
      setTimeout(() => {
        setFiles([]);
        setUploadProgress(0);
        setUploadComplete(false);
        onOpenChange(false);
      }, 1500);
    } catch (error) {
      handleError(error, ...ERROR_TEMPLATES.DOCUMENT_UPLOAD(storeId, files.length));
    }
  };

  const handleClose = () => {
    if (!uploadDocuments.isPending) {
      setFiles([]);
      setUploadProgress(0);
      setUploadComplete(false);
      onOpenChange(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <Dialog 
      open={open} 
      onOpenChange={(newOpen) => {
        // Allow closing only if not uploading or user confirms
        if (!uploadDocuments.isPending || !newOpen) {
          handleClose();
        }
      }}
    >
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>
            <IconLabel icon={<Upload className="h-5 w-5" />} gap="sm">
              Upload Documents
            </IconLabel>
          </DialogTitle>
          <DialogDescription>
            Upload documents to <strong>{storeName}</strong>. 
            Supported formats: PDF, TXT, MD, DOCX
          </DialogDescription>
        </DialogHeader>
        
        <div className="py-4">
          {/* Drop zone - using label for accessibility */}
          <label
            htmlFor="file-upload"
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={cn(
              "block border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer",
              isDragging 
                ? "border-primary bg-primary/5" 
                : "border-muted-foreground/25 hover:border-muted-foreground/50",
              uploadDocuments.isPending && "pointer-events-none opacity-50"
            )}
          >
            <Upload className="mx-auto h-10 w-10 text-muted-foreground mb-4" />
            <p className="text-sm text-muted-foreground mb-2">
              Drag and drop files here, or
            </p>
            <span className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors border border-input bg-background hover:bg-accent hover:text-accent-foreground h-9 px-3">
              Browse Files
            </span>
          </label>
          <input
            id="file-upload"
            type="file"
            multiple
            accept=".pdf,.txt,.md,.docx"
            onChange={handleFileSelect}
            className="hidden"
            disabled={uploadDocuments.isPending}
          />

          {/* File list */}
          {files.length > 0 && (
            <div className="mt-4 space-y-2 max-h-[200px] overflow-y-auto">
              {files.map((file, index) => (
                <div
                  key={`${file.name}-${index}`}
                  className="p-2 rounded-md bg-muted/50 flex items-center justify-between"
                >
                  <IconLabel icon={<FileText className="h-4 w-4 text-muted-foreground" />} gap="md">
                    <div className="min-w-0">
                      <p className="text-sm font-medium truncate">{file.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {formatFileSize(file.size)}
                      </p>
                    </div>
                  </IconLabel>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => removeFile(index)}
                    disabled={uploadDocuments.isPending}
                    className="h-8 w-8 p-0"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          )}

          {/* Upload progress */}
          {uploadDocuments.isPending && (
            <div className="mt-4 space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span>Uploading...</span>
                <span>{uploadProgress}%</span>
              </div>
              <Progress value={uploadProgress} />
            </div>
          )}

          {/* Upload complete */}
          {uploadComplete && (
            <div className="mt-4">
              <IconLabel icon={<CheckCircle2 className="h-4 w-4" />} gap="sm" className="text-sm text-green-600">
                Upload complete!
              </IconLabel>
            </div>
          )}
        </div>
        
        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={handleClose}
            disabled={uploadDocuments.isPending}
          >
            Cancel
          </Button>
          <Button
            type="button"
            onClick={handleUpload}
            disabled={files.length === 0 || uploadDocuments.isPending || uploadComplete}
          >
            {uploadDocuments.isPending ? (
              <IconLabel icon={<Loader2 className="h-4 w-4 animate-spin" />} gap="sm">
                Uploading...
              </IconLabel>
            ) : (
              <IconLabel icon={<Upload className="h-4 w-4" />} gap="sm">
                Upload {files.length > 0 && `(${files.length})`}
              </IconLabel>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
