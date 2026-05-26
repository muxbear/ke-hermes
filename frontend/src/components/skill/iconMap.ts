import {
  Globe,
  Code2,
  Image,
  BarChart3,
  FolderOpen,
  Zap,
  Search,
  FileText,
  Database,
  Palette,
  Music,
  Wrench,
} from 'lucide-vue-next'
import type { Component } from 'vue'

export const SKILL_ICONS: Record<string, Component> = {
  Globe,
  Code2,
  Image,
  BarChart3,
  FolderOpen,
  Zap,
  Search,
  FileText,
  Database,
  Palette,
  Music,
  Wrench,
}

export function getSkillIcon(iconName: string): Component {
  return SKILL_ICONS[iconName] || Zap
}
