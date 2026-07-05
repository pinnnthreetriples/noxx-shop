import {
  List, Datagrid, TextField, EditButton, DeleteButton,
  Edit, SimpleForm, TextInput, Create, SelectInput, SelectField,
} from 'react-admin'

const statusChoices = [
  { id: 'draft', name: 'Черновик' },
  { id: 'published', name: 'Опубликован' },
  { id: 'hidden', name: 'Скрыт' },
  { id: 'deleted', name: 'Удалён' },
]

const LANGUAGES = ['en', 'ru', 'es', 'de', 'el', 'ro', 'bg', 'mo', 'sr', 'tr'] as const

const TitleInputs = () => (
  <>
    {LANGUAGES.map((lang) => (
      <TextInput key={`title_${lang}`} source={`title_${lang}`} label={`Название (${lang.toUpperCase()})`} />
    ))}
  </>
)

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
      <TitleInputs />
    </SimpleForm>
  </Edit>
)

export const CategoryCreate = () => (
  <Create>
    <SimpleForm>
      <TextInput source="slug" />
      <SelectInput source="status" choices={statusChoices} defaultValue="published" />
      <TitleInputs />
    </SimpleForm>
  </Create>
)
