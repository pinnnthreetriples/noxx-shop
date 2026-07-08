import { useEffect, useRef, useState, type ChangeEvent, type ReactNode } from 'react'
import {
  List, Datagrid, TextField, NumberField, BooleanField, EditButton, DeleteButton,
  Edit, SimpleForm, TextInput, NumberInput, BooleanInput, SelectInput, SelectField, Create,
  ReferenceInput, ReferenceArrayInput, AutocompleteInput, AutocompleteArrayInput,
  ReferenceField, FunctionField,
  useInput, useNotify,
} from 'react-admin'
import { useFormContext } from 'react-hook-form'
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

const errText = (e: unknown) => (e instanceof Error ? e.message : 'неизвестная')

// Served URL for a stored relative path (or an absolute URL as-is).
const mediaSrc = (value: string) =>
  value ? (/^https?:\/\//.test(value) ? value : `${mediaUrl}/${value.replace(/^\//, '')}`) : ''

const btnStyle = (busy: boolean) => ({
  display: 'inline-block', padding: '8px 16px', borderRadius: 4, background: '#1976d2',
  color: '#fff', fontSize: 14, cursor: busy ? 'wait' : 'pointer', opacity: busy ? 0.6 : 1,
} as const)

// Upload a file/blob to POST /admin/upload; returns the served URL (an absolute
// CDN URL when R2 is configured, else a media-server path). Stored as-is.
// A filename is required for blobs so the backend extension check passes.
const uploadToMedia = async (file: Blob, filename?: string): Promise<string> => {
  const fd = new FormData()
  if (filename) fd.append('file', file, filename)
  else fd.append('file', file)
  const token = localStorage.getItem('admin_token')
  const res = await fetch(`${apiUrl}/admin/upload`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    body: fd,
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return (await res.json()).url as string
}

// Downscale an image blob to a JPEG whose longest side is <= maxDim (never
// upscaling). On any decode failure, resolves with the original blob so the
// upload is never blocked.
const shrinkImage = (source: Blob, maxDim = 1280, quality = 0.82): Promise<Blob> =>
  new Promise((resolve) => {
    const url = URL.createObjectURL(source)
    const img = new Image()
    img.addEventListener('error', () => { URL.revokeObjectURL(url); resolve(source) })
    img.addEventListener('load', () => {
      URL.revokeObjectURL(url)
      const scale = Math.min(1, maxDim / Math.max(img.width, img.height))
      const canvas = document.createElement('canvas')
      canvas.width = Math.round(img.width * scale)
      canvas.height = Math.round(img.height * scale)
      const ctx = canvas.getContext('2d')
      if (!ctx) { resolve(source); return }
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
      canvas.toBlob((blob) => resolve(blob || source), 'image/jpeg', quality)
    })
    img.src = url
  })

// Draw the current frame of a loaded, untainted <video> to a JPEG blob.
const captureFrame = (video: HTMLVideoElement): Promise<Blob> =>
  new Promise((resolve, reject) => {
    const w = video.videoWidth
    const h = video.videoHeight
    if (!w || !h) { reject(new Error('видео ещё не готово')); return }
    const canvas = document.createElement('canvas')
    canvas.width = w
    canvas.height = h
    const ctx = canvas.getContext('2d')
    if (!ctx) { reject(new Error('canvas недоступен')); return }
    ctx.drawImage(video, 0, 0, w, h)
    canvas.toBlob((blob) => (blob ? resolve(blob) : reject(new Error('кадр не получен'))), 'image/jpeg', 0.82)
  })

// Load a local blob URL into an offscreen <video>, seek slightly past the start
// (t=0 is often blank), and capture that frame. blob: URLs never taint canvas.
const captureFirstFrame = (blobUrl: string): Promise<Blob> =>
  new Promise((resolve, reject) => {
    const v = document.createElement('video')
    v.muted = true
    v.preload = 'auto'
    v.src = blobUrl
    v.addEventListener('error', () => reject(new Error('видео не декодируется')))
    v.addEventListener('loadeddata', () => {
      v.currentTime = Number.isFinite(v.duration) && v.duration > 0 ? Math.min(0.1, v.duration / 2) : 0.1
    })
    v.addEventListener('seeked', () => { captureFrame(v).then(resolve, reject) })
  })

// Upload an image to POST /admin/upload and put the returned relative path into
// the form field. Shows a live preview. Used for the manual cover image.
const MediaUploadInput = ({ source, label, accept }: {
  source: string; label: string; accept: string
}) => {
  const { field } = useInput({ source })
  const notify = useNotify()
  const [busy, setBusy] = useState(false)
  const src = mediaSrc((field.value as string) || '')
  const onFile = async (e: ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (!f) return
    setBusy(true)
    try {
      const isImage = accept.startsWith('image')
      field.onChange(isImage ? await uploadToMedia(await shrinkImage(f), 'cover.jpg') : await uploadToMedia(f))
      notify('Файл загружен', { type: 'success' })
    } catch (err) {
      notify(`Ошибка загрузки: ${errText(err)}`, { type: 'error' })
    } finally {
      setBusy(false)
      e.target.value = ''
    }
  }
  return (
    <div style={{ marginBottom: 20 }}>
      <div style={{ fontSize: 13, color: '#666', marginBottom: 8 }}>{label}</div>
      {src && <img src={src} alt="" style={{ maxWidth: 280, maxHeight: 160, borderRadius: 8, display: 'block', marginBottom: 8 }} />}
      <label style={btnStyle(busy)}>
        {busy ? 'Загрузка…' : 'Загрузить файл'}
        <input type="file" accept={accept} onChange={onFile} disabled={busy} style={{ display: 'none' }} />
      </label>
    </div>
  )
}

// Preview-video upload with cover-from-frame. The scrubbable <video> and frame
// capture are driven by a local blob: URL (same-origin, never taints canvas) so
// canvas.toBlob() works; the served cross-origin URL is only shown when editing
// without reselecting, in which case capture is unavailable (no local File).
const PreviewVideoInput = () => {
  const { field } = useInput({ source: 'preview_video_url' })
  const { setValue, getValues } = useFormContext()
  const notify = useNotify()
  const [busy, setBusy] = useState(false)
  const [objUrl, setObjUrl] = useState('')
  const videoRef = useRef<HTMLVideoElement>(null)

  useEffect(() => {
    if (!objUrl) return
    return () => URL.revokeObjectURL(objUrl)
  }, [objUrl])

  const setCover = async (blob: Blob) => {
    setValue('cover_url', await uploadToMedia(await shrinkImage(blob), 'cover.jpg'), { shouldDirty: true })
  }

  const onFile = async (e: ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (!f) return
    const url = URL.createObjectURL(f)
    setObjUrl(url)
    setBusy(true)
    try {
      field.onChange(await uploadToMedia(f))
      notify('Видео загружено', { type: 'success' })
      if (!getValues('cover_url')) {
        try {
          await setCover(await captureFirstFrame(url))
          notify('Обложка создана из первого кадра', { type: 'success' })
        } catch (err) {
          notify(`Не удалось создать обложку: ${errText(err)}`, { type: 'warning' })
        }
      }
    } catch (err) {
      notify(`Ошибка загрузки: ${errText(err)}`, { type: 'error' })
    } finally {
      setBusy(false)
      e.target.value = ''
    }
  }

  const makeCover = async () => {
    const v = videoRef.current
    if (!v) return
    setBusy(true)
    try {
      await setCover(await captureFrame(v))
      notify('Обложка сделана из этого кадра', { type: 'success' })
    } catch (err) {
      notify(`Не удалось сделать обложку: ${errText(err)}`, { type: 'error' })
    } finally {
      setBusy(false)
    }
  }

  const src = objUrl || mediaSrc((field.value as string) || '')
  return (
    <div style={{ marginBottom: 20 }}>
      <div style={{ fontSize: 13, color: '#666', marginBottom: 8 }}>Превью (короткое видео)</div>
      {src && <video key={src} ref={videoRef} src={src} controls muted style={{ maxWidth: 280, borderRadius: 8, display: 'block', marginBottom: 8 }} />}
      <label style={btnStyle(busy)}>
        {busy ? 'Загрузка…' : 'Загрузить файл'}
        <input type="file" accept="video/mp4,video/webm,video/quicktime" onChange={onFile} disabled={busy} style={{ display: 'none' }} />
      </label>
      {objUrl && (
        <button type="button" onClick={makeCover} disabled={busy} style={{ ...btnStyle(busy), border: 'none', marginLeft: 8 }}>
          📸 Сделать обложку из этого кадра
        </button>
      )}
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
        <PreviewVideoInput />
        <TextInput source="preview_video_url" label="Превью видео — URL/путь" fullWidth />
      </Box>
    </Row>
    <Section title="Контент и показатели" />
    <Row>
      <TextInput
        source="tg_message_id"
        label="Видео из канала (ссылка на сообщение)"
        fullWidth
        format={(v) => (v == null ? '' : String(v))}
        helperText="Залей полное видео в канал доставки → «Скопировать ссылку на сообщение» → вставь сюда. Приоритетнее Google Drive."
      />
    </Row>
    <Row>
      <TextInput source="google_drive_link" helperText="Запасной вариант, если видео нет в канале." />
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
