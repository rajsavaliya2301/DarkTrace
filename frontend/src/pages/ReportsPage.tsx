import { useState } from 'react';
import { useLocation } from 'react-router-dom';
import { Plus } from 'lucide-react';
import PageHeader from '../components/common/PageHeader';
import ReportGenerator from '../components/reports/ReportGenerator';
import ReportList from '../components/reports/ReportList';
import { useReports, useGenerateReport } from '../hooks/useReports';
import type { GenerateReportRequest } from '../types';

export default function ReportsPage() {
  const location = useLocation();
  const stateQuery = (location.state as { searchQuery?: string })?.searchQuery;

  const [showGenerator, setShowGenerator] = useState(!!stateQuery);
  const [page, setPage] = useState(1);

  const { data, isLoading, isError, refetch } = useReports({
    page,
    per_page: 25,
  });

  const generateReport = useGenerateReport();

  const handleGenerate = (formData: GenerateReportRequest) => {
    generateReport.mutate(formData, {
      onSuccess: () => setShowGenerator(false),
    });
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Reports"
        subtitle="Generate and manage threat intelligence reports"
      >
        <button
          onClick={() => setShowGenerator(true)}
          className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          <Plus className="h-4 w-4" />
          Generate Report
        </button>
      </PageHeader>

      <ReportList
        reports={data?.data}
        isLoading={isLoading}
        isError={isError}
        onRetry={() => refetch()}
        page={page}
        totalPages={data?.pagination?.total_pages || 1}
        onPageChange={setPage}
      />

      {showGenerator && (
        <ReportGenerator
          onSubmit={handleGenerate}
          onCancel={() => setShowGenerator(false)}
          isLoading={generateReport.isPending}
          prefillQuery={stateQuery}
        />
      )}
    </div>
  );
}
