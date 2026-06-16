import { ref, computed, markRaw } from 'vue'
import type { Node, Edge } from '@vue-flow/core'
import { MarkerType } from '@vue-flow/core'
import {
  forceSimulation,
  forceLink,
  forceManyBody,
  forceCenter,
  forceCollide,
} from 'd3-force'
import KbGraphNode from '@/components/knowledgeBase/KbGraphNode.vue'
import KbGraphEdge from '@/components/knowledgeBase/KbGraphEdge.vue'
import type { Entity, Relation } from '@/types/knowledgeBase'

const ENTITY_COLORS: Record<string, string> = {
  '人物': '#60a5fa',
  '组织': '#a78bfa',
  '产品': '#34d399',
  '概念': '#fbbf24',
  '算法': '#f87171',
}

const NODE_WIDTH = 200
const NODE_HEIGHT = 60

export function useKnowledgeGraph() {
  const nodeTypes = { kbEntity: markRaw(KbGraphNode) }
  const edgeTypes = { kbRelation: markRaw(KbGraphEdge) }

  const graphNodes = ref<Node[]>([])
  const graphEdges = ref<Edge[]>([])
  const selectedEntityId = ref<string | null>(null)
  const searchQuery = ref('')
  const loadingLayout = ref(false)

  const entities = ref<Entity[]>([])
  const relations = ref<Relation[]>([])

  // 与选中实体关联的节点 ID 集合
  const connectedNodeIds = computed(() => {
    if (!selectedEntityId.value) return new Set<string>()
    const connected = new Set<string>([selectedEntityId.value])
    for (const r of relations.value) {
      if (r.from === selectedEntityId.value) connected.add(r.to)
      if (r.to === selectedEntityId.value) connected.add(r.from)
    }
    return connected
  })

  // 搜索匹配的节点 ID
  const matchedSearchIds = computed(() => {
    if (!searchQuery.value.trim()) return new Set<string>()
    const q = searchQuery.value.toLowerCase()
    return new Set(
      entities.value.filter((e) => e.name.toLowerCase().includes(q)).map((e) => e.id),
    )
  })

  function buildNodes(): Node[] {
    return entities.value.map((e) => ({
      id: e.id,
      type: 'kbEntity',
      position: { x: e.x || 0, y: e.y || 0 },
      draggable: true,
      data: {
        name: e.name,
        type: e.type,
        mentions: e.mentions,
        color: ENTITY_COLORS[e.type] || '#94a3b8',
        hovered: false,
        selected: e.id === selectedEntityId.value,
        dimmed: false,
      },
    }))
  }

  function buildEdges(): Edge[] {
    const entityIds = new Set(entities.value.map((e) => e.id))
    return relations.value
      .filter((r) => entityIds.has(r.from) && entityIds.has(r.to))
      .map((r) => ({
        id: r.id,
        source: r.from,
        target: r.to,
        type: 'kbRelation',
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: '#475569',
          width: 18,
          height: 18,
        },
        data: {
          label: r.label,
          highlighted: false,
          dimmed: false,
        },
      }))
  }

  function applyNodeData() {
    // 更新节点数据中的选中/dimmed 状态
    const dimmedIds = computeDimmedIds()
    graphNodes.value = graphNodes.value.map((n) => ({
      ...n,
      data: {
        ...n.data,
        selected: n.id === selectedEntityId.value,
        dimmed: dimmedIds.has(n.id),
      },
    }))
    graphEdges.value = graphEdges.value.map((e) => ({
      ...e,
      data: {
        ...e.data,
        highlighted:
          selectedEntityId.value != null &&
          (e.source === selectedEntityId.value || e.target === selectedEntityId.value),
        dimmed: selectedEntityId.value != null && e.source !== selectedEntityId.value && e.target !== selectedEntityId.value,
      },
    }))
  }

  function computeDimmedIds(): Set<string> {
    if (!selectedEntityId.value && !searchQuery.value.trim()) return new Set()
    const highlighted = new Set<string>()

    // 选中实体 + 关联实体
    if (selectedEntityId.value) {
      highlighted.add(selectedEntityId.value)
      for (const r of relations.value) {
        if (r.from === selectedEntityId.value) highlighted.add(r.to)
        if (r.to === selectedEntityId.value) highlighted.add(r.from)
      }
    }

    // 搜索匹配
    if (searchQuery.value.trim()) {
      const q = searchQuery.value.toLowerCase()
      for (const e of entities.value) {
        if (e.name.toLowerCase().includes(q)) highlighted.add(e.id)
      }
    }

    if (highlighted.size === 0) return new Set()
    return new Set(entities.value.filter((e) => !highlighted.has(e.id)).map((e) => e.id))
  }

  function selectEntity(id: string | null) {
    selectedEntityId.value = id
    if (id === selectedEntityId.value && id !== null) {
      // 再次点击取消选中
      selectedEntityId.value = null
    } else {
      selectedEntityId.value = id
    }
    applyNodeData()
  }

  function applyForceLayout() {
    if (entities.value.length === 0) return
    loadingLayout.value = true

    // d3-force 需要扁平的 {x, y} 属性，Vue Flow 用 {position: {x, y}}
    // 创建中间对象给 d3 操作，再映射回 Vue Flow 格式
    interface SimNode {
      id: string
      x: number
      y: number
      entityId: string
    }

    const simNodes: SimNode[] = entities.value.map((e) => ({
      id: e.id,
      x: e.x || (Math.random() - 0.5) * 600,
      y: e.y || (Math.random() - 0.5) * 400,
      entityId: e.id,
    }))

    const links = relations.value
      .filter((r) => simNodes.some((n) => n.id === r.from) && simNodes.some((n) => n.id === r.to))
      .map((r) => ({
        source: r.from,
        target: r.to,
      }))

    const sim = forceSimulation(simNodes)
      .force(
        'link',
        forceLink(links)
          .id((d: any) => d.id)
          .distance(160)
          .strength(0.4),
      )
      .force('charge', forceManyBody().strength(-600))
      .force('center', forceCenter(0, 0))
      .force('collide', forceCollide(55))
      .stop()

    for (let i = 0; i < 300; i++) {
      sim.tick()
    }

    // 将 d3 计算的位置写回实体和 Vue Flow 节点
    const nodeMap = new Map(simNodes.map((n) => [n.id, n]))
    for (const ent of entities.value) {
      const sn = nodeMap.get(ent.id)
      if (sn) {
        ent.x = sn.x
        ent.y = sn.y
      }
    }

    graphNodes.value = buildNodes().map((n) => ({
      ...n,
      position: { x: n.position.x, y: n.position.y },
      data: {
        ...n.data,
        selected: n.id === selectedEntityId.value,
      },
    }))
    graphEdges.value = buildEdges()

    applyNodeData()
    loadingLayout.value = false
  }

  function init(ents: Entity[], rels: Relation[]) {
    entities.value = ents
    relations.value = rels
    applyForceLayout()
  }

  function refresh(ents: Entity[], rels: Relation[]) {
    entities.value = ents
    relations.value = rels
    applyNodeData()
  }

  return {
    nodeTypes,
    edgeTypes,
    graphNodes,
    graphEdges,
    selectedEntityId,
    searchQuery,
    connectedNodeIds,
    matchedSearchIds,
    loadingLayout,
    selectEntity,
    applyForceLayout,
    init,
    refresh,
    applyNodeData,
  }
}
