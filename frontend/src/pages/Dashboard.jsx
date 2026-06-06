import useAuthStore from '../store/authStore'
import { useNavigate } from 'react-router-dom'

export default function Dashboard() {
  const logout = useAuthStore((s) => s.logout)
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm px-6 py-4 flex justify-between items-center">
        <h1 className="text-xl font-bold text-blue-600">SmartStore AI</h1>
        <button
          onClick={handleLogout}
          className="text-sm text-gray-500 hover:text-red-500 transition"
        >
          Logout
        </button>
      </nav>
      <main className="p-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-6">Dashboard</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[
            { label: 'Total Products', value: '—', color: 'blue' },
            { label: 'Low Stock Alerts', value: '—', color: 'amber' },
            { label: 'Expired Items', value: '—', color: 'red' },
            { label: 'Suppliers', value: '—', color: 'green' },
          ].map((card) => (
            <div key={card.label} className="bg-white rounded-xl shadow-sm p-5 border border-gray-100">
              <p className="text-sm text-gray-500">{card.label}</p>
              <p className="text-3xl font-bold text-gray-800 mt-1">{card.value}</p>
            </div>
          ))}
        </div>
      </main>
    </div>
  )
}
