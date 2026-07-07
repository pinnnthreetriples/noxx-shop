import {
  List, Datagrid, TextField, EditButton, DeleteButton,
  Edit, SimpleForm, TextInput, Create, SelectInput, SelectField,
} from 'react-admin'
import { TranslatableInput } from '../components/TranslatableInput'

const statusChoices = [
  { id: 'draft', name: 'Черновик' },
  { id: 'published', name: 'Опубликован' },
  { id: 'hidden', name: 'Скрыт' },
  { id: 'deleted', name: 'Удалён' },
]

export const CategoryList = () => (
  <List>
    <Datagrid rowClick="edit">
      <TextField source="id" />
      <TextField source="slug" />
      <SelectField source="status" choices={statusChoices} />
      <EditButton />
      <DeleteButton />
    </Datagrid>
  </List>
)

export const CategoryEdit = () => (
  <Edit>
    <SimpleForm>
      <TextInput source="slug" />
      <SelectInput source="status" choices={statusChoices} />
      <TranslatableInput base="title" label="Название" />
    </SimpleForm>
  </Edit>
)

export const CategoryCreate = () => (
  <Create>
    <SimpleForm>
      <TextInput source="slug" />
      <SelectInput source="status" choices={statusChoices} defaultValue="published" />
      <TranslatableInput base="title" label="Название" />
    </SimpleForm>
  </Create>
)
