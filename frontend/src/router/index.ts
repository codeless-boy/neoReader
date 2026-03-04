import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import ReaderView from '../views/ReaderView.vue'
import MainLayout from '../layouts/MainLayout.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: MainLayout,
      children: [
        {
          path: '',
          name: 'home',
          component: HomeView
        },
        {
          path: 'uploads',
          name: 'uploads',
          component: () => import('../views/UploadsView.vue')
        },
        {
          path: 'settings',
          name: 'settings',
          component: () => import('../views/SettingsView.vue')
        },
        {
          path: 'chat',
          name: 'chat',
          component: () => import('../views/ChatView.vue')
        }
      ]
    },
    {
      path: '/read/:id',
      name: 'read',
      component: ReaderView
    }
  ]
})

export default router
