import { List, Datagrid, TextField, NumberField, DateField } from 'react-admin'

export const LinkDeliveryLogList = () => (
  <List>
    <Datagrid>
      <TextField source="id" />
      <NumberField source="user_id" />
      <NumberField source="order_id" />
      <NumberField source="product_id" />
      <TextField source="delivery_method" />
      <TextField source="status" />
      <DateField source="sent_at" />
    </Datagrid>
  </List>
)
