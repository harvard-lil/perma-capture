import { createRouter, createWebHistory } from 'vue-router'
import TheDashboard from './components/TheDashboard.vue'
import TheDocs from './components/TheDocs.vue'

const routes = [
  { path: '/', name: 'dashboard', component: TheDashboard },
  { path: '/docs/', name: 'docs', component: TheDocs }
]

export default createRouter({
  history: createWebHistory(),
  routes
})
