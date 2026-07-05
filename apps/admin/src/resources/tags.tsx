import {
  List, Datagrid, TextField, EditButton, DeleteButton,
  Edit, SimpleForm, TextInput, Create,
} from 'react-admin'

const LANGUAGES = ['en', 'ru', 'es', 'de', 'el', 'ro', 'bg', 'mo', 'sr', 'tr'] as const

const TitleInputs = () => (
  <>
    {LANGUAGES.map((lang) => (
      <TextInput key={`title_${lang}`} source={`title_${lang}`} label={`Название (${lang.toUpperCase()})`} />
    ))}
  </>
)

export const TagList = () => (
  <List>
    <Datagrid rowClick="edit">
      <TextField source="id" />
      <TextField source="slug" />
      <EditButton />
      <DeleteButton />
    </Datagrid>
  </List>
)

export const TagEdit = () => (
  <Edit>
    <SimpleForm>
      <TextInput source="slug" />
      <TitleInputs />
    </SimpleForm>
  </Edit>
)

export const TagCreate = () => (
  <Create>
    <SimpleForm>
      <TextInput source="slug" />
      <TitleInputs />
    </SimpleForm>
  </Create>
)
