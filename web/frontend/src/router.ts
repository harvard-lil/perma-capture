import { createRouter, createWebHistory } from 'vue-router'
import TheRoot from './components/TheRoot.vue'
import TheDocsPage from './components/TheDocsPage.vue'
import TheSignUpPage from './components/TheSignUpPage.vue'
import TheLoginPage from './components/TheLoginPage.vue'
import TheAccountSettingsPage from './components/TheAccountSettingsPage.vue'
import ThePasswordChangePage from './components/ThePasswordChangePage.vue'
import ThePasswordResetPage from './components/ThePasswordResetPage.vue'

const routes = [
  { path: '/', name: 'root', component: TheRoot },
  { path: '/docs/', name: 'docs', component: TheDocsPage },
  { path: '/sign-up/', name: 'sign_up', component: TheSignUpPage },
  { path: '/user/login/', name: 'login', component: TheLoginPage },
  { path: '/user/account/', name: 'account', component: TheAccountSettingsPage },
  { path: '/user/password_change/', name: 'password_change', component: ThePasswordChangePage },
  { path: '/user/password_reset/', name: 'password_reset', component: ThePasswordResetPage }
]

export default createRouter({
  history: createWebHistory(),
  routes
})
