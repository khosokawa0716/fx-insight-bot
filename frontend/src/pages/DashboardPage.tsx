import { useDashboardData } from '../hooks'
import { formatCurrency } from '../lib/format'
import { useAuth } from '../contexts/AuthContext'

export function DashboardPage() {
  const { account, positions, health, loading, error, refetch } = useDashboardData()
  const { user, signOut } = useAuth()

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">
            FX Insight Bot Dashboard
          </h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">{user?.email}</span>
            <button
              onClick={signOut}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {error && (
          <div className="mb-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
            <button
              onClick={refetch}
              className="ml-4 text-sm underline hover:no-underline"
            >
              Retry
            </button>
          </div>
        )}

        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-blue-500 border-t-transparent"></div>
            <p className="mt-2 text-gray-600">Loading...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Account Balance Card */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-700 mb-4">
                Account Balance
              </h2>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-500">Balance</span>
                  <span className="font-medium">
                    {formatCurrency(account?.balance)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Available</span>
                  <span className="font-medium">
                    {formatCurrency(account?.availableAmount)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Margin</span>
                  <span className="font-medium">
                    {formatCurrency(account?.margin)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">P/L</span>
                  <span
                    className={`font-medium ${
                      account?.profitLoss && parseFloat(account.profitLoss) >= 0
                        ? 'text-green-600'
                        : 'text-red-600'
                    }`}
                  >
                    {formatCurrency(account?.profitLoss)}
                  </span>
                </div>
              </div>
            </div>

            {/* Health Status Card */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-700 mb-4">
                System Status
              </h2>
              <div className="space-y-3">
                <div className="flex items-center">
                  <span
                    className={`w-3 h-3 rounded-full mr-3 ${
                      health?.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
                    }`}
                  ></span>
                  <span className="text-gray-700">
                    {health?.status === 'healthy' ? 'System Online' : 'System Offline'}
                  </span>
                </div>
              </div>
            </div>

            {/* Positions Summary Card */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-700 mb-4">
                Positions Summary
              </h2>
              <div className="text-3xl font-bold text-gray-900">
                {positions.length}
              </div>
              <div className="text-sm text-gray-500">Active Positions</div>
            </div>

            {/* Positions List */}
            <div className="bg-white rounded-lg shadow p-6 md:col-span-2 lg:col-span-3">
              <h2 className="text-lg font-semibold text-gray-700 mb-4">
                Open Positions
              </h2>
              {positions.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  No open positions
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Symbol
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Side
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Size
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Entry Price
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          P/L
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {positions.map((position) => (
                        <tr key={position.positionId}>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {position.symbol}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <span
                              className={`px-2 py-1 rounded text-xs font-medium ${
                                position.side === 'BUY'
                                  ? 'bg-green-100 text-green-800'
                                  : 'bg-red-100 text-red-800'
                              }`}
                            >
                              {position.side}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {position.size}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {position.price}
                          </td>
                          <td
                            className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${
                              parseFloat(position.lossGain) >= 0
                                ? 'text-green-600'
                                : 'text-red-600'
                            }`}
                          >
                            {formatCurrency(position.lossGain)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Refresh Button */}
        <div className="mt-6 text-center">
          <button
            onClick={refetch}
            disabled={loading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Refreshing...' : 'Refresh Data'}
          </button>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-auto">
        <div className="max-w-7xl mx-auto px-4 py-4 text-center text-sm text-gray-500">
          FX Insight Bot - Display Only Dashboard
        </div>
      </footer>
    </div>
  )
}
