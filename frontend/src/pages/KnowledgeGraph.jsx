/**
 * KnowledgeHive - Knowledge Graph Visualization
 *
 * Interactive force-directed graph showing organizational knowledge
 * with entities, relationships, and document connections.
 */
import { useState, useEffect, useRef, useCallback } from "react";
import {
  Box,
  VStack,
  HStack,
  Text,
  Heading,
  Icon,
  Flex,
  Badge,
  Select,
  Spinner,
} from "@chakra-ui/react";
import { FiShare2, FiZoomIn, FiZoomOut, FiMaximize2 } from "react-icons/fi";
import { motion } from "framer-motion";

const MotionBox = motion(Box);

/* ------------------------------------------------------------------ */
/*  Demo graph data — represents organizational knowledge              */
/* ------------------------------------------------------------------ */
const DEMO_NODES = [
  // Projects
  { id: "project-atlas", label: "Project Atlas", type: "project", x: 0, y: 0 },
  { id: "migration-initiative", label: "Migration Initiative", type: "project", x: 0, y: 0 },
  { id: "api-gateway", label: "API Gateway", type: "project", x: 0, y: 0 },
  { id: "release-3.2", label: "Release 3.2", type: "project", x: 0, y: 0 },
  // People
  { id: "john-smith", label: "John Smith", type: "person", x: 0, y: 0 },
  { id: "sarah-chen", label: "Sarah Chen", type: "person", x: 0, y: 0 },
  { id: "mike-johnson", label: "Mike Johnson", type: "person", x: 0, y: 0 },
  { id: "eng-director", label: "Engineering Director", type: "person", x: 0, y: 0 },
  { id: "lisa-wang", label: "Lisa Wang", type: "person", x: 0, y: 0 },
  // Teams
  { id: "backend-team", label: "Backend Team", type: "team", x: 0, y: 0 },
  { id: "frontend-team", label: "Frontend Team", type: "team", x: 0, y: 0 },
  { id: "devops-team", label: "DevOps Team", type: "team", x: 0, y: 0 },
  // Documents
  { id: "arch-doc", label: "Architecture Doc", type: "document", x: 0, y: 0 },
  { id: "deploy-guide", label: "Deployment Guide", type: "document", x: 0, y: 0 },
  { id: "runbook", label: "Runbook", type: "document", x: 0, y: 0 },
  // Tickets
  { id: "jira-1234", label: "ATLAS-1234", type: "ticket", x: 0, y: 0 },
  { id: "jira-1235", label: "ATLAS-1235", type: "ticket", x: 0, y: 0 },
  { id: "jira-1240", label: "ATLAS-1240", type: "ticket", x: 0, y: 0 },
  // Technologies
  { id: "oauth", label: "OAuth 2.0", type: "technology", x: 0, y: 0 },
  { id: "kubernetes", label: "Kubernetes", type: "technology", x: 0, y: 0 },
];

const DEMO_EDGES = [
  { source: "john-smith", target: "project-atlas", label: "owns" },
  { source: "project-atlas", target: "migration-initiative", label: "contains" },
  { source: "migration-initiative", target: "eng-director", label: "approved by" },
  { source: "sarah-chen", target: "api-gateway", label: "leads" },
  { source: "api-gateway", target: "oauth", label: "implements" },
  { source: "mike-johnson", target: "backend-team", label: "member of" },
  { source: "john-smith", target: "backend-team", label: "leads" },
  { source: "sarah-chen", target: "frontend-team", label: "member of" },
  { source: "lisa-wang", target: "devops-team", label: "leads" },
  { source: "project-atlas", target: "arch-doc", label: "documented in" },
  { source: "project-atlas", target: "jira-1234", label: "tracked by" },
  { source: "api-gateway", target: "jira-1235", label: "tracked by" },
  { source: "migration-initiative", target: "jira-1240", label: "tracked by" },
  { source: "devops-team", target: "deploy-guide", label: "maintains" },
  { source: "devops-team", target: "runbook", label: "maintains" },
  { source: "devops-team", target: "kubernetes", label: "manages" },
  { source: "release-3.2", target: "project-atlas", label: "includes" },
  { source: "release-3.2", target: "api-gateway", label: "includes" },
  { source: "eng-director", target: "release-3.2", label: "approved" },
  { source: "lisa-wang", target: "deploy-guide", label: "authored" },
];

const TYPE_CONFIG = {
  project: { color: "#6366F1", label: "Project" },
  person: { color: "#10B981", label: "Person" },
  team: { color: "#F59E0B", label: "Team" },
  document: { color: "#3B82F6", label: "Document" },
  ticket: { color: "#EC4899", label: "Ticket" },
  technology: { color: "#8B5CF6", label: "Technology" },
};

/* ------------------------------------------------------------------ */
/*  Simple force simulation                                            */
/* ------------------------------------------------------------------ */
function useForceSimulation(nodes, edges, width, height) {
  const [positions, setPositions] = useState([]);
  const animFrame = useRef(null);

  useEffect(() => {
    if (!nodes.length || !width || !height) return;

    // Initialize positions in a circle
    const pos = nodes.map((n, i) => {
      const angle = (2 * Math.PI * i) / nodes.length;
      const r = Math.min(width, height) * 0.3;
      return {
        ...n,
        x: width / 2 + r * Math.cos(angle) + (Math.random() - 0.5) * 50,
        y: height / 2 + r * Math.sin(angle) + (Math.random() - 0.5) * 50,
        vx: 0,
        vy: 0,
      };
    });

    const idxMap = {};
    nodes.forEach((n, i) => (idxMap[n.id] = i));

    let iteration = 0;
    const maxIterations = 200;

    function step() {
      const alpha = Math.max(0.01, 1 - iteration / maxIterations);

      // Repulsion (all pairs)
      for (let i = 0; i < pos.length; i++) {
        for (let j = i + 1; j < pos.length; j++) {
          const dx = pos[j].x - pos[i].x;
          const dy = pos[j].y - pos[i].y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = (800 * alpha) / dist;
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;
          pos[i].vx -= fx;
          pos[i].vy -= fy;
          pos[j].vx += fx;
          pos[j].vy += fy;
        }
      }

      // Attraction (edges)
      edges.forEach((e) => {
        const si = idxMap[e.source];
        const ti = idxMap[e.target];
        if (si === undefined || ti === undefined) return;
        const dx = pos[ti].x - pos[si].x;
        const dy = pos[ti].y - pos[si].y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const force = (dist - 120) * 0.02 * alpha;
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;
        pos[si].vx += fx;
        pos[si].vy += fy;
        pos[ti].vx -= fx;
        pos[ti].vy -= fy;
      });

      // Center gravity
      pos.forEach((p) => {
        p.vx += (width / 2 - p.x) * 0.005 * alpha;
        p.vy += (height / 2 - p.y) * 0.005 * alpha;
      });

      // Apply velocity
      pos.forEach((p) => {
        p.vx *= 0.8;
        p.vy *= 0.8;
        p.x += p.vx;
        p.y += p.vy;
        // Boundary
        p.x = Math.max(60, Math.min(width - 60, p.x));
        p.y = Math.max(40, Math.min(height - 40, p.y));
      });

      setPositions([...pos]);
      iteration++;

      if (iteration < maxIterations) {
        animFrame.current = requestAnimationFrame(step);
      }
    }

    animFrame.current = requestAnimationFrame(step);
    return () => cancelAnimationFrame(animFrame.current);
  }, [nodes, edges, width, height]);

  return positions;
}

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */
export default function KnowledgeGraph() {
  const containerRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  const [selectedNode, setSelectedNode] = useState(null);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [zoom, setZoom] = useState(1);

  // Measure container
  useEffect(() => {
    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setDimensions({
          width: entry.contentRect.width,
          height: entry.contentRect.height,
        });
      }
    });
    if (containerRef.current) resizeObserver.observe(containerRef.current);
    return () => resizeObserver.disconnect();
  }, []);

  const positions = useForceSimulation(
    DEMO_NODES,
    DEMO_EDGES,
    dimensions.width,
    dimensions.height
  );

  const posMap = {};
  positions.forEach((p) => (posMap[p.id] = p));

  // Get connected edges for selected node
  const selectedEdges = selectedNode
    ? DEMO_EDGES.filter(
        (e) => e.source === selectedNode.id || e.target === selectedNode.id
      )
    : [];

  return (
    <Box px={8} py={8} maxW="1400px" mx="auto" h="calc(100vh - 32px)">
      {/* Header */}
      <HStack justify="space-between" mb={6}>
        <VStack spacing={1} align="start">
          <Heading
            size="lg"
            bgGradient="linear(to-r, brand.300, brand.500, brand.700)"
            bgClip="text"
          >
            Knowledge Graph
          </Heading>
          <Text color="hive.textMuted" fontSize="sm">
            Visualize organizational knowledge relationships and entity connections
          </Text>
        </VStack>

        {/* Stats */}
        <HStack spacing={4}>
          <Badge px={3} py={1} borderRadius="md" colorScheme="purple" variant="subtle">
            {DEMO_NODES.length} Nodes
          </Badge>
          <Badge px={3} py={1} borderRadius="md" colorScheme="blue" variant="subtle">
            {DEMO_EDGES.length} Edges
          </Badge>
          <Badge px={3} py={1} borderRadius="md" colorScheme="green" variant="subtle">
            {Object.keys(TYPE_CONFIG).length} Types
          </Badge>
        </HStack>
      </HStack>

      <Flex gap={5} h="calc(100% - 80px)">
        {/* Graph Canvas */}
        <Box
          ref={containerRef}
          flex="1"
          borderRadius="xl"
          bg="hive.card"
          border="1px solid"
          borderColor="hive.border"
          position="relative"
          overflow="hidden"
        >
          {/* Zoom Controls */}
          <VStack
            position="absolute"
            top={4}
            right={4}
            spacing={1}
            zIndex={10}
          >
            <Box
              as="button"
              p={2}
              borderRadius="md"
              bg="hive.surface"
              border="1px solid"
              borderColor="hive.border"
              color="hive.textMuted"
              _hover={{ color: "hive.text", borderColor: "brand.500" }}
              onClick={() => setZoom((z) => Math.min(z + 0.2, 3))}
            >
              <FiZoomIn size={16} />
            </Box>
            <Box
              as="button"
              p={2}
              borderRadius="md"
              bg="hive.surface"
              border="1px solid"
              borderColor="hive.border"
              color="hive.textMuted"
              _hover={{ color: "hive.text", borderColor: "brand.500" }}
              onClick={() => setZoom((z) => Math.max(z - 0.2, 0.3))}
            >
              <FiZoomOut size={16} />
            </Box>
            <Box
              as="button"
              p={2}
              borderRadius="md"
              bg="hive.surface"
              border="1px solid"
              borderColor="hive.border"
              color="hive.textMuted"
              _hover={{ color: "hive.text", borderColor: "brand.500" }}
              onClick={() => setZoom(1)}
            >
              <FiMaximize2 size={16} />
            </Box>
          </VStack>

          {/* SVG Graph */}
          {dimensions.width > 0 && (
            <svg
              width="100%"
              height="100%"
              viewBox={`0 0 ${dimensions.width} ${dimensions.height}`}
              style={{ transform: `scale(${zoom})`, transformOrigin: "center", transition: "transform 0.3s" }}
            >
              {/* Edges */}
              {DEMO_EDGES.map((edge, i) => {
                const s = posMap[edge.source];
                const t = posMap[edge.target];
                if (!s || !t) return null;
                const isHighlighted =
                  selectedNode &&
                  (edge.source === selectedNode.id ||
                    edge.target === selectedNode.id);
                return (
                  <g key={`edge-${i}`}>
                    <line
                      x1={s.x}
                      y1={s.y}
                      x2={t.x}
                      y2={t.y}
                      stroke={isHighlighted ? "#FFB300" : "rgba(255,255,255,0.08)"}
                      strokeWidth={isHighlighted ? 2 : 1}
                      style={{ transition: "stroke 0.3s, stroke-width 0.3s" }}
                    />
                    {/* Edge label */}
                    {isHighlighted && (
                      <text
                        x={(s.x + t.x) / 2}
                        y={(s.y + t.y) / 2 - 6}
                        fill="#FFB300"
                        fontSize="9"
                        textAnchor="middle"
                        fontFamily="Inter, sans-serif"
                      >
                        {edge.label}
                      </text>
                    )}
                  </g>
                );
              })}

              {/* Nodes */}
              {positions.map((node) => {
                const config = TYPE_CONFIG[node.type] || { color: "#888" };
                const isSelected = selectedNode?.id === node.id;
                const isHovered = hoveredNode === node.id;
                const isConnected =
                  selectedNode &&
                  selectedEdges.some(
                    (e) =>
                      (e.source === node.id || e.target === node.id) &&
                      node.id !== selectedNode.id
                  );
                const dimmed =
                  selectedNode && !isSelected && !isConnected;

                return (
                  <g
                    key={node.id}
                    style={{ cursor: "pointer" }}
                    onClick={() =>
                      setSelectedNode(isSelected ? null : node)
                    }
                    onMouseEnter={() => setHoveredNode(node.id)}
                    onMouseLeave={() => setHoveredNode(null)}
                  >
                    {/* Glow */}
                    {(isSelected || isHovered) && (
                      <circle
                        cx={node.x}
                        cy={node.y}
                        r={24}
                        fill={config.color}
                        opacity={0.15}
                      />
                    )}
                    {/* Node circle */}
                    <circle
                      cx={node.x}
                      cy={node.y}
                      r={isSelected ? 16 : isHovered ? 14 : 12}
                      fill={config.color}
                      opacity={dimmed ? 0.2 : 1}
                      stroke={isSelected ? "#FFB300" : "transparent"}
                      strokeWidth={2}
                      style={{ transition: "r 0.2s, opacity 0.3s" }}
                    />
                    {/* Label */}
                    <text
                      x={node.x}
                      y={node.y + (isSelected ? 28 : 24)}
                      fill={dimmed ? "rgba(255,255,255,0.2)" : "rgba(255,255,255,0.8)"}
                      fontSize="10"
                      textAnchor="middle"
                      fontFamily="Inter, sans-serif"
                      fontWeight={isSelected ? "600" : "400"}
                      style={{ transition: "fill 0.3s" }}
                    >
                      {node.label}
                    </text>
                  </g>
                );
              })}
            </svg>
          )}

          {/* Loading state */}
          {positions.length === 0 && (
            <Flex position="absolute" inset="0" align="center" justify="center">
              <VStack spacing={3}>
                <Spinner size="lg" color="brand.400" />
                <Text color="hive.textMuted" fontSize="sm">
                  Computing graph layout...
                </Text>
              </VStack>
            </Flex>
          )}
        </Box>

        {/* Legend + Details Panel */}
        <VStack w="260px" spacing={4} flexShrink={0}>
          {/* Legend */}
          <Box
            p={4}
            borderRadius="xl"
            bg="hive.card"
            border="1px solid"
            borderColor="hive.border"
            w="100%"
          >
            <Text fontSize="sm" fontWeight="600" mb={3}>
              Entity Types
            </Text>
            <VStack spacing={2} align="stretch">
              {Object.entries(TYPE_CONFIG).map(([key, config]) => (
                <HStack key={key} spacing={2}>
                  <Box
                    w="10px"
                    h="10px"
                    borderRadius="full"
                    bg={config.color}
                    flexShrink={0}
                  />
                  <Text fontSize="xs" color="hive.textMuted">
                    {config.label}
                  </Text>
                  <Text fontSize="xs" color="hive.textMuted" ml="auto">
                    {DEMO_NODES.filter((n) => n.type === key).length}
                  </Text>
                </HStack>
              ))}
            </VStack>
          </Box>

          {/* Selected Node Details */}
          {selectedNode && (
            <MotionBox
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3 }}
              w="100%"
            >
              <Box
                p={4}
                borderRadius="xl"
                bg="hive.card"
                border="1px solid"
                borderColor={TYPE_CONFIG[selectedNode.type]?.color || "hive.border"}
                w="100%"
              >
                <HStack mb={3}>
                  <Box
                    w="12px"
                    h="12px"
                    borderRadius="full"
                    bg={TYPE_CONFIG[selectedNode.type]?.color}
                  />
                  <Text fontSize="sm" fontWeight="600">
                    {selectedNode.label}
                  </Text>
                </HStack>
                <Badge
                  colorScheme="purple"
                  variant="subtle"
                  fontSize="10px"
                  mb={3}
                >
                  {TYPE_CONFIG[selectedNode.type]?.label}
                </Badge>

                <Text fontSize="xs" color="hive.textMuted" mb={2} fontWeight="600">
                  Connections ({selectedEdges.length})
                </Text>
                <VStack spacing={1} align="stretch">
                  {selectedEdges.map((e, i) => {
                    const other =
                      e.source === selectedNode.id ? e.target : e.source;
                    const otherNode = DEMO_NODES.find((n) => n.id === other);
                    return (
                      <HStack key={i} spacing={2}>
                        <Text fontSize="10px" color="brand.400">
                          {e.label}
                        </Text>
                        <Text fontSize="10px" color="hive.textMuted">
                          →
                        </Text>
                        <Text fontSize="10px" color="hive.text">
                          {otherNode?.label || other}
                        </Text>
                      </HStack>
                    );
                  })}
                </VStack>
              </Box>
            </MotionBox>
          )}

          {!selectedNode && (
            <Box
              p={4}
              borderRadius="xl"
              bg="hive.card"
              border="1px solid"
              borderColor="hive.border"
              w="100%"
            >
              <Text fontSize="xs" color="hive.textMuted" textAlign="center">
                Click a node to see its connections and details
              </Text>
            </Box>
          )}
        </VStack>
      </Flex>
    </Box>
  );
}
