import { useState } from 'react'
import { useFormContext } from 'react-hook-form'
import { TextInput, useNotify } from 'react-admin'
import { Box, Button, IconButton, Collapse, MenuItem, Select, CircularProgress } from '@mui/material'

const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Must match the miniapp language switcher (and backend LANGUAGES).
const LANGUAGES: ReadonlyArray<readonly [string, string]> = [
  ['en', 'EN'], ['ru', 'RU'], ['de', 'DE'], ['el', 'EL'], ['ro', 'RO'],
  ['bg', 'BG'], ['mo', 'MO'], ['sr', 'SR'], ['tr', 'TR'],
]

interface Props {
  base: string      // 'title' | 'description' — fields are `${base}_${lang}`
  label: string
  multiline?: boolean
}

/**
 * One box you type into (in any source language) plus:
 *  - «Применить» — copy the text as-is into every still-empty language,
 *  - «Перевести» — auto-translate into all languages via the LLM endpoint,
 *  - a chevron that expands per-language fields so you can review/edit each.
 * All language values bind to the form fields `${base}_${lang}`, so the form
 * saves them exactly like the old flat inputs did.
 */
export function TranslatableInput({ base, label, multiline = false }: Props) {
  const { setValue, getValues } = useFormContext()
  const notify = useNotify()
  const [source, setSource] = useState('ru')
  const [busy, setBusy] = useState(false)
  const [open, setOpen] = useState(false)

  const primary = `${base}_${source}`

  const applyToEmpty = () => {
    const text = (getValues(primary) as string) || ''
    if (!text.trim()) { notify('Сначала введите текст', { type: 'warning' }); return }
    LANGUAGES.forEach(([code]) => {
      if (!getValues(`${base}_${code}`)) setValue(`${base}_${code}`, text, { shouldDirty: true })
    })
    notify('Текст применён ко всем пустым языкам', { type: 'info' })
  }

  const translate = async () => {
    const text = (getValues(primary) as string) || ''
    if (!text.trim()) { notify('Сначала введите текст', { type: 'warning' }); return }
    setBusy(true)
    try {
      const token = localStorage.getItem('admin_token')
      const resp = await fetch(`${apiUrl}/admin/translate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ text, source }),
      })
      if (!resp.ok) throw new Error(await resp.text())
      const data = await resp.json()
      Object.entries(data.translations as Record<string, string>).forEach(([code, val]) => {
        setValue(`${base}_${code}`, val, { shouldDirty: true })
      })
      setOpen(true)
      notify('Переведено на все языки', { type: 'success' })
    } catch (e) {
      notify(`Ошибка перевода: ${e instanceof Error ? e.message : String(e)}`, { type: 'error' })
    } finally {
      setBusy(false)
    }
  }

  return (
    <Box sx={{ width: '100%', mb: 1 }}>
      <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-start', flexWrap: 'wrap' }}>
        <Select
          size="small"
          value={source}
          onChange={(e) => setSource(String(e.target.value))}
          sx={{ minWidth: 76 }}
        >
          {LANGUAGES.map(([code, lbl]) => <MenuItem key={code} value={code}>{lbl}</MenuItem>)}
        </Select>
        <Box sx={{ flex: 1, minWidth: 220 }}>
          <TextInput source={primary} label={label} multiline={multiline} fullWidth helperText={false} />
        </Box>
        <Button onClick={applyToEmpty} size="small" variant="outlined">✓ Применить</Button>
        <Button onClick={translate} size="small" variant="contained" disabled={busy} sx={{ minWidth: 120 }}>
          {busy ? <CircularProgress size={16} color="inherit" /> : '🌐 Перевести'}
        </Button>
        <IconButton onClick={() => setOpen((o) => !o)} size="small" title="Показать все языки">
          {open ? '▾' : '▸'}
        </IconButton>
      </Box>
      <Collapse in={open}>
        <Box sx={{ pl: 2, mt: 1, borderLeft: '2px solid rgba(128,128,128,.3)' }}>
          {LANGUAGES.map(([code, lbl]) => (
            <TextInput
              key={code}
              source={`${base}_${code}`}
              label={`${label} (${lbl})`}
              multiline={multiline}
              fullWidth
              helperText={false}
            />
          ))}
        </Box>
      </Collapse>
    </Box>
  )
}
