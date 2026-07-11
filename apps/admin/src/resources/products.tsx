import { useEffect, useRef, useState, type ChangeEvent, type ReactNode } from 'react'
import {
  List, Datagrid, TextField, NumberField, BooleanField, EditButton, DeleteButton,
  Edit, SimpleForm, TextInput, NumberInput, BooleanInput, SelectInput, SelectField, Create,
  ReferenceInput, ReferenceArrayInput, AutocompleteInput, AutocompleteArrayInput,
  ReferenceField, FunctionField, FormDataConsumer,
  useInput, useNotify, useGetOne,
} from 'react-admin'
import { useFormContext } from 'react-hook-form'
import { Box, Button, CircularProgress, Divider, IconButton, Typography } from '@mui/material'
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline'
import FileUploadOutlinedIcon from '@mui/icons-material/FileUploadOutlined'
import AddPhotoAlternateOutlinedIcon from '@mui/icons-material/AddPhotoAlternateOutlined'
import VideocamOutlinedIcon from '@mui/icons-material/VideocamOutlined'
import PhotoCameraOutlinedIcon from '@mui/icons-material/PhotoCameraOutlined'
import { TranslatableInput } from '../components/TranslatableInput'

// Layout helpers: fields side by side instead of one per line
const Row = ({ children }: { children: ReactNode }) => (
  <Box sx={{ display: 'flex', gap: 2, width: '100%', '& > *': { flex: 1 } }}>{children}</Box>
)
const Section = ({ title }: { title: string }) => (
  <Box sx={{ width: '100%', mt: 2 }}>
    <Typography variant="overline" sx={{ color: 'text.secondary', letterSpacing: '.08em' }}>{title}</Typography>
    <Divider />
  </Box>
)

const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const mediaUrl = import.meta.env.VITE_MEDIA_PUBLIC_URL || 'http://localhost:9000'

const errText = (e: unknown) => (e instanceof Error ? e.message : 'неизвестная')

// Served URL for a stored relative path (or an absolute URL as-is).
const mediaSrc = (value: string) =>
  value ? (/^https?:\/\//.test(value) ? value : `${mediaUrl}/${value.replace(/^\//, '')}`) : ''

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

// Card chrome shared by the two media inputs: label + trash icon in the
// header, a dashed click-to-upload area when empty, preview + actions when
// filled. Deleting clears the form field (saved as null), no URL editing.
const MediaCard = ({ label, filled, busy, accept, onFile, onClear, emptyIcon, emptyText, preview, actions }: {
  label: string; filled: boolean; busy: boolean; accept: string
  onFile: (e: ChangeEvent<HTMLInputElement>) => void; onClear: () => void
  emptyIcon: ReactNode; emptyText: string; preview: ReactNode; actions?: ReactNode
}) => (
  <Box sx={{ flex: 1, minWidth: 280, border: '1px solid', borderColor: 'divider', borderRadius: 2, p: 1.5 }}>
    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', minHeight: 32, mb: 0.5 }}>
      <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 600, letterSpacing: '.06em', textTransform: 'uppercase' }}>
        {label}
      </Typography>
      {filled && (
        <IconButton size="small" onClick={onClear} disabled={busy} title="Удалить"
          sx={{ color: 'text.secondary', '&:hover': { color: 'error.main' } }}>
          <DeleteOutlineIcon fontSize="small" />
        </IconButton>
      )}
    </Box>
    {filled ? (
      <>
        {preview}
        <Box sx={{ display: 'flex', gap: 1, mt: 1, flexWrap: 'wrap', alignItems: 'center' }}>
          <Button component="label" size="small" disabled={busy}
            startIcon={busy ? <CircularProgress size={14} /> : <FileUploadOutlinedIcon />}>
            Заменить
            <input type="file" hidden accept={accept} onChange={onFile} disabled={busy} />
          </Button>
          {actions}
        </Box>
      </>
    ) : (
      <Box component="label" sx={{
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 0.5,
        py: 4, borderRadius: 1.5, border: '1px dashed', borderColor: 'divider', color: 'text.secondary',
        cursor: busy ? 'wait' : 'pointer', transition: 'border-color .15s, color .15s',
        '&:hover': { borderColor: 'primary.main', color: 'primary.main', bgcolor: 'action.hover' },
      }}>
        {busy ? <CircularProgress size={22} /> : emptyIcon}
        <Typography variant="body2">{busy ? 'Загрузка…' : emptyText}</Typography>
        <input type="file" hidden accept={accept} onChange={onFile} disabled={busy} />
      </Box>
    )}
  </Box>
)

// Cover image: uploads to /admin/upload (downscaled to JPEG), shows a preview.
const CoverInput = () => {
  const { field } = useInput({ source: 'cover_url' })
  const notify = useNotify()
  const [busy, setBusy] = useState(false)
  const src = mediaSrc((field.value as string) || '')
  const onFile = async (e: ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (!f) return
    setBusy(true)
    try {
      field.onChange(await uploadToMedia(await shrinkImage(f), 'cover.jpg'))
      notify('Обложка загружена', { type: 'success' })
    } catch (err) {
      notify(`Ошибка загрузки: ${errText(err)}`, { type: 'error' })
    } finally {
      setBusy(false)
      e.target.value = ''
    }
  }
  return (
    <MediaCard
      label="Обложка" filled={!!src} busy={busy} accept="image/*"
      onFile={onFile} onClear={() => field.onChange(null)}
      emptyIcon={<AddPhotoAlternateOutlinedIcon />} emptyText="Загрузить изображение"
      preview={<img src={src} alt="" style={{ width: '100%', maxHeight: 220, objectFit: 'cover', borderRadius: 8, display: 'block' }} />}
    />
  )
}

// Preview-video upload with cover-from-frame. A freshly selected file plays
// from a local blob: URL (same-origin, never taints canvas). A saved video is
// loaded with crossOrigin=anonymous so capture works too — that needs CORS on
// the CDN (scripts/set_r2_cors.py); if the CDN refuses, we reload the video
// without CORS so playback still works and only the capture button is hidden.
const PreviewVideoInput = () => {
  const { field } = useInput({ source: 'preview_video_url' })
  const { setValue, getValues } = useFormContext()
  const notify = useNotify()
  const [busy, setBusy] = useState(false)
  const [objUrl, setObjUrl] = useState('')
  const [corsBlocked, setCorsBlocked] = useState(false)
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
    setBusy(true)
    try {
      field.onChange(await uploadToMedia(f))
      setObjUrl(url) // adopt the local preview only after the upload succeeded
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
      URL.revokeObjectURL(url)
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
  const remote = !objUrl && !!src
  const canCapture = !!objUrl || (remote && !corsBlocked)
  return (
    <MediaCard
      label="Превью (короткое видео)" filled={!!src} busy={busy}
      accept="video/mp4,video/webm,video/quicktime"
      onFile={onFile} onClear={() => { field.onChange(null); setObjUrl('') }}
      emptyIcon={<VideocamOutlinedIcon />} emptyText="Загрузить видео"
      preview={
        <>
          <video key={`${src}:${corsBlocked}`} ref={videoRef} src={src} controls muted
            crossOrigin={remote && !corsBlocked ? 'anonymous' : undefined}
            onError={() => { if (remote && !corsBlocked) setCorsBlocked(true) }}
            style={{ width: '100%', maxHeight: 220, borderRadius: 8, display: 'block' }} />
          {canCapture && (
            <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mt: 0.5 }}>
              Перемотай на нужный кадр — и он станет обложкой
            </Typography>
          )}
        </>
      }
      actions={canCapture && (
        <Button size="small" onClick={makeCover} disabled={busy} startIcon={<PhotoCameraOutlinedIcon />}>
          Обложка из кадра
        </Button>
      )}
    />
  )
}

const statusChoices = [
  { id: 'draft', name: 'Черновик' },
  { id: 'published', name: 'Опубликован' },
  { id: 'hidden', name: 'Скрыт' },
  { id: 'deleted', name: 'Удалён' },
]

// Mirrors backend pricing math exactly (admin_api/products/service.py +
// modules/pricing.py): base stars from USD, buyer-facing gross-up on top.
const starsFromUsd = (usd: number, rate: number) => Math.max(Math.round(usd / rate), 1)
const grossStars = (base: number, enabled: boolean, percent: number) =>
  !enabled || base <= 0 || percent <= 0 ? base : Math.round(base / (1 - Math.min(percent, 95) / 100))

type PricingSettings = {
  stars_to_usd_mode?: string
  manual_stars_to_usd_rate?: number | null
  star_usd_rate?: number
  withdrawal_commission_enabled?: boolean
  withdrawal_commission_percent?: number
}

// "Цена" section: typing a USD price live-derives the Stars price (the same
// rule the backend applies on save), and a preview line shows what the buyer
// will actually pay — including the withdrawal-commission gross-up.
const PricingFields = ({ create = false }: { create?: boolean }) => {
  const { setValue } = useFormContext()
  const { data: cfg } = useGetOne<PricingSettings & { id: number }>('settings', { id: 1 })
  // effective rate: manual (when valid) wins, else built-in; 0 while loading
  const rate = cfg?.stars_to_usd_mode === 'manual' && Number(cfg.manual_stars_to_usd_rate) > 0
    ? Number(cfg.manual_stars_to_usd_rate) : Number(cfg?.star_usd_rate) || 0
  const onUsdChange = (e: ChangeEvent<HTMLInputElement>) => {
    const usd = parseFloat(e.target.value)
    if (rate > 0 && Number.isFinite(usd) && usd > 0) {
      setValue('price_stars', starsFromUsd(usd, rate), { shouldDirty: true })
    }
  }
  return (
    <>
      <Row>
        <NumberInput source="price_stars" label="Цена (Stars)" helperText="База: столько Stars получишь ты" />
        <NumberInput
          source="usd_price_manual"
          label="Цена (USD)"
          onChange={onUsdChange}
          helperText={rate > 0 ? `Курс 1⭐ = $${rate} — Stars пересчитаются сами` : ' '}
        />
        <SelectInput source="usd_price_mode" choices={[{ id: 'auto', name: 'Авто' }, { id: 'manual', name: 'Вручную' }]} defaultValue={create ? 'auto' : undefined} label="Цена в $ на витрине" helperText="Авто — из Stars по курсу" />
      </Row>
      <FormDataConsumer>
        {({ formData }) => {
          const base = Number(formData.price_stars) || 0
          if (base <= 0 || !cfg) return null
          const commissionOn = !!cfg.withdrawal_commission_enabled
          const pct = Number(cfg.withdrawal_commission_percent) || 0
          const buyerStars = grossStars(base, commissionOn, pct)
          const buyerUsd = rate > 0 ? ` (≈ $${(buyerStars * rate).toFixed(2)})` : ''
          const net = rate > 0 ? ` · тебе ≈ $${(base * rate).toFixed(2)}` : ''
          return (
            <Typography variant="caption" sx={{ color: 'text.secondary', mt: -1.5, mb: 1 }}>
              Покупатель заплатит: <b>{buyerStars} ⭐</b>{buyerUsd}
              {commissionOn && pct > 0 ? ` · вкл. компенсацию комиссии ${pct}%${net}` : ''}
            </Typography>
          )
        }}
      </FormDataConsumer>
    </>
  )
}

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
    <PricingFields create={create} />
    <Section title="Медиа" />
    <Row>
      <CoverInput />
      <PreviewVideoInput />
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
      <NumberInput source="display_views" defaultValue={create ? 0 : undefined} helperText="Витрина показывает только это число" />
      <NumberInput source="display_purchases" defaultValue={create ? 0 : undefined} helperText="Витрина показывает только это число" />
      <NumberInput source="trend_score" helperText=" " />
      <ReferenceArrayInput source="tag_ids" reference="tags">
        <AutocompleteArrayInput optionText="slug" helperText=" " />
      </ReferenceArrayInput>
    </Row>
    {!create && (
      <Row>
        <NumberInput source="real_views" disabled helperText="Считается автоматически — открытия карточки" />
        <NumberInput source="real_purchases" disabled helperText="Считается автоматически — оплаченные заказы" />
      </Row>
    )}
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
  <ReferenceInput key="category" source="category_id" reference="categories">
    <AutocompleteInput optionText={categoryOptionText} label="Категория" />
  </ReferenceInput>,
  <SelectInput key="status" source="status" label="Статус" choices={statusChoices} />,
]

export const ProductList = () => (
  <List filters={productFilters}>
    <Datagrid rowClick="edit">
      <TextField source="id" />
      <FunctionField label="Обложка" sortable={false} render={(r: { cover_url?: string }) => (
        r?.cover_url
          ? <img src={mediaSrc(r.cover_url)} alt="" style={{ width: 56, height: 34, objectFit: 'cover', borderRadius: 4, display: 'block' }} />
          : null
      )} />
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
