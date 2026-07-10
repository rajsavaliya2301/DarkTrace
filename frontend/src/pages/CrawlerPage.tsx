import { useState } from 'react';
import { Plus } from 'lucide-react';
import PageHeader from '../components/common/PageHeader';
import TargetList from '../components/crawler/TargetList';
import TargetForm from '../components/crawler/TargetForm';
import JobList from '../components/crawler/JobList';
import { useCrawlTargets, useCrawlJobs, useAddTarget, useTriggerCrawl } from '../hooks/useCrawler';
import type { AddTargetRequest } from '../types';

type Tab = 'targets' | 'jobs';

export default function CrawlerPage() {
  const [tab, setTab] = useState<Tab>('targets');
  const [showForm, setShowForm] = useState(false);
  const [jobPage, setJobPage] = useState(1);

  const {
    data: targetsData,
    isLoading: targetsLoading,
    isError: targetsError,
    refetch: refetchTargets,
  } = useCrawlTargets();

  const {
    data: jobsData,
    isLoading: jobsLoading,
    isError: jobsError,
    refetch: refetchJobs,
  } = useCrawlJobs({ page: jobPage, per_page: 25 });

  const addTarget = useAddTarget();
  const triggerCrawl = useTriggerCrawl();

  const handleAddTarget = (data: AddTargetRequest) => {
    addTarget.mutate(data, {
      onSuccess: () => setShowForm(false),
    });
  };

  const handleTriggerCrawl = (targetId: string) => {
    triggerCrawl.mutate(targetId);
  };

  const tabs: { key: Tab; label: string }[] = [
    { key: 'targets', label: 'Targets' },
    { key: 'jobs', label: 'Jobs' },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Crawler Management"
        subtitle="Manage crawl targets and monitor job status"
      >
        {tab === 'targets' && (
          <button
            onClick={() => setShowForm(true)}
            className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            <Plus className="h-4 w-4" />
            Add Target
          </button>
        )}
      </PageHeader>

      {/* Tabs */}
      <div className="flex gap-1 rounded-lg bg-dark-surface p-1 w-fit">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => {
              setTab(t.key);
              setJobPage(1);
            }}
            className={`rounded-md px-4 py-2 text-sm font-medium transition-colors ${
              tab === t.key
                ? 'bg-blue-600 text-white'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'targets' && (
        <TargetList
          targets={targetsData?.data}
          isLoading={targetsLoading}
          isError={targetsError}
          onRetry={() => refetchTargets()}
          onTriggerCrawl={handleTriggerCrawl}
        />
      )}

      {tab === 'jobs' && (
        <JobList
          jobs={jobsData?.data}
          isLoading={jobsLoading}
          isError={jobsError}
          onRetry={() => refetchJobs()}
          page={jobPage}
          totalPages={jobsData?.pagination?.total_pages || 1}
          onPageChange={setJobPage}
        />
      )}

      {showForm && (
        <TargetForm
          onSubmit={handleAddTarget}
          onCancel={() => setShowForm(false)}
          isLoading={addTarget.isPending}
        />
      )}
    </div>
  );
}
