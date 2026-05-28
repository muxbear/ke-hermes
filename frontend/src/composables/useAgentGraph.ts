import { ref, computed, watch, markRaw } from 'vue'
import type { Node, Edge } from '@vue-flow/core'
import { MarkerType } from '@vue-flow/core'
import dagre from 'dagre'
import { useAgentStore } from '@/stores/agent'
import type { Agent } from '@/types/agent'
import AgentNode from '@/components/agent/AgentNode.vue'
import AgentEdge from '@/components/agent/AgentEdge.vue'

const NODE_WIDTH = 240
const NODE_HEIGHT = 130

export function useAgentGraph() {
  const agentStore = useAgentStore()

  const nodeTypes = { agent: markRaw(AgentNode) }
  const edgeTypes = { agent: markRaw(AgentEdge) }
  const graphNodes = ref<Node[]>([])
  const graphEdges = ref<Edge[]>([])

  const hasAgents = computed(() => agentStore.agents.length > 0)

  function buildNodes(): Node[] {
    const nodes: Node[] = []
    const main = agentStore.mainAgent
    if (!main) return nodes

    nodes.push({
      id: main.id,
      type: 'agent',
      position: { x: 0, y: 0 },
      data: { agent: main, isMain: true },
      draggable: true,
    })

    for (const sub of agentStore.subAgents) {
      nodes.push({
        id: sub.id,
        type: 'agent',
        position: { x: 0, y: 0 },
        data: { agent: sub, isMain: false },
        draggable: true,
      })
    }

    return nodes
  }

  function buildEdges(): Edge[] {
    const edges: Edge[] = []
    const main = agentStore.mainAgent
    if (!main) return edges

    for (const sub of agentStore.subAgents) {
      const isActive = sub.status === 'active'
      edges.push({
        id: `${main.id}->${sub.id}`,
        source: main.id,
        target: sub.id,
        type: 'agent',
        animated: isActive,
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: isActive ? '#8b5cf6' : '#6b7280',
          width: 20,
          height: 20,
        },
        data: { status: sub.status },
      })
    }

    return edges
  }

  function applyLayout() {
    const raw = buildNodes()
    if (raw.length === 0) {
      graphNodes.value = []
      graphEdges.value = []
      return
    }

    const g = new dagre.graphlib.Graph()
    g.setDefaultEdgeLabel(() => ({}))
    g.setGraph({ rankdir: 'TB', ranksep: 140, nodesep: 120, marginx: 80, marginy: 80 })

    for (const node of raw) {
      g.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT })
    }

    const mainNode = raw.find((n) => (n.data as { isMain: boolean }).isMain)
    const subNodes = raw.filter((n) => !(n.data as { isMain: boolean }).isMain)

    for (const sub of subNodes) {
      if (mainNode) {
        g.setEdge(mainNode.id, sub.id)
      }
    }

    dagre.layout(g)

    const hasLayout = g.node(raw[0].id) != null
    if (!hasLayout) {
      graphNodes.value = raw
      graphEdges.value = buildEdges()
      return
    }

    graphNodes.value = raw.map((node) => {
      const pos = g.node(node.id)
      if (!pos) return node
      return {
        ...node,
        position: {
          x: pos.x - NODE_WIDTH / 2,
          y: pos.y - NODE_HEIGHT / 2,
        },
      }
    })

    graphEdges.value = buildEdges()
  }

  watch(
    () => [agentStore.mainAgent, agentStore.subAgents],
    () => applyLayout(),
    { deep: true, immediate: true },
  )

  function onNodeClick({ node }: { node: Node }) {
    const agent = (node.data as { agent: Agent }).agent
    if (agent) {
      agentStore.selectAgent(agent.id)
    }
  }

  return {
    nodeTypes,
    edgeTypes,
    graphNodes,
    graphEdges,
    hasAgents,
    onNodeClick,
  }
}
