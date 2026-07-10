import { useForm } from 'react-hook-form';
import { X } from 'lucide-react';
import { REPORT_TYPES, REPORT_FORMATS } from '../../utils/constants';
import type { GenerateReportRequest, ReportParameters } from '../../types';

interface ReportGeneratorProps {
  onSubmit: (data: GenerateReportRequest) => void;
  onCancel: () => void;
  isLoading?: boolean;
  prefillAlertId?: string;
  prefillActorId?: string;
  prefillQuery?: string;
}

export default function ReportGenerator({
  onSubmit,
  onCancel,
  isLoading,
  prefillAlertId,
  prefillActorId,
  prefillQuery,
}: ReportGeneratorProps) {
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<GenerateReportRequest>({
    defaultValues: {
      type: prefillQuery ? 'search_results_export' : 'alert_report',
      format: prefillQuery ? 'json' : 'pdf',
      parameters: {
        alert_id: prefillAlertId || '',
        actor_id: prefillActorId || '',
        query: prefillQuery || '',
        include_evidence: true,
        include_blockchain_seal: false,
      } as ReportParameters,
    },
  });

  const reportType = watch('type');

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-xl border border-dark-border bg-dark-card shadow-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between border-b border-dark-border px-6 py-4">
          <h2 className="text-lg font-semibold text-gray-100">
            Generate Report
          </h2>
          <button
            onClick={onCancel}
            className="rounded p-1 text-gray-500 hover:text-gray-300"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form
          onSubmit={handleSubmit(onSubmit)}
          className="space-y-4 p-6"
        >
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300">
                Report Type
              </label>
              <select
                {...register('type', { required: true })}
                className="mt-1 w-full rounded-lg border border-dark-border bg-dark-surface px-3 py-2 text-sm text-gray-300 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                {REPORT_TYPES.map((type) => (
                  <option key={type} value={type}>
                    {type
                      .split('_')
                      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
                      .join(' ')}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300">
                Format
              </label>
              <select
                {...register('format', { required: true })}
                className="mt-1 w-full rounded-lg border border-dark-border bg-dark-surface px-3 py-2 text-sm text-gray-300 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                {REPORT_FORMATS.map((fmt) => (
                  <option key={fmt} value={fmt}>
                    {fmt.toUpperCase()}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {(reportType === 'alert_report' || !prefillAlertId) && (
            <div>
              <label className="block text-sm font-medium text-gray-300">
                Alert ID {reportType === 'alert_report' ? '(required)' : '(optional)'}
              </label>
              <input
                {...register(
                  'parameters.alert_id',
                  reportType === 'alert_report'
                    ? { required: 'Alert ID is required for alert reports' }
                    : {}
                )}
                placeholder="alert-uuid"
                className="mt-1 w-full rounded-lg border border-dark-border bg-dark-surface px-3 py-2 text-sm text-gray-100 placeholder-gray-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
              {errors.parameters?.alert_id && (
                <p className="mt-1 text-xs text-red-400">
                  {errors.parameters.alert_id.message}
                </p>
              )}
            </div>
          )}

          {reportType === 'actor_dossier' && (
            <div>
              <label className="block text-sm font-medium text-gray-300">
                Actor ID (required)
              </label>
              <input
                {...register('parameters.actor_id', {
                  required:
                    reportType === 'actor_dossier'
                      ? 'Actor ID is required for actor dossiers'
                      : false,
                })}
                placeholder="actor-uuid"
                className="mt-1 w-full rounded-lg border border-dark-border bg-dark-surface px-3 py-2 text-sm text-gray-100 placeholder-gray-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
              {errors.parameters?.actor_id && (
                <p className="mt-1 text-xs text-red-400">
                  {errors.parameters.actor_id.message}
                </p>
              )}
            </div>
          )}

          {(reportType === 'trend_report' || reportType === 'raw_export') && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300">
                  Date From
                </label>
                <input
                  type="date"
                  {...register('parameters.date_from')}
                  className="mt-1 w-full rounded-lg border border-dark-border bg-dark-surface px-3 py-2 text-sm text-gray-100 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300">
                  Date To
                </label>
                <input
                  type="date"
                  {...register('parameters.date_to')}
                  className="mt-1 w-full rounded-lg border border-dark-border bg-dark-surface px-3 py-2 text-sm text-gray-100 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>
            </div>
          )}

          {reportType === 'search_results_export' && (
            <div>
              <label className="block text-sm font-medium text-gray-300">
                Search Query <span className="text-red-400">*</span>
              </label>
              <input
                {...register('parameters.query', {
                  required: 'Search query is required for search results export',
                })}
                placeholder="Enter search query..."
                className="mt-1 w-full rounded-lg border border-dark-border bg-dark-surface px-3 py-2 text-sm text-gray-100 placeholder-gray-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
              {errors.parameters?.query && (
                <p className="mt-1 text-xs text-red-400">
                  {errors.parameters.query.message}
                </p>
              )}
            </div>
          )}

          <div className="space-y-3">
            <label className="flex items-center gap-3">
              <input
                type="checkbox"
                {...register('parameters.include_evidence')}
                className="rounded border-dark-border bg-dark-card text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-300">
                Include evidence (screenshots, raw content)
              </span>
            </label>
            <label className="flex items-center gap-3">
              <input
                type="checkbox"
                {...register('parameters.include_blockchain_seal')}
                className="rounded border-dark-border bg-dark-card text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-300">
                Include blockchain seal (tamper-proof evidence)
              </span>
            </label>
          </div>

          <div className="flex justify-end gap-3 border-t border-dark-border pt-4">
            <button
              type="button"
              onClick={onCancel}
              className="rounded-md border border-dark-border px-4 py-2 text-sm font-medium text-gray-300 hover:bg-dark-surface"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {isLoading ? 'Generating...' : 'Generate Report'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
