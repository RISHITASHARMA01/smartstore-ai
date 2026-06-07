import { NavLink, useNavigate } from 'react-router-dom'
import useAuthStore from '../store/authStore'

const navItems = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/products', label: 'Products' },
  { to: '/suppliers', label: 'Suppliers' },
  { to: '/purchase-orders', label: 'Purchase Orders' },
  { to: '/invoices', label: 'Invoices' },
  { to: '/reports', label: 'Reports' },
]

export default function Layout({ children }) {
  const logout = useAuthStore((s) => s.logout)
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen flex bg-gray-50">
      <aside className="w-56 bg-white border-r border-gray-200 flex flex-col shrink-0">
        <div className="px-6 py-5 border-b border-gray-100">
          <span className="text-lg font-bold text-blue-600">SmartStore AI</span>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center px-3 py-2 rounded-lg text-sm font-medium transition ${
                  isActive
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="px-3 py-4 border-t border-gray-100">
          <button
            onClick={handleLogout}
            className="w-full text-left px-3 py-2 text-sm text-gray-500 hover:text-red-500 rounded-lg transition"
          >
            Logout
          </button>
        </div>
      </aside>
      <div className="flex-1 overflow-auto">{children}</div>
    </div>
  )
}
