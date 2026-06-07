import Layout from '../components/Layout'
import ChatPanel from '../components/ChatPanel'

export default function Dashboard() {
  return (
    <Layout>
      <div className="p-6">
        <h1 className="text-2xl font-bold text-gray-800 mb-6">Dashboard</h1>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[
            { label: 'Total Products', value: '—' },
            { label: 'Low Stock Alerts', value: '—' },
            { label: 'Expired Items', value: '—' },
            { label: 'Suppliers', value: '—' },
          ].map((card) => (
            <div key={card.label} className="bg-white rounded-xl shadow-sm p-5 border border-gray-100">
              <p className="text-sm text-gray-500">{card.label}</p>
              <p className="text-3xl font-bold text-gray-800 mt-1">{card.value}</p>
            </div>
          ))}
        </div>
      </div>
      <ChatPanel />
    </Layout>
  )
}
