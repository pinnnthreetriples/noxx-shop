import {
  List, Datagrid, TextField, NumberField, DateField, Create, SimpleForm, TextInput, NumberInput,
} from 'react-admin'

export const NotificationList = () => (
  <List>
    <Datagrid>
      <TextField source="id" />
      <TextField source="title" />
      <NumberField source="product_id" />
      <DateField source="created_at" />
    </Datagrid>
  </List>
)

export const NotificationCreate = () => (
  <Create>
    <SimpleForm>
      <TextInput source="title" />
      <TextInput source="body" />
      <NumberInput source="product_id" />
    </SimpleForm>
  </Create>
)
