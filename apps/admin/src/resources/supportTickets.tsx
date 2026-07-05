import {
  List, Datagrid, TextField, DateField, EditButton,
  Edit, SimpleForm, SelectInput, SelectField, TextInput,
  Toolbar, SaveButton,
} from 'react-admin'

// Backend has no DELETE /admin/support_tickets — hide react-admin's default delete button.
const SaveOnlyToolbar = () => <Toolbar><SaveButton /></Toolbar>

const statusChoices = [
  { id: 'open', name: 'Открыт' },
  { id: 'answered', name: 'Отвечен' },
  { id: 'closed', name: 'Закрыт' },
]

export const SupportTicketList = () => (
  <List>
    <Datagrid rowClick="edit" bulkActionButtons={false}>
      <TextField source="id" />
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
      <SelectInput source="status" choices={statusChoices} />
      <TextInput source="topic" disabled />
    </SimpleForm>
  </Edit>
)
