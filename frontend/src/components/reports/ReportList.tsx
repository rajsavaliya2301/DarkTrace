import DataTable, { type Column } from '../common/DataTable';
import ReportDownload from './ReportDownload';
import { formatDate, formatFileSize } from '../../utils/formatters';
import type { Report } from '../../types';
import { useDeleteReport } from '../../hooks/useReports';
import { Trash2 } from 'lucide-react';
import { useState } from 'react';
import ConfirmDialog from '../common/ConfirmDialog';

interface ReportListProps {
  reports: Report[] | undefined;
  isLoading: boolean;
  isError: boolean;
  onRetry?: () => void;
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export default function ReportList({
  reports,
  isLoading,
  isError,
  onRetry,
  page,
  totalPages,
  onPageChange,
}: ReportListProps) {
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const deleteReport = useDeleteReport();

  const columns: Column<Report>[] = [
    {
      key: 'type',
      header: 'Type',
      render: (report) => (
        <span className="text-sm text-gray-200 capitalize">
          {report.type.replace(/_/g, ' ')}
        </span>
      ),
    },
    {
      key: 'format',
      header: 'Format',
      width: '70px',
      render: (report) => (
        <span className="text-xs font-mono uppercase text-gray-400">
          {report.format}
        </span>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      width: '100px',
      render: (report) => (
        <ReportDownload
          status={report.status}
          downloadUrl={report.download_url}
          fileSize={report.file_size_bytes}
        />
      ),
    },
    {
      key: 'file_size',
      header: 'Size',
      width: '80px',
      hideOnMobile: true,
      render: (report) => (
        <span className="text-sm text-gray-400">
          {report.file_size_bytes
            ? formatFileSize(report.file_size_bytes)
            : '—'}
        </span>
      ),
    },
    {
      key: 'created_at',
      header: 'Created',
      width: '120px',
      hideOnMobile: true,
      render: (report) => (
        <span className="text-xs text-gray-400">
          {formatDate(report.created_at)}
        </span>
      ),
    },
    {
      key: 'actions',
      header: '',
      width: '50px',
      render: (report) => (
        <button
          onClick={(e) => {
            e.stopPropagation();
            setDeletingId(report.id);
          }}
          className="rounded p-1 text-gray-500 hover:text-red-400"
          aria-label="Delete report"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      ),
    },
  ];

  return (
    <>
      <DataTable
        columns={columns}
        data={reports || []}
        keyExtractor={(r) => r.id}
        isLoading={isLoading}
        isError={isError}
        onRetry={onRetry}
        page={page}
        totalPages={totalPages}
        onPageChange={onPageChange}
        emptyTitle="No reports"
        emptyMessage="Generate your first report to start documenting threat intelligence."
      />

      <ConfirmDialog
        isOpen={!!deletingId}
        onClose={() => setDeletingId(null)}
        onConfirm={() => {
          if (deletingId) {
            deleteReport.mutate(deletingId, {
              onSuccess: () => setDeletingId(null),
            });
          }
        }}
        title="Delete Report"
        message="Are you sure you want to delete this report? This action cannot be undone."
        confirmLabel="Delete"
        isLoading={deleteReport.isPending}
      />
    </>
  );
}
