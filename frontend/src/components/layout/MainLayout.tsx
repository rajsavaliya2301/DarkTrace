import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';
import { useAuthStore } from '../../store/authStore';

export default function MainLayout() {
  const isSidebarOpen = useAuthStore((s) => s.isSidebarOpen);
  const toggleSidebar = useAuthStore((s) => s.toggleSidebar);

  return (
    <div className="flex h-screen overflow-hidden bg-dark-bg">
      <Sidebar isOpen={isSidebarOpen} onToggle={toggleSidebar} />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header onMenuToggle={toggleSidebar} />
        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
