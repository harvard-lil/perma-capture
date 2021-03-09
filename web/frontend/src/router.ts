import { createRouter, createWebHistory } from 'vue-router'
import TheDashboard from './components/TheDashboard.vue'
import TheDocs from './components/TheDocs.vue'
import TheAccountSettings from './components/TheAccountSettings.vue'
import ThePasswordChange from './components/ThePasswordChange.vue'

const routes = [
  { path: '/', name: 'dashboard', component: TheDashboard },
  { path: '/docs/', name: 'docs', component: TheDocs },
  { path: '/user/account/', name: 'account', component: TheAccountSettings },
  { path: '/user/password_change/', name: 'password_change', component: ThePasswordChange }
]

export default createRouter({
  history: createWebHistory(),
  routes
})
