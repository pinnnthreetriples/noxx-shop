import { useCallback, useEffect, useState } from 'react'
import { useNotify } from 'react-admin'
import { Alert, Box, Button, Card, CardContent, CircularProgress, TextField, Typography } from '@mui/material'
import { QRCodeSVG } from 'qrcode.react'

const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function authHeaders(): HeadersInit {
  const token = localStorage.getItem('admin_token')
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }
}

interface StatusResponse {
  enabled: boolean
  required: boolean
}

interface SetupResponse {
  secret: string
  otpauth_uri: string
}

interface EnableResponse {
  backup_codes: string[]
}

/** Reads `{detail: {code}}` off a failed response and turns it into RU copy. */
async function errorMessage(res: Response): Promise<string> {
  const body = (await res.json().catch(() => null)) as { detail?: { code?: string } } | null
  if (body?.detail?.code === 'totp_invalid') return 'Неверный код. Попробуйте снова.'
  return `Ошибка (HTTP ${res.status})`
}

const SecurityPage = () => {
  const notify = useNotify()
  const [status, setStatus] = useState<StatusResponse | null>(null)
  const [setup, setSetup] = useState<SetupResponse | null>(null)
  const [backupCodes, setBackupCodes] = useState<string[] | null>(null)
  // Shared by the enable and disable forms below — only one is ever mounted at a time.
  const [code, setCode] = useState('')
  const [formError, setFormError] = useState('')
  const [loading, setLoading] = useState(false)

  const loadStatus = useCallback(async () => {
    const res = await fetch(`${apiUrl}/2fa/status`, { headers: authHeaders() })
    if (res.ok) setStatus(await res.json())
  }, [])

  useEffect(() => {
    loadStatus()
  }, [loadStatus])

  const startSetup = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${apiUrl}/2fa/setup`, { method: 'POST', headers: authHeaders() })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      setSetup(await res.json())
    } catch (err) {
      notify(err instanceof Error ? err.message : 'Не удалось начать настройку 2FA', { type: 'error' })
    } finally {
      setLoading(false)
    }
  }

  // POST {code} to a 2fa endpoint; returns the OK response or null (formError set).
  const postCode = async (path: string): Promise<Response | null> => {
    setLoading(true)
    setFormError('')
    try {
      const res = await fetch(`${apiUrl}/2fa/${path}`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ code }),
      })
      if (!res.ok) {
        setFormError(await errorMessage(res))
        return null
      }
      return res
    } finally {
      setLoading(false)
    }
  }

  const confirmEnable = async () => {
    const res = await postCode('enable')
    if (!res) return
    const data: EnableResponse = await res.json()
    setBackupCodes(data.backup_codes)
    setSetup(null)
    setCode('')
    await loadStatus()
  }

  const disable2fa = async () => {
    const res = await postCode('disable')
    if (!res) return
    setCode('')
    await loadStatus()
    notify('Двухфакторная аутентификация отключена', { type: 'info' })
  }

  const copyBackupCodes = () => {
    if (!backupCodes) return
    navigator.clipboard.writeText(backupCodes.join('\n'))
    notify('Backup-коды скопированы', { type: 'info' })
  }

  if (!status) {
    return (
      <Box sx={{ p: 3 }}>
        <CircularProgress size={24} />
      </Box>
    )
  }

  return (
    <Box sx={{ p: 3, maxWidth: 480 }}>
      <Typography variant="h5" sx={{ mb: 2 }}>
        Двухфакторная аутентификация
      </Typography>

      {status.required && !status.enabled && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          Для этого аккаунта 2FA обязательна — включите её, чтобы продолжить работу с админкой.
        </Alert>
      )}

      {backupCodes && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Alert severity="warning" sx={{ mb: 2 }}>
              Сохраните эти backup-коды в надёжном месте — они показываются только один раз.
            </Alert>
            <Box component="pre" sx={{ fontFamily: 'monospace', fontSize: 14, whiteSpace: 'pre-wrap', m: 0 }}>
              {backupCodes.join('\n')}
            </Box>
            <Button variant="outlined" onClick={copyBackupCodes} sx={{ mt: 2 }}>
              Скопировать все
            </Button>
          </CardContent>
        </Card>
      )}

      {status.enabled ? (
        <Card>
          <CardContent>
            <Typography sx={{ mb: 2 }}>2FA включена для этого аккаунта.</Typography>
            <TextField
              fullWidth
              label="Код из приложения или backup-код"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              error={!!formError}
              helperText={formError}
              margin="normal"
            />
            <Button color="error" variant="outlined" disabled={loading || !code} onClick={disable2fa}>
              Отключить 2FA
            </Button>
          </CardContent>
        </Card>
      ) : setup ? (
        <Card>
          <CardContent>
            <Typography sx={{ mb: 2 }}>Отсканируйте QR-код в приложении-аутентификаторе:</Typography>
            <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
              <QRCodeSVG value={setup.otpauth_uri} size={200} />
            </Box>
            <TextField
              fullWidth
              label="Секретный ключ"
              value={setup.secret}
              InputProps={{ readOnly: true }}
              margin="normal"
              onFocus={(e) => e.target.select()}
              helperText="Если не получается отсканировать QR — введите ключ вручную."
            />
            <TextField
              fullWidth
              label="Код из приложения"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              error={!!formError}
              helperText={formError}
              margin="normal"
              autoFocus
            />
            <Button variant="contained" disabled={loading || code.length < 6} onClick={confirmEnable}>
              Включить 2FA
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Button variant="contained" disabled={loading} onClick={startSetup}>
          Включить 2FA
        </Button>
      )}
    </Box>
  )
}

export default SecurityPage
