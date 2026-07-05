import { useState, type MouseEvent } from 'react'
import {
  List, Datagrid, TextField, NumberField, DateField, EditButton,
  Edit, SimpleForm, SelectInput, SelectField,
  Button, useRecordContext, useNotify, useRefresh,
  Toolbar, SaveButton,
} from 'react-admin'

// Backend has no DELETE /admin/orders — hide react-admin's default delete button.
const SaveOnlyToolbar = () => <Toolbar><SaveButton /></Toolbar>

const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const statusChoices = [
  { id: 'pending', name: 'Ожидает оплаты' },
  { id: 'paid', name: 'Оплачен' },
  { id: 'failed', name: 'Ошибка' },
  { id: 'cancelled', name: 'Отменён' },
  { id: 'refunded_manual', name: 'Возврат (вручную)' },
]

// Re-deliver the digital links for a PAID order.
// Mirrors the backend capability: POST /admin/orders/{id}/resend-links.
// Only shown for paid orders (the backend rejects anything else with 404).
const ResendLinksButton = () => {
  const record = useRecordContext()
  const notify = useNotify()
  const refresh = useRefresh()
  const [loading, setLoading] = useState(false)
  if (!record || record.status !== 'paid') return null
  const handleClick = async (e: MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation() // don't trigger the row's rowClick="edit"
    setLoading(true)
    try {
      const token = localStorage.getItem('admin_token')
      const res = await fetch(`${apiUrl}/admin/orders/${record.id}/resend-links`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      notify('Ссылки отправлены покупателю повторно', { type: 'success' })
      refresh()
    } catch (err) {
      notify(
        `Не удалось отправить ссылки: ${err instanceof Error ? err.message : 'неизвестная ошибка'}`,
        { type: 'error' },
      )
    } finally {
      setLoading(false)
    }
  }
  return <Button label="Отправить ссылки повторно" onClick={handleClick} disabled={loading} />
}

export const OrderList = () => (
  <List>
    <Datagrid rowClick="edit" bulkActionButtons={false}>
      <TextField source="id" />
      <SelectField source="status" choices={statusChoices} />
      <NumberField source="total_stars" />
      <NumberField source="paid_stars" />
      <NumberField source="final_discount_percent" />
      <TextField source="subscription_plan" label="Подписка" />
      <DateField source="created_at" />
      <ResendLinksButton />
      <EditButton />
    </Datagrid>
  </List>
)

export const OrderEdit = () => (
  <Edit>
    <SimpleForm toolbar={<SaveOnlyToolbar />}>
      <SelectInput source="status" choices={statusChoices} />
      <ResendLinksButton />
    </SimpleForm>
  </Edit>
)