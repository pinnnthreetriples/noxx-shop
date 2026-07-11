import { useState } from 'react'
import {
  Edit,
  TabbedForm,
  FormTab,
  TextInput,
  NumberInput,
  BooleanInput,
  SelectInput,
  FormDataConsumer,
  Confirm,
  useNotify,
  minValue,
  maxValue,
} from 'react-admin'
import { Box, Button, Typography } from '@mui/material'
import { TranslatableInput } from '../components/TranslatableInput'

const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const LANGUAGES = [
  { id: 'en', name: 'English' },
  { id: 'ru', name: 'Русский' },
  { id: 'de', name: 'Deutsch' },
  { id: 'el', name: 'Ελληνικά' },
  { id: 'ro', name: 'Română' },
  { id: 'bg', name: 'Български' },
  { id: 'mo', name: 'Moldovenească' },
  { id: 'sr', name: 'Српски' },
  { id: 'tr', name: 'Türkçe' },
]

const rateOf = (fd: Record<string, unknown>): number => {
  if (fd.stars_to_usd_mode === 'manual' && fd.manual_stars_to_usd_rate) {
    return Number(fd.manual_stars_to_usd_rate)
  }
  return Number(fd.star_usd_rate) || 0
}

const UsdHint = ({ fd, source }: { fd: Record<string, unknown>; source: string }) => {
  const rate = rateOf(fd)
  const stars = Number(fd[source])
  if (!rate || !stars) return null
  // same gross-up as the backend applies to buyer-facing subscription prices
  const pct = Number(fd.withdrawal_commission_percent) || 0
  const gross = fd.withdrawal_commission_enabled && pct > 0
    ? Math.round(stars / (1 - Math.min(pct, 95) / 100))
    : stars
  return (
    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: -1, mb: 2 }}>
      ≈ ${(stars * rate).toFixed(2)}
      {gross !== stars ? ` · покупатель заплатит ${gross}⭐ (≈ $${(gross * rate).toFixed(2)})` : ''}
    </Typography>
  )
}

const ResetDataButton = () => {
  const notify = useNotify()
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleConfirm = async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('admin_token')
      const res = await fetch(`${apiUrl}/admin/settings/reset`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      notify('Все данные удалены — магазин как с нуля.', { type: 'success' })
      setOpen(false)
    } catch (err) {
      notify(`Не удалось сбросить данные: ${err instanceof Error ? err.message : 'неизвестная ошибка'}`, {
        type: 'error',
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box sx={{ maxWidth: 640 }}>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Полностью очистит магазин: товары, категории, теги, пользователей, заказы, платежи, промокоды,
        обращения в поддержку и уведомления. Администраторы и настройки сохранятся. Действие необратимо.
      </Typography>
      <Button color="error" variant="outlined" onClick={() => setOpen(true)}>
        Удалить все данные
      </Button>
      <Confirm
        isOpen={open}
        loading={loading}
        title="Полный сброс данных"
        content="Все товары, пользователи, заказы и другие данные будут безвозвратно удалены, магазин станет как с нуля. Продолжить?"
        confirm="Удалить всё"
        cancel="Отмена"
        onConfirm={handleConfirm}
        onClose={() => setOpen(false)}
      />
    </Box>
  )
}

const SettingsPage = () => (
  <Edit resource="settings" id={1} redirect={false} title="Настройки">
    <TabbedForm>
      <FormTab label="Общие">
        <SelectInput
          source="default_language"
          label="Язык по умолчанию"
          choices={LANGUAGES}
          helperText="Язык витрины до того, как пользователь выберет свой."
        />
        <BooleanInput source="notifications_enabled_by_default" label="Уведомления включены по умолчанию" />
      </FormTab>

      <FormTab label="Цены и Stars">
        <SelectInput
          source="stars_to_usd_mode"
          label="Режим курса Stars → USD"
          choices={[
            { id: 'manual', name: 'Вручную' },
            { id: 'auto', name: 'Стандартный (фиксированный)' },
          ]}
          helperText="«Стандартный» — фиксированный встроенный курс. «Вручную» — ваш курс ниже."
        />
        <FormDataConsumer>
          {({ formData }) =>
            formData.stars_to_usd_mode === 'manual' ? (
              <NumberInput
                source="manual_stars_to_usd_rate"
                label="Курс Stars → USD (вручную)"
                min={0.0001}
                validate={[minValue(0.0001, 'Курс должен быть больше нуля')]}
                helperText="Сколько $ стоит 1⭐, напр. 0.02"
              />
            ) : null
          }
        </FormDataConsumer>
        <BooleanInput
          source="withdrawal_commission_enabled"
          label="Компенсировать комиссию Telegram при выводе"
          helperText="Звёзды при выводе стоят примерно на 35% дешевле. Включи — и покупатель заплатит больше на эту комиссию, а тебе придёт твоя базовая цена (500⭐ → 770⭐)."
        />
        <FormDataConsumer>
          {({ formData }) =>
            formData.withdrawal_commission_enabled ? (
              <NumberInput
                source="withdrawal_commission_percent"
                label="Комиссия при выводе (%)"
                min={0}
                max={100}
                validate={[minValue(0), maxValue(100)]}
                helperText="Обычно ~35. Цена для покупателя = базовая ÷ (1 − процент/100)."
              />
            ) : null
          }
        </FormDataConsumer>
        <NumberInput source="sub_price_week_stars" label="Подписка: неделя (Stars)" min={1} validate={[minValue(1)]} />
        <FormDataConsumer>
          {({ formData }) => <UsdHint fd={formData} source="sub_price_week_stars" />}
        </FormDataConsumer>
        <NumberInput source="sub_price_month_stars" label="Подписка: месяц (Stars)" min={1} validate={[minValue(1)]} />
        <FormDataConsumer>
          {({ formData }) => <UsdHint fd={formData} source="sub_price_month_stars" />}
        </FormDataConsumer>
        <NumberInput source="sub_price_year_stars" label="Подписка: год (Stars)" min={1} validate={[minValue(1)]} />
        <FormDataConsumer>
          {({ formData }) => <UsdHint fd={formData} source="sub_price_year_stars" />}
        </FormDataConsumer>
      </FormTab>

      <FormTab label="Скидки">
        <NumberInput
          source="max_discount_percent"
          label="Макс. скидка (%)"
          min={0}
          max={100}
          validate={[minValue(0), maxValue(100)]}
          helperText="Глобальный потолок: итоговая скидка не превысит это значение."
        />
        <NumberInput source="discount_first_purchase_percent" label="Скидка на первую покупку (%)" min={0} max={100} validate={[minValue(0), maxValue(100)]} />
        <Box sx={{ display: 'flex', gap: 2 }}>
          <NumberInput source="discount_bulk_percent" label="Скидка за крупный заказ (%)" min={0} max={100} validate={[minValue(0), maxValue(100)]} />
          <NumberInput source="discount_bulk_min_items" label="Крупный заказ: от скольких видео" min={1} validate={[minValue(1)]} />
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <NumberInput source="discount_loyalty_percent" label="Постоянная скидка (%)" min={0} max={100} validate={[minValue(0), maxValue(100)]} />
          <NumberInput source="discount_loyalty_min_items" label="Постоянная скидка: от скольких купленных видео" min={1} validate={[minValue(1)]} />
        </Box>
      </FormTab>

      <FormTab label="Подписка">
        <BooleanInput source="subscription_coming_soon_enabled" label="Подписка «скоро» включена" />
        <FormDataConsumer>
          {({ formData }) =>
            formData.subscription_coming_soon_enabled ? (
              <TextInput source="subscription_coming_soon_text" label="Текст «Подписка скоро»" multiline fullWidth />
            ) : null
          }
        </FormDataConsumer>
      </FormTab>

      <FormTab label="Доставка">
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2, maxWidth: 640 }}>
          Полное видео покупатель получает прямо в боте. Создай приватный канал, добавь бота
          администратором, вставь сюда ID канала (вида <code>-100…</code>). Дальше у каждого товара
          указывай ссылку на сообщение с видео из этого канала.
        </Typography>
        <TextInput
          source="delivery_channel_id"
          label="ID канала доставки"
          helperText="Например -1001234567890. Бот должен быть админом этого канала."
        />
      </FormTab>

      <FormTab label="Тексты">
        <TranslatableInput base="terms_text" label="Текст условий использования" multiline />
        <TranslatableInput base="refund_policy_text" label="Текст политики возврата" multiline />
      </FormTab>

      <FormTab label="Опасная зона">
        <ResetDataButton />
      </FormTab>
    </TabbedForm>
  </Edit>
)

export default SettingsPage
