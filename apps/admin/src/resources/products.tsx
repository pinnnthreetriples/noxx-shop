import { useState, type ChangeEvent } from 'react'
import {
  List, Datagrid, TextField, NumberField, BooleanField, EditButton, DeleteButton,
  Edit, SimpleForm, TextInput, NumberInput, BooleanInput, SelectInput, SelectField, Create,
  ReferenceInput, ReferenceArrayInput, AutocompleteInput, AutocompleteArrayInput,
  useInput, useNotify,
} from 'react-admin'

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

const LANGUAGES = ['en', 'ru', 'es', 'de', 'el', 'ro', 'bg', 'mo', 'sr', 'tr'] as const

const DescriptionInputs = () => (
  <>
    {LANGUAGES.map((lang) => (
      <TextInput
        key={`description_${lang}`}
        source={`description_${lang}`}
        label={`Описание (${lang.toUpperCase()})`}
        multiline
        fullWidth
      />
    ))}
  </>
)

const TitleInputs = () => (
  <>
    {LANGUAGES.map((lang) => (
      <TextInput
        key={`title_${lang}`}
        source={`title_${lang}`}
        label={`Название (${lang.toUpperCase()})`}
      />
    ))}
  </>
)

export const ProductList = () => (
  <List>
    <Datagrid rowClick="edit">
      <TextField source="id" />
      <TextField source="slug" />
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
      <TextInput source="slug" />
      <SelectInput source="status" choices={statusChoices} />
      <NumberInput source="price_stars" label="Цена (Stars)" helperText="Пусто или 0 — посчитается из «Цена (USD)» по курсу" />
      <SelectInput source="usd_price_mode" choices={[{ id: 'auto', name: 'Авто' }, { id: 'manual', name: 'Вручную' }]} label="Цена в $ на витрине" helperText="Авто — из Stars по курсу; Вручную — из поля «Цена (USD)»" />
      <NumberInput source="usd_price_manual" label="Цена (USD)" />
      <ReferenceInput source="category_id" reference="categories">
        <AutocompleteInput optionText="slug" />
      </ReferenceInput>
      <ReferenceArrayInput source="tag_ids" reference="tags">
        <AutocompleteArrayInput optionText="slug" />
      </ReferenceArrayInput>
      <MediaUploadInput source="cover_url" label="Обложка (изображение)" accept="image/*" />
      <TextInput source="cover_url" label="Обложка — URL/путь" fullWidth />
      <MediaUploadInput source="preview_video_url" label="Превью (короткое видео)" accept="video/mp4,video/webm,video/quicktime" video />
      <TextInput source="preview_video_url" label="Превью видео — URL/путь" fullWidth />
      <TextInput source="google_drive_link" />
      <TextInput source="google_drive_file_id" />
      <NumberInput source="display_views" />
      <NumberInput source="display_purchases" />
      <NumberInput source="trend_score" />
      <BooleanInput source="is_premium" />
      <BooleanInput source="available_for_subscription" />
      <TitleInputs />
      <DescriptionInputs />
    </SimpleForm>
  </Edit>
)

export const ProductCreate = () => (
  <Create>
    <SimpleForm>
      <TextInput source="slug" />
      <SelectInput source="status" choices={statusChoices} defaultValue="draft" />
      <NumberInput source="price_stars" label="Цена (Stars)" helperText="Пусто или 0 — посчитается из «Цена (USD)» по курсу" />
      <SelectInput source="usd_price_mode" choices={[{ id: 'auto', name: 'Авто' }, { id: 'manual', name: 'Вручную' }]} defaultValue="auto" label="Цена в $ на витрине" helperText="Авто — из Stars по курсу; Вручную — из поля «Цена (USD)»" />
      <NumberInput source="usd_price_manual" label="Цена (USD)" />
      <ReferenceInput source="category_id" reference="categories">
        <AutocompleteInput optionText="slug" />
      </ReferenceInput>
      <ReferenceArrayInput source="tag_ids" reference="tags">
        <AutocompleteArrayInput optionText="slug" />
      </ReferenceArrayInput>
      <MediaUploadInput source="cover_url" label="Обложка (изображение)" accept="image/*" />
      <TextInput source="cover_url" label="Обложка — URL/путь" fullWidth />
      <MediaUploadInput source="preview_video_url" label="Превью (короткое видео)" accept="video/mp4,video/webm,video/quicktime" video />
      <TextInput source="preview_video_url" label="Превью видео — URL/путь" fullWidth />
      <TextInput source="google_drive_link" />
      <TextInput source="google_drive_file_id" />
      <NumberInput source="trend_score" />
      <BooleanInput source="is_premium" />
      <BooleanInput source="available_for_subscription" />
      <TitleInputs />
      <DescriptionInputs />
    </SimpleForm>
  </Create>
)
