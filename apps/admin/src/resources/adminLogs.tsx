import { List, Datagrid, TextField, NumberField, DateField } from 'react-admin'

export const AdminLogList = () => (
  <List>
    {/* Audit log: no backend DELETE endpoint, and it must not be erasable from the UI. */}
    <Datagrid bulkActionButtons={false}>
      <TextField source="id" />
      <NumberField source="admin_id" />
      <TextField source="action" />
      <TextField source="entity_type" />
      <NumberField source="entity_id" />
      <DateField source="created_at" />
    </Datagrid>
  </List>
)
