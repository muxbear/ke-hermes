import {
  Code2, Globe, MessageSquare, FileText, Database,
  Sparkles, Cpu, Wrench, CheckCircle2, PauseCircle,
  AlertCircle, Lock, Package, Search, Terminal, Cloud,
} from 'lucide-vue-next'
import type { Component } from 'vue'

const map: Record<string, Component> = {
  Code2, Globe, MessageSquare, FileText, Database,
  Sparkles, Cpu, Wrench, CheckCircle2, PauseCircle,
  AlertCircle, Lock, Package, Search, Terminal, Cloud,
}

export function getToolIcon(name: string): Component {
  return map[name] || Wrench
}
