import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Skull } from 'lucide-react';

export default function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div className="flex min-h-screen items-center justify-center bg-dark-bg p-4">
      <div className="text-center">
        <div className="mb-6 flex justify-center">
          <div className="flex h-20 w-20 items-center justify-center rounded-full bg-gray-800">
            <Skull className="h-10 w-10 text-gray-600" />
          </div>
        </div>
        <h1 className="mb-2 text-6xl font-bold text-gray-600">404</h1>
        <p className="mb-2 text-xl text-gray-400">Page Not Found</p>
        <p className="mb-8 text-sm text-gray-600">
          The page you are looking for does not exist or has been moved.
        </p>
        <button
          onClick={() => navigate('/dashboard')}
          className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-6 py-3 text-sm font-medium text-white transition-colors hover:bg-blue-700"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Dashboard
        </button>
      </div>
    </div>
  );
}
