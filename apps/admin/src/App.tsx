import { Admin, Resource } from 'react-admin'
import dataProvider from './dataProvider'
import authProvider from './authProvider'
import { ProductList, ProductEdit, ProductCreate } from './resources/products'
import { CategoryList, CategoryEdit, CategoryCreate } from './resources/categories'
import { TagList, TagEdit, TagCreate } from './resources/tags'
import { UserList, UserEdit } from './resources/users'
import { OrderList, OrderEdit } from './resources/orders'
import { PromoCodeList, PromoCodeEdit, PromoCodeCreate } from './resources/promoCodes'
import { SupportTicketList, SupportTicketEdit } from './resources/supportTickets'
import { NotificationList, NotificationCreate } from './resources/notifications'
import { AdminList, AdminEdit, AdminCreate } from './resources/admins'
import { AdminLogList } from './resources/adminLogs'
import { LinkDeliveryLogList } from './resources/linkDeliveryLogs'
import SettingsPage from './resources/settings'
import DashboardPage from './resources/dashboard'
import { i18nProvider } from './i18n'

function App() {
  return (
    <Admin
      dataProvider={dataProvider}
      authProvider={authProvider}
      i18nProvider={i18nProvider}
      dashboard={DashboardPage}
    >
      <Resource name="products" list={ProductList} edit={ProductEdit} create={ProductCreate} />
      <Resource name="categories" list={CategoryList} edit={CategoryEdit} create={CategoryCreate} />
      <Resource name="tags" list={TagList} edit={TagEdit} create={TagCreate} />
      <Resource name="users" list={UserList} edit={UserEdit} />
      <Resource name="orders" list={OrderList} edit={OrderEdit} />
      <Resource name="promo_codes" list={PromoCodeList} edit={PromoCodeEdit} create={PromoCodeCreate} options={{ label: 'Промокоды' }} />
      <Resource name="support_tickets" list={SupportTicketList} edit={SupportTicketEdit} options={{ label: 'Поддержка' }} />
      <Resource name="notifications" list={NotificationList} create={NotificationCreate} options={{ label: 'Рассылки' }} />
      <Resource name="admins" list={AdminList} edit={AdminEdit} create={AdminCreate} options={{ label: 'Админы' }} />
      <Resource name="admin_logs" list={AdminLogList} options={{ label: 'Логи админов' }} />
      <Resource name="link_delivery_logs" list={LinkDeliveryLogList} options={{ label: 'Отправленные ссылки' }} />
      <Resource name="settings" list={SettingsPage} options={{ label: 'Настройки' }} />
    </Admin>
  )
}

export default App
