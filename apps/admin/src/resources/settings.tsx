import { Edit, SimpleForm, TextInput, NumberInput, BooleanInput, SelectInput } from 'react-admin'

const SettingsPage = () => (
  <Edit resource="settings" id={1} redirect={false} title="Настройки">
    <SimpleForm>
      <TextInput source="bot_name" label="Название бота" fullWidth />
      <BooleanInput source="support_enabled" label="Поддержка включена" />
      <BooleanInput source="content_18_plus_enabled" label="Контент 18+ включён" />
      <SelectInput
        source="default_language"
        label="Язык по умолчанию"
        choices={[
          { id: 'ru', name: 'Русский' },
          { id: 'en', name: 'Английский' },
        ]}
      />
      <SelectInput
        source="stars_to_usd_mode"
        label="Режим курса Stars → USD"
        choices={[
          { id: 'manual', name: 'Вручную' },
          { id: 'auto', name: 'Автоматически' },
        ]}
      />
      <NumberInput source="manual_stars_to_usd_rate" label="Курс Stars → USD (вручную)" />
      <NumberInput source="max_discount_percent" label="Макс. скидка (%)" />
      <NumberInput source="discount_first_purchase_percent" label="Скидка на первую покупку (%)" />
      <NumberInput source="discount_bulk_percent" label="Скидка за крупный заказ (%)" />
      <NumberInput source="discount_bulk_min_items" label="Крупный заказ: от скольких видео" />
      <NumberInput source="discount_loyalty_percent" label="Постоянная скидка (%)" />
      <NumberInput source="discount_loyalty_min_items" label="Постоянная скидка: от скольких купленных видео" />
      <NumberInput source="sub_price_week_stars" label="Подписка: неделя (Stars)" />
      <NumberInput source="sub_price_month_stars" label="Подписка: месяц (Stars)" />
      <NumberInput source="sub_price_year_stars" label="Подписка: год (Stars)" />
      <TextInput source="terms_text_en" label="Текст условий использования" multiline fullWidth />
      <TextInput source="refund_policy_text_en" label="Текст политики возврата" multiline fullWidth />
      <BooleanInput source="notifications_enabled_by_default" label="Уведомления включены по умолчанию" />
      <BooleanInput source="subscription_coming_soon_enabled" label="Подписка «скоро» включена" />
      <TextInput source="subscription_coming_soon_text" label="Текст «Подписка скоро»" multiline fullWidth />
    </SimpleForm>
  </Edit>
)

export default SettingsPage
