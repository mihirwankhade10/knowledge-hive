/**
 * KnowledgeHive - ChatWindow Component
 *
 * Chat interface with message bubbles, sources panel, confidence display,
 * and real-time agent step indicators via WebSocket.
 *
 * Phase 3: Uses WebSocket for live agent updates during queries,
 * falls back to REST if WebSocket connection fails.
 */
import { useState, useRef, useEffect, useCallback } from "react";
import {
  Box,
  VStack,
  HStack,
  Input,
  IconButton,
  Text,
  Flex,
  Badge,
  Spinner,
  Collapse,
  Divider,
  Tooltip,
  Progress,
} from "@chakra-ui/react";
import {
  FiSend,
  FiChevronDown,
  FiChevronUp,
  FiFileText,
  FiCheckCircle,
  FiLoader,
  FiCircle,
  FiZap,
} from "react-icons/fi";
import { queryKnowledge, queryKnowledgeWS } from "../services/api";

// Agent display config
const AGENT_LABELS = {
  retrieval: { label: "Retrieval", icon: "🔍", color: "blue" },
  validation: { label: "Validation", icon: "✅", color: "green" },
  response: { label: "Response", icon: "💬", color: "purple" },
  cache: { label: "Cache", icon: "⚡", color: "yellow" },
};

export default function ChatWindow({ suggestedQueries = [] }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [agentSteps, setAgentSteps] = useState([]);
  const messagesEndRef = useRef(null);
  const wsRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages, agentSteps]);

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const handleSend = useCallback(async () => {
    const question = input.trim();
    if (!question || loading) return;

    // Add user message
    setMessages((prev) => [...prev, { type: "user", content: question }]);
    setInput("");
    setLoading(true);
    setAgentSteps([]);

    // Try WebSocket first for live updates
    try {
      const { ws, close } = queryKnowledgeWS(
        question,
        // onAgentUpdate
        (update) => {
          setAgentSteps((prev) => {
            const existing = prev.findIndex((s) => s.agent === update.agent);
            if (existing >= 0) {
              const updated = [...prev];
              updated[existing] = { ...updated[existing], ...update };
              return updated;
            }
            return [...prev, update];
          });
        },
        // onResult
        (data) => {
          setMessages((prev) => [
            ...prev,
            {
              type: "assistant",
              content: data.answer,
              sources: data.sources || [],
              confidence: data.confidence || 0,
              agentFlow: data.agent_flow || [],
            },
          ]);
          setLoading(false);
          setAgentSteps([]);
        },
        // onError — fallback to REST
        async (err) => {
          console.warn("WebSocket query failed, falling back to REST:", err);
          try {
            const data = await queryKnowledge(question);
            setMessages((prev) => [
              ...prev,
              {
                type: "assistant",
                content: data.answer,
                sources: data.sources || [],
                confidence: data.confidence || 0,
                agentFlow: data.agent_flow || [],
              },
            ]);
          } catch (restErr) {
            setMessages((prev) => [
              ...prev,
              {
                type: "error",
                content:
                  restErr.response?.data?.detail ||
                  "Failed to get response. Please try again.",
              },
            ]);
          } finally {
            setLoading(false);
            setAgentSteps([]);
          }
        }
      );
      wsRef.current = ws;
    } catch (err) {
      // If WebSocket constructor itself fails, use REST
      try {
        const data = await queryKnowledge(question);
        setMessages((prev) => [
          ...prev,
          {
            type: "assistant",
            content: data.answer,
            sources: data.sources || [],
            confidence: data.confidence || 0,
            agentFlow: data.agent_flow || [],
          },
        ]);
      } catch (restErr) {
        setMessages((prev) => [
          ...prev,
          {
            type: "error",
            content:
              restErr.response?.data?.detail ||
              "Failed to get response. Please try again.",
          },
        ]);
      } finally {
        setLoading(false);
        setAgentSteps([]);
      }
    }
  }, [input, loading]);

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <Flex direction="column" h="calc(100vh - 140px)" maxH="800px">
      {/* Messages Area */}
      <Box
        flex="1"
        overflowY="auto"
        px={4}
        py={4}
        borderRadius="xl"
        bg="hive.surface"
        border="1px solid"
        borderColor="hive.border"
        mb={4}
      >
        {messages.length === 0 ? (
          <Flex h="100%" align="center" justify="center">
            <VStack spacing={4} color="hive.textMuted" maxW="500px">
              <Text fontSize="4xl">🐝</Text>
              <Text fontSize="lg" fontWeight="500">
                Enterprise Knowledge Assistant
              </Text>
              <Text fontSize="sm" textAlign="center">
                Ask questions across all connected sources — Teams, Email, Jira, SharePoint, Confluence
              </Text>
              {suggestedQueries.length > 0 && (
                <Flex gap={2} flexWrap="wrap" justify="center" mt={2}>
                  {suggestedQueries.slice(0, 4).map((q) => (
                    <Box
                      key={q}
                      px={3}
                      py={2}
                      borderRadius="lg"
                      bg="hive.surface"
                      border="1px solid"
                      borderColor="hive.border"
                      fontSize="xs"
                      cursor="pointer"
                      _hover={{
                        borderColor: "brand.500",
                        bg: "hive.accentGlow",
                        color: "hive.text",
                      }}
                      transition="all 0.2s"
                      onClick={() => setInput(q)}
                    >
                      {q}
                    </Box>
                  ))}
                </Flex>
              )}
            </VStack>
          </Flex>
        ) : (
          <VStack spacing={4} align="stretch">
            {messages.map((msg, i) => (
              <MessageBubble key={i} message={msg} />
            ))}

            {/* Live Agent Steps Indicator */}
            {loading && agentSteps.length > 0 && (
              <AgentStepIndicator steps={agentSteps} />
            )}

            {/* Fallback loading (no WS updates yet) */}
            {loading && agentSteps.length === 0 && (
              <HStack spacing={3} p={4}>
                <Spinner size="sm" color="brand.400" />
                <Text fontSize="sm" color="hive.textMuted">
                  Connecting to agent swarm...
                </Text>
              </HStack>
            )}
            <div ref={messagesEndRef} />
          </VStack>
        )}
      </Box>

      {/* Input Area */}
      <HStack spacing={3}>
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about your documents..."
          size="lg"
          borderRadius="xl"
          bg="hive.surface"
          borderColor="hive.border"
          _focus={{
            borderColor: "brand.500",
            boxShadow: "0 0 0 1px var(--chakra-colors-brand-500)",
          }}
          disabled={loading}
        />
        <IconButton
          icon={<FiSend />}
          onClick={handleSend}
          isLoading={loading}
          aria-label="Send message"
          size="lg"
          borderRadius="xl"
          bg="brand.500"
          color="black"
          _hover={{
            bg: "brand.400",
            transform: "translateY(-1px)",
            boxShadow: "0 4px 20px rgba(255, 179, 0, 0.3)",
          }}
          transition="all 0.2s"
        />
      </HStack>
    </Flex>
  );
}

/**
 * Live agent step indicator — shows real-time progress during queries
 */
function AgentStepIndicator({ steps }) {
  const allAgents = ["retrieval", "validation", "response"];

  return (
    <Box
      p={4}
      borderRadius="lg"
      bg="hive.card"
      border="1px solid"
      borderColor="hive.border"
    >
      <HStack spacing={2} mb={3}>
        <FiZap color="var(--chakra-colors-brand-400)" />
        <Text fontSize="sm" fontWeight="600" color="brand.400">
          Agent Swarm Active
        </Text>
      </HStack>
      <HStack spacing={4} flexWrap="wrap">
        {allAgents.map((agentKey) => {
          const step = steps.find((s) => s.agent === agentKey);
          const config = AGENT_LABELS[agentKey] || {};
          const status = step?.status || "pending";

          return (
            <HStack key={agentKey} spacing={2}>
              {status === "running" ? (
                <Spinner size="xs" color={`${config.color}.400`} />
              ) : status === "completed" ? (
                <FiCheckCircle color={`var(--chakra-colors-green-400)`} size={14} />
              ) : (
                <FiCircle color="var(--chakra-colors-whiteAlpha-300)" size={14} />
              )}
              <Text
                fontSize="xs"
                fontWeight="500"
                color={
                  status === "completed"
                    ? "green.300"
                    : status === "running"
                    ? `${config.color}.300`
                    : "hive.textMuted"
                }
              >
                {config.icon} {config.label}
              </Text>
              {step?.duration_ms && (
                <Badge
                  fontSize="9px"
                  variant="outline"
                  colorScheme={config.color}
                  borderRadius="sm"
                >
                  {step.duration_ms.toFixed(0)}ms
                </Badge>
              )}
            </HStack>
          );
        })}
      </HStack>

      {/* Show latest message */}
      {steps.length > 0 && steps[steps.length - 1]?.message && (
        <Text fontSize="xs" color="hive.textMuted" mt={2}>
          {steps[steps.length - 1].message}
        </Text>
      )}
    </Box>
  );
}

/**
 * Individual message bubble with expandable sources
 */
function MessageBubble({ message }) {
  const [showSources, setShowSources] = useState(false);
  const isUser = message.type === "user";
  const isError = message.type === "error";

  return (
    <Box
      alignSelf={isUser ? "flex-end" : "flex-start"}
      maxW="85%"
      w={isUser ? "auto" : "100%"}
    >
      <Box
        p={4}
        borderRadius="xl"
        bg={
          isUser
            ? "brand.500"
            : isError
            ? "rgba(248, 113, 113, 0.1)"
            : "hive.card"
        }
        color={isUser ? "black" : isError ? "red.300" : "hive.text"}
        border={isUser ? "none" : "1px solid"}
        borderColor={isError ? "red.800" : "hive.border"}
      >
        <Text
          fontSize="sm"
          lineHeight="tall"
          whiteSpace="pre-wrap"
        >
          {message.content}
        </Text>

        {/* Confidence + Sources toggle */}
        {message.sources && message.sources.length > 0 && (
          <>
            <Divider my={3} borderColor="hive.border" />
            <HStack justify="space-between">
              <HStack spacing={2}>
                <Tooltip label="Confidence score based on evidence quality">
                  <Badge
                    colorScheme={
                      message.confidence > 0.7
                        ? "green"
                        : message.confidence > 0.4
                        ? "yellow"
                        : "red"
                    }
                    variant="subtle"
                    px={2}
                    borderRadius="md"
                  >
                    {(message.confidence * 100).toFixed(0)}% confidence
                  </Badge>
                </Tooltip>
                <Badge variant="subtle" colorScheme="blue" px={2} borderRadius="md">
                  {message.sources.length} sources
                </Badge>
              </HStack>
              <IconButton
                icon={showSources ? <FiChevronUp /> : <FiChevronDown />}
                size="xs"
                variant="ghost"
                onClick={() => setShowSources(!showSources)}
                aria-label="Toggle sources"
              />
            </HStack>

            <Collapse in={showSources} animateOpacity>
              <VStack spacing={2} mt={3} align="stretch">
                {message.sources.map((source, i) => (
                  <Box
                    key={i}
                    p={3}
                    borderRadius="lg"
                    bg="hive.surface"
                    border="1px solid"
                    borderColor="hive.border"
                    fontSize="xs"
                  >
                    <HStack spacing={2} mb={1}>
                      <FiFileText size={12} />
                      <Text fontWeight="600" color="brand.300">
                        {source.document_name}
                      </Text>
                      <Badge
                        size="sm"
                        colorScheme="yellow"
                        variant="outline"
                        fontSize="10px"
                      >
                        {(source.relevance_score * 100).toFixed(0)}% relevant
                      </Badge>
                    </HStack>
                    <Text color="hive.textMuted" noOfLines={3}>
                      {source.chunk_text}
                    </Text>
                  </Box>
                ))}
              </VStack>
            </Collapse>
          </>
        )}
      </Box>
    </Box>
  );
}
