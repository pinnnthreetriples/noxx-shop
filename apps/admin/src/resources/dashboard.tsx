import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader } from '@mui/material'

const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

interface Summary {
  users: number
  products: number
  paid_orders: number
  total_revenue_stars: number
  open_support_tickets: number
}

const STATS: { key: keyof Summary; label: string }[] = [
  { key: 'users', label: 'Пользователи' },
  { key: 'products', label: 'Товары' },
  { key: 'paid_orders', label: 'Оплаченные заказы' },
  { key: 'total_revenue_stars', label: 'Выручка (Stars)' },
  { key: 'open_support_tickets', label: 'Открытые тикеты' },
]

const DashboardPage = () => {
  const [summary, setSummary] = useState<Summary | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const token = localStorage.getItem('admin_token')
    fetch(`${apiUrl}/admin/analytics/summary`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then(setSummary)
      .catch((e) => setError(String(e.message || e)))
  }, [])

  return (
    <div style={{ padding: 16 }}>
      <Card>
        <CardHeader title="Аналитика" />
        <CardContent>
          {error && <p>Не удалось загрузить данные: {error}</p>}
          {!error && !summary && <p>Загрузка…</p>}
          {summary && (
            <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
              {STATS.map(({ key, label }) => (
                <div key={key} style={{ minWidth: 170, padding: '14px 18px', borderRadius: 8, background: 'rgba(25,118,210,.06)', border: '1px solid rgba(25,118,210,.15)' }}>
                  <div style={{ fontSize: 13, color: '#666' }}>{label}</div>
                  <div style={{ fontSize: 28, fontWeight: 700 }}>{summary[key]}</div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default DashboardPage
