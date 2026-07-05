import {
  List, Datagrid, TextField, NumberField, BooleanField, EditButton, DeleteButton,
  Edit, SimpleForm, TextInput, NumberInput, BooleanInput, SelectInput, Create,
} from 'react-admin'

const roleChoices = [
  { id: 'owner', name: 'Владелец' },
  { id: 'admin', name: 'Админ' },
  { id: 'support', name: 'Поддержка' },
  { id: 'content_manager', name: 'Контент-менеджер' },
]

export const AdminList = () => (
  <List>
    <Datagrid rowClick="edit">
      <TextField source="id" />
      <NumberField source="telegram_id" />
      <TextField source="name" />
      <TextField source="role" />
      <BooleanField source="active" />
      <EditButton />
      <DeleteButton />
    </Datagrid>
  </List>
)

export const AdminEdit = () => (
  <Edit>
    <SimpleForm>
      <TextInput source="name" />
      <SelectInput source="role" choices={roleChoices} />
      <BooleanInput source="active" />
    </SimpleForm>
  </Edit>
)

export const AdminCreate = () => (
  <Create>
    <SimpleForm>
      <NumberInput source="telegram_id" />
      <TextInput source="name" />
      <SelectInput source="role" choices={roleChoices} defaultValue="admin" />
      <BooleanInput source="active" defaultValue />
    </SimpleForm>
  </Create>
)
