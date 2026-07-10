import { useState, FormEvent } from 'react'
import { useLogin, useNotify, Notification } from 'react-admin'
import { Box, Card, CardContent, TextField, Button, Typography } from '@mui/material'
import { TotpError } from './authProvider'

const LoginPage = () => {
  const login = useLogin()
  const notify = useNotify()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [otp, setOtp] = useState('')
  const [needsOtp, setNeedsOtp] = useState(false)
  const [otpError, setOtpError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setOtpError('')
    try {
      await login({ username, password, ...(needsOtp ? { otp } : {}) })
    } catch (err) {
      const code = err instanceof Error ? (err as TotpError).code : undefined
      if (code) {
        setNeedsOtp(true)
        setOtpError(code === 'totp_invalid' ? 'Неверный код. Попробуйте снова.' : '')
      } else {
        notify(err instanceof Error ? err.message : 'Ошибка входа', { type: 'error' })
      }
    } finally {
      setLoading(false)
    }
  }

  const goBack = () => {
    setNeedsOtp(false)
    setOtp('')
    setOtpError('')
  }

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        bgcolor: 'background.default',
      }}
    >
      <Card sx={{ minWidth: 320, maxWidth: 360 }}>
        <CardContent>
          <Typography variant="h5" sx={{ mb: 2 }}>
            Вход в админку
          </Typography>
          <form onSubmit={handleSubmit}>
            {!needsOtp && (
              <>
                <TextField
                  fullWidth
                  label="Email"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  margin="normal"
                  autoFocus
                />
                <TextField
                  fullWidth
                  type="password"
                  label="Пароль"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  margin="normal"
                />
              </>
            )}
            {needsOtp && (
              <>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1, mb: 1 }}>
                  Введите код из приложения или backup-код
                </Typography>
                <TextField
                  fullWidth
                  label="Код"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value)}
                  error={!!otpError}
                  helperText={otpError}
                  margin="normal"
                  autoFocus
                />
              </>
            )}
            <Button type="submit" fullWidth variant="contained" disabled={loading} sx={{ mt: 2 }}>
              {needsOtp ? 'Подтвердить' : 'Войти'}
            </Button>
            {needsOtp && (
              <Button fullWidth sx={{ mt: 1 }} onClick={goBack} disabled={loading}>
                Назад
              </Button>
            )}
          </form>
        </CardContent>
      </Card>
      <Notification />
    </Box>
  )
}

export default LoginPage
