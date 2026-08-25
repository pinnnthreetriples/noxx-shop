import { List, Datagrid, TextField, NumberField, DateField } from 'react-admin'

export const LinkDeliveryLogList = () => (
  <List>
    {/* Audit log: no backend DELETE endpoint, and it must not be erasable from the UI. */}
    <Datagrid bulkActionButtons={false}>
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
