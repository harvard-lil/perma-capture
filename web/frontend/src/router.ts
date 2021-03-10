import { createRouter, createWebHistory } from 'vue-router'
import TheRoot from './components/TheRoot.vue'
import TheDocs from './components/TheDocs.vue'
import TheAccountSettingsPage from './components/TheAccountSettingsPage.vue'
import ThePasswordChange from './components/ThePasswordChange.vue'
import TheSignUpPage from './components/TheSignUpPage.vue'

const routes = [
  { path: '/', name: 'root', component: TheRoot },
  { path: '/sign-up/', name: 'sign_up', component: TheSignUpPage },
  { path: '/docs/', name: 'docs', component: TheDocs },
  { path: '/user/account/', name: 'account', component: TheAccountSettingsPage },
  { path: '/user/password_change/', name: 'password_change', component: ThePasswordChange }
]

export default createRouter({
  history: createWebHistory(),
  routes
})
