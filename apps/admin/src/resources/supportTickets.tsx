import { useState } from 'react'
import {
  List, Datagrid, TextField, DateField, EditButton,
  Edit, SimpleForm, SelectInput, SelectField, TextInput,
  Toolbar, SaveButton, Button, useRecordContext, useNotify, useRefresh,
} from 'react-admin'

// Backend has no DELETE /admin/support_tickets — hide react-admin's default delete button.
const SaveOnlyToolbar = () => <Toolbar><SaveButton /></Toolbar>

const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const statusChoices = [
  { id: 'open', name: 'Открыт' },
  { id: 'answered', name: 'Отвечен' },
  { id: 'closed', name: 'Закрыт' },
]

type TicketMessage = {
  id: number
  sender_type: string
  text: string | null
  file_url: string | null
  file_type: string | null
  created_at: string
}

const MessagesThread = () => {
  const record = useRecordContext<{ messages?: TicketMessage[] }>()
  const messages = record?.messages ?? []
  if (!messages.length) return <div style={{ color: '#888', padding: '8px 0' }}>Сообщений нет</div>
  return (
    <div style={{ width: '100%', marginBottom: 16 }}>
      {messages.map((m) => (
        <div
          key={m.id}
          style={{
            margin: '8px 0',
            padding: '10px 14px',
            borderRadius: 10,
            background: m.sender_type === 'user' ? 'rgba(25,118,210,.08)' : 'rgba(76,175,80,.10)',
            border: '1px solid rgba(0,0,0,.08)',
          }}
        >
          <div style={{ fontSize: 12, color: '#777', marginBottom: 4 }}>
            {m.sender_type === 'user' ? 'Пользователь' : 'Поддержка'} · {new Date(m.created_at).toLocaleString('ru-RU')}
          </div>
          <div style={{ whiteSpace: 'pre-wrap' }}>{m.text || (m.file_type ? `[${m.file_type}]` : '')}</div>
        </div>
      ))}
    </div>
  )
}

// Reply to the ticket author; delivered to the user via the bot.
// Mirrors the backend capability: POST /admin/support_tickets/{id}/reply.
const ReplyBox = () => {
  const record = useRecordContext<{ id: number }>()
  const notify = useNotify()
  const refresh = useRefresh()
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  if (!record) return null
  const handleClick = async () => {
    const body = text.trim()
    if (!body) return
    setLoading(true)
    try {
      const token = localStorage.getItem('admin_token')
      const res = await fetch(`${apiUrl}/admin/support_tickets/${record.id}/reply`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ text: body }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      notify(
        data.delivered ? 'Ответ отправлен пользователю' : 'Ответ сохранён (пользователь недоступен в боте)',
        { type: data.delivered ? 'success' : 'warning' },
      )
      setText('')
      refresh()
    } catch (err) {
      notify(
        `Не удалось отправить ответ: ${err instanceof Error ? err.message : 'неизвестная ошибка'}`,
        { type: 'error' },
      )
    } finally {
      setLoading(false)
    }
  }
  return (
    <div style={{ width: '100%', marginBottom: 16 }}>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Введите ответ пользователю…"
        rows={3}
        style={{ width: '100%', padding: 10, borderRadius: 8, border: '1px solid rgba(0,0,0,.2)', fontFamily: 'inherit', fontSize: 14 }}
      />
      <Button label="Отправить ответ" onClick={handleClick} disabled={loading || !text.trim()} />
    </div>
  )
}

export const SupportTicketList = () => (
  <List>
    <Datagrid rowClick="edit" bulkActionButtons={false}>
      <TextField source="id" />
      <TextField source="user_id" />
      <TextField source="topic" />
      <SelectField source="status" choices={statusChoices} />
      <DateField source="created_at" />
      <EditButton />
    </Datagrid>
  </List>
)

export const SupportTicketEdit = () => (
  <Edit>
    <SimpleForm toolbar={<SaveOnlyToolbar />}>
      <MessagesThread />
      <ReplyBox />
      <SelectInput source="status" choices={statusChoices} />
      <TextInput source="topic" disabled />
    </SimpleForm>
  </Edit>
)
