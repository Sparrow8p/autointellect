import { CarFront, ChartNoAxesCombined, GitCompareArrows, History, House, Wrench } from 'lucide-react'

export const sections = [
  { path: '/home', title: 'Главная', name: 'Home', icon: House },
  { path: '/car', title: 'Профиль авто', name: 'CarProfile', icon: CarFront },
  { path: '/repair', title: 'Оценка ремонта', name: 'RepairEstimate', icon: Wrench },
  { path: '/valuation', title: 'Стоимость авто', name: 'CarValuation', icon: ChartNoAxesCombined },
  { path: '/scenarios', title: 'Сценарии', name: 'Scenarios', icon: GitCompareArrows },
  { path: '/history', title: 'История расчётов', name: 'History', icon: History },
] as const

export const placeholderSections = sections.filter((section) => section.path !== '/home' && section.path !== '/car')

export const backFallbacks: Record<string, string | undefined> = {
  '/home': '/',
  '/car': '/home',
  '/repair': '/car',
  '/valuation': '/home',
  '/scenarios': '/home',
  '/history': '/home',
}
