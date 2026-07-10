import { Download, Loader2 } from 'lucide-react';
import { cn } from '../../utils/cn';
import { formatFileSize } from '../../utils/formatters';

interface ReportDownloadProps {
  status: 'generating' | 'completed' | 'failed';
  downloadUrl?: string;
  fileSize?: number | null;
  onDownload?: () => void;
  className?: string;
}

export default function ReportDownload({
  status,
  downloadUrl,
  fileSize,
  onDownload,
  className,
}: ReportDownloadProps) {
  if (status === 'generating') {
    return (
      <span
        className={cn(
          'inline-flex items-center gap-2 rounded-md bg-blue-500/10 px-3 py-1.5 text-xs font-medium text-blue-400',
          className
        )}
      >
        <Loader2 className="h-3.5 w-3.5 animate-spin" />
        Generating...
      </span>
    );
  }

  if (status === 'failed') {
    return (
      <span
        className={cn(
          'inline-flex items-center gap-2 rounded-md bg-red-500/10 px-3 py-1.5 text-xs font-medium text-red-400',
          className
        )}
      >
        Failed
      </span>
    );
  }

  return (
    <div className={cn('flex items-center gap-2', className)}>
      {fileSize && (
        <span className="text-xs text-gray-500">
          {formatFileSize(fileSize)}
        </span>
      )}
      {downloadUrl ? (
        <a
          href={downloadUrl}
          className="inline-flex items-center gap-1.5 rounded-md bg-emerald-500/10 px-3 py-1.5 text-xs font-medium text-emerald-400 transition-colors hover:bg-emerald-500/20"
          download
        >
          <Download className="h-3.5 w-3.5" />
          Download
        </a>
      ) : (
        <button
          onClick={onDownload}
          className="inline-flex items-center gap-1.5 rounded-md bg-emerald-500/10 px-3 py-1.5 text-xs font-medium text-emerald-400 transition-colors hover:bg-emerald-500/20"
        >
          <Download className="h-3.5 w-3.5" />
          Download
        </button>
      )}
    </div>
  );
}
