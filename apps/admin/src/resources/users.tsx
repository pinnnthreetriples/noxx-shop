import {
  List, Datagrid, TextField, NumberField, BooleanField, DateField, EditButton,
  Edit, SimpleForm, TextInput, BooleanInput, DateTimeInput,
  Toolbar, SaveButton,
} from 'react-admin'

// Backend has no DELETE /admin/users — hide react-admin's default delete button.
const SaveOnlyToolbar = () => <Toolbar><SaveButton /></Toolbar>

export const UserList = () => (
  <List>
    <Datagrid rowClick="edit" bulkActionButtons={false}>
      <TextField source="id" />
      <NumberField source="telegram_id" />
      <TextField source="username" />
      <TextField source="first_name" />
      <TextField source="last_name" />
      <TextField source="language_code" />
      <BooleanField source="is_blocked" />
      <BooleanField source="notifications_enabled" />
      <BooleanField source="age_confirmed" />
      <DateField source="premium_until" label="Премиум до" showTime />
      <EditButton />
    </Datagrid>
  </List>
)

export const UserEdit = () => (
  <Edit>
    <SimpleForm toolbar={<SaveOnlyToolbar />}>
      <TextInput source="username" />
      <TextInput source="first_name" />
      <TextInput source="last_name" />
      <TextInput source="selected_language" />
      <BooleanInput source="is_blocked" />
      <BooleanInput source="notifications_enabled" />
      <BooleanInput source="age_confirmed" />
      <DateTimeInput source="premium_until" label="Премиум до (пусто = нет подписки)" />
    </SimpleForm>
  </Edit>
)
