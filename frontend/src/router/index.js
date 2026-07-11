import { createRouter, createWebHistory } from 'vue-router'
import HomeView from "@/views/home/HomeView.vue";
import LoginView from "@/views/user/LoginView.vue";
import RegisterView from "@/views/user/RegisterView.vue";
import ResearchView from "@/views/chat/ResearchView.vue";
import ProjectsView from "@/views/project/ProjectsView.vue";
import ReportView from "@/views/report/ReportView.vue";
import ResetPwdView from "@/views/user/ResetPwdView.vue";
import NotFoundView from "@/views/error/NotFoundView.vue";
import { useUserStore } from "@/stores/user.js";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home-index',
      component: HomeView
    },
    {
      path: '/user/login',
      name: 'user-login-index',
      component: LoginView
    },
    {
      path: '/user/register',
      name: 'user-register-index',
      component: RegisterView
    },
    {
      path: '/user/resetpwd',
      name: 'user-resetpwd-index',
      component: ResetPwdView
    },
    {
      path: '/chat',
      name: 'chat-index',
      component: ResearchView,
      meta: { requiresAuth: true },
    },
    {
      path: '/project',
      name: 'project-index',
      component: ProjectsView,
      meta: { requiresAuth: true },
    },
    {
      path: '/report',
      name: 'report-index',
      component: ReportView,
      meta: { requiresAuth: true },
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: NotFoundView,
    },
  ],
})

const PUBLIC_ROUTES = new Set([
  'home-index',
  'user-login-index',
  'user-register-index',
  'user-resetpwd-index',
  'not-found',
])

router.beforeEach(async (to, from, next) => {
  if (PUBLIC_ROUTES.has(to.name)) {
    return next()
  }

  if (to.meta.requiresAuth) {
    const userStore = useUserStore()
    await userStore.waitForAuth()
    if (!userStore.isLogin()) {
      return next({ name: 'user-login-index' })
    }
  }

  next()
})

export default router
