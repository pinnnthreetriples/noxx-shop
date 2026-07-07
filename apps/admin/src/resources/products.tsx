import { useState, type ChangeEvent, type ReactNode } from 'react'
import {
  List, Datagrid, TextField, NumberField, BooleanField, EditButton, DeleteButton,
  Edit, SimpleForm, TextInput, NumberInput, BooleanInput, SelectInput, SelectField, Create,
  ReferenceInput, ReferenceArrayInput, AutocompleteInput, AutocompleteArrayInput,
  ReferenceField, FunctionField,
  useInput, useNotify,
} from 'react-admin'
import { Box, Typography } from '@mui/material'
import { TranslatableInput } from '../components/TranslatableInput'

// Layout helpers: fields side by side instead of one per line
const Row = ({ children }: { children: ReactNode }) => (
  <Box sx={{ display: 'flex', gap: 2, width: '100%', '& > *': { flex: 1 } }}>{children}</Box>
)
const Section = ({ title }: { title: string }) => (
  <Typography variant="overline" sx={{ color: 'text.secondary', mt: 1, mb: -1, width: '100%' }}>{title}</Typography>
)

const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const mediaUrl = import.meta.env.VITE_MEDIA_PUBLIC_URL || 'http://localhost:9000'

// Upload a file to POST /admin/upload and put the returned relative path into
// the form field (cover_url / preview_video_url). Shows a live preview.
const MediaUploadInput = ({ source, label, accept, video = false }: {
  source: string; label: string; accept: string; video?: boolean
}) => {
  const { field } = useInput({ source })
  const notify = useNotify()
  const [busy, setBusy] = useState(false)
  const value = (field.value as string) || ''
  const src = value ? (/^https?:\/\//.test(value) ? value : `${mediaUrl}/${value.replace(/^\//, '')}`) : ''
  const onFile = async (e: ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (!f) return
    setBusy(true)
    try {
      const fd = new FormData()
      fd.append('file', f)
      const token = localStorage.getItem('admin_token')
      const res = await fetch(`${apiUrl}/admin/upload`, {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
        body: fd,
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      field.onChange((await res.json()).path)
      notify('Файл загружен', { type: 'success' })
    } catch (err) {
      notify(`Ошибка загрузки: ${err instanceof Error ? err.message : 'неизвестная'}`, { type: 'error' })
    } finally {
      setBusy(false)
      e.target.value = ''
    }
  }
  return (
    <div style={{ marginBottom: 20 }}>
      <div style={{ fontSize: 13, color: '#666', marginBottom: 8 }}>{label}</div>
      {src && (video
        ? <video key={src} src={src} controls muted style={{ maxWidth: 280, borderRadius: 8, display: 'block', marginBottom: 8 }} />
        : <img src={src} alt="" style={{ maxWidth: 280, maxHeight: 160, borderRadius: 8, display: 'block', marginBottom: 8 }} />)}
      <label style={{ display: 'inline-block', padding: '8px 16px', borderRadius: 4, background: '#1976d2', color: '#fff', fontSize: 14, cursor: busy ? 'wait' : 'pointer', opacity: busy ? 0.6 : 1 }}>
        {busy ? 'Загрузка…' : 'Загрузить файл'}
        <input type="file" accept={accept} onChange={onFile} disabled={busy} style={{ display: 'none' }} />
      </label>
    </div>
  )
}

const statusChoices = [
  { id: 'draft', name: 'Черновик' },
  { id: 'published', name: 'Опубликован' },
  { id: 'hidden', name: 'Скрыт' },
  { id: 'deleted', name: 'Удалён' },
]

const ProductFormFields = ({ create = false }: { create?: boolean }) => (
  <>
    <Row>
      <TextInput source="slug" />
      <SelectInput source="status" choices={statusChoices} defaultValue={create ? 'draft' : undefined} />
      <ReferenceInput source="category_id" reference="categories">
        <AutocompleteInput optionText={categoryOptionText} label="Категория" />
      </ReferenceInput>
    </Row>
    <Section title="Цена" />
    <Row>
      <NumberInput source="price_stars" label="Цена (Stars)" helperText="Пусто или 0 — посчитается из «Цена (USD)» по курсу" />
      <NumberInput source="usd_price_manual" label="Цена (USD)" helperText=" " />
      <SelectInput source="usd_price_mode" choices={[{ id: 'auto', name: 'Авто' }, { id: 'manual', name: 'Вручную' }]} defaultValue={create ? 'auto' : undefined} label="Цена в $ на витрине" helperText="Авто — из Stars по курсу" />
    </Row>
    <Section title="Медиа" />
    <Row>
      <Box>
        <MediaUploadInput source="cover_url" label="Обложка (изображение)" accept="image/*" />
        <TextInput source="cover_url" label="Обложка — URL/путь" fullWidth />
      </Box>
      <Box>
        <MediaUploadInput source="preview_video_url" label="Превью (короткое видео)" accept="video/mp4,video/webm,video/quicktime" video />
        <TextInput source="preview_video_url" label="Превью видео — URL/путь" fullWidth />
      </Box>
    </Row>
    <Section title="Контент и показатели" />
    <Row>
      <TextInput source="google_drive_link" />
      <TextInput source="google_drive_file_id" />
    </Row>
    <Row>
      {!create && <NumberInput source="display_views" />}
      {!create && <NumberInput source="display_purchases" />}
      <NumberInput source="trend_score" />
      <ReferenceArrayInput source="tag_ids" reference="tags">
        <AutocompleteArrayInput optionText="slug" />
      </ReferenceArrayInput>
    </Row>
    <Row>
      <BooleanInput source="is_premium" label="Премиум — подписчики получают бесплатно" />
    </Row>
    <Section title="Название" />
    <TranslatableInput base="title" label="Название" />
    <Section title="Описание" />
    <TranslatableInput base="description" label="Описание" multiline />
  </>
)

// dropdown label: human RU title when the API sent one, latin slug otherwise
const categoryOptionText = (c: { slug?: string; title_ru?: string }) =>
  c?.title_ru ? `${c.title_ru} (${c.slug})` : (c?.slug ?? '')

const productFilters = [
  <TextInput key="q" source="q" label="Поиск" alwaysOn />,
  <SelectInput key="status" source="status" label="Статус" choices={statusChoices} />,
]

export const ProductList = () => (
  <List filters={productFilters}>
    <Datagrid rowClick="edit">
      <TextField source="id" />
      <TextField source="slug" />
      <ReferenceField source="category_id" reference="categories" label="Категория" sortable={false}>
        <FunctionField render={categoryOptionText} />
      </ReferenceField>
      <SelectField source="status" choices={statusChoices} />
      <NumberField source="price_stars" />
      <NumberField source="usd_price_manual" />
      <NumberField source="trend_score" />
      <BooleanField source="is_premium" />
      <EditButton />
      <DeleteButton />
    </Datagrid>
  </List>
)

export const ProductEdit = () => (
  <Edit>
    <SimpleForm>
      <ProductFormFields />
    </SimpleForm>
  </Edit>
)

export const ProductCreate = () => (
  <Create>
    <SimpleForm>
      <ProductFormFields create />
    </SimpleForm>
  </Create>
)
