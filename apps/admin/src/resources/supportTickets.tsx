import {
  List, Datagrid, TextField, DateField, EditButton,
  Edit, SimpleForm, SelectInput, SelectField, TextInput,
  Toolbar, SaveButton, useRecordContext,
} from 'react-admin'

// Backend has no DELETE /admin/support_tickets — hide react-admin's default delete button.
const SaveOnlyToolbar = () => <Toolbar><SaveButton /></Toolbar>

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
      <SelectInput source="status" choices={statusChoices} />
      <TextInput source="topic" disabled />
    </SimpleForm>
  </Edit>
)
