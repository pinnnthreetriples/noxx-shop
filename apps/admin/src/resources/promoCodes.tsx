import {
  List, Datagrid, TextField, NumberField, BooleanField, DateField, EditButton, DeleteButton,
  Edit, SimpleForm, TextInput, NumberInput, BooleanInput, DateInput, Create,
} from 'react-admin'

export const PromoCodeList = () => (
  <List>
    <Datagrid rowClick="edit">
      <TextField source="id" />
      <TextField source="code" />
      <TextField source="discount_type" />
      <NumberField source="discount_value" />
      <BooleanField source="active" />
      <NumberField source="usage_limit" />
      <NumberField source="used_count" />
      <DateField source="starts_at" />
      <DateField source="expires_at" />
      <EditButton />
      <DeleteButton />
    </Datagrid>
  </List>
)

export const PromoCodeEdit = () => (
  <Edit>
    <SimpleForm>
      <TextInput source="code" />
      <TextInput source="discount_type" />
      <NumberInput source="discount_value" />
      <BooleanInput source="active" />
      <NumberInput source="usage_limit" />
      <NumberInput source="used_count" />
      <DateInput source="starts_at" />
      <DateInput source="expires_at" />
      <BooleanInput source="first_purchase_only" />
      <NumberInput source="min_cart_total" />
    </SimpleForm>
  </Edit>
)

export const PromoCodeCreate = () => (
  <Create>
    <SimpleForm>
      <TextInput source="code" />
      <TextInput source="discount_type" />
      <NumberInput source="discount_value" />
      <BooleanInput source="active" defaultValue />
      <NumberInput source="usage_limit" />
      <DateInput source="starts_at" />
      <DateInput source="expires_at" />
      <BooleanInput source="first_purchase_only" />
      <NumberInput source="min_cart_total" />
    </SimpleForm>
  </Create>
)
