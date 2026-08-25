import { useState, type MouseEvent } from 'react'
import {
  List, Datagrid, TextField, NumberField, DateField, EditButton,
  Edit, SimpleForm, SelectInput, SelectField, FunctionField,
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

// Setting an order to "paid" by hand settles nothing — no payment row, no links
// delivered, no premium extended — so the backend rejects that transition with 400.
// Display (and filtering) still needs the label, hence the separate list.
const editableStatusChoices = statusChoices.filter((c) => c.id !== 'paid')

const orderFilters = [<SelectInput key="status" source="status" choices={statusChoices} alwaysOn />]

// How the order was actually settled. Crypto orders are priced in Stars like any
// other order but are paid in coin, so they never show up in the bot's Star
// balance — the charge id prefix ("orb:") is the only thing that tells them apart.
const paymentMethod = (record: { payment?: { telegram_payment_charge_id?: string | null } | null }) => {
  const chargeId = record.payment?.telegram_payment_charge_id
  if (!chargeId) return '—'
  return chargeId.startsWith('orb:') ? 'Крипта' : 'Stars'
}

// Who ordered. The list endpoint already nests the user, so read it from the record:
// <ReferenceField> would make dataProvider.getMany fire one /admin/users/{id} request
// per row (dataProvider.ts:89), i.e. 50 requests for a full page.
const buyer = (record: { user?: { telegram_id?: number; username?: string | null } | null }) => {
  const user = record.user
  if (!user) return '—'
  return user.username ? `@${user.username}` : String(user.telegram_id ?? '—')
}

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
  <List filters={orderFilters} sort={{ field: 'id', order: 'DESC' }}>
    <Datagrid rowClick="edit" bulkActionButtons={false}>
      <TextField source="id" />
      <FunctionField source="user" render={buyer} sortable={false} />
      <SelectField source="status" choices={statusChoices} />
      <NumberField source="total_stars" />
      <NumberField source="paid_stars" />
      <NumberField source="approx_usd" emptyText="—" />
      <NumberField source="final_discount_percent" />
      <FunctionField source="payment_method" render={paymentMethod} sortable={false} />
      <TextField source="orbchain_track_id" emptyText="—" />
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
      <SelectInput source="status" choices={editableStatusChoices} />
      <ResendLinksButton />
    </SimpleForm>
  </Edit>
)