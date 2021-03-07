import { createRouter, createWebHistory } from 'vue-router'
import TheDashboard from './components/TheDashboard.vue'

const routes = [
  { path: '/', name: 'dashboard', component: TheDashboard }
]

export default createRouter({
  history: createWebHistory(),
  routes
})
