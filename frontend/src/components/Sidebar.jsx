/**
 * KnowledgeHive - Enterprise Sidebar Navigation
 *
 * Professional sidebar with navigation sections, status indicator,
 * and version badge. Replaces the top Navbar for enterprise feel.
 */
import { Box, VStack, HStack, Text, Flex, Badge, Icon, Divider, Tooltip } from "@chakra-ui/react";
import { Link, useLocation } from "react-router-dom";
import {
  FiHome,
  FiDatabase,
  FiShare2,
  FiCpu,
  FiMessageSquare,
  FiSettings,
  FiZap,
  FiChevronLeft,
  FiChevronRight,
} from "react-icons/fi";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

const MotionBox = motion(Box);
const MotionText = motion(Text);

const navSections = [
  {
    title: "OVERVIEW",
    items: [
      { path: "/", label: "Dashboard", icon: FiHome, id: "nav-dashboard" },
    ],
  },
  {
    title: "KNOWLEDGE",
    items: [
      { path: "/sources", label: "Knowledge Sources", icon: FiDatabase, id: "nav-sources" },
      { path: "/graph", label: "Knowledge Graph", icon: FiShare2, id: "nav-graph" },
    ],
  },
  {
    title: "INTELLIGENCE",
    items: [
      { path: "/agents", label: "Agent Swarm", icon: FiCpu, id: "nav-agents" },
      { path: "/chat", label: "Chat Assistant", icon: FiMessageSquare, id: "nav-chat" },
    ],
  },
  {
    title: "SYSTEM",
    items: [
      { path: "/settings", label: "Settings", icon: FiSettings, id: "nav-settings" },
    ],
  },
];

export default function Sidebar() {
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);

  const sidebarWidth = collapsed ? "72px" : "260px";

  return (
    <Box
      as="nav"
      position="fixed"
      top="0"
      left="0"
      bottom="0"
      w={sidebarWidth}
      bg="rgba(12, 12, 18, 0.95)"
      backdropFilter="blur(20px)"
      borderRight="1px solid"
      borderColor="hive.border"
      zIndex="1000"
      transition="width 0.3s cubic-bezier(0.4, 0, 0.2, 1)"
      display="flex"
      flexDirection="column"
      overflowX="hidden"
      overflowY="auto"
      css={{
        "&::-webkit-scrollbar": { width: "4px" },
        "&::-webkit-scrollbar-thumb": { background: "rgba(255,255,255,0.1)", borderRadius: "2px" },
      }}
    >
      {/* Logo Area */}
      <Flex
        h="64px"
        px={collapsed ? 3 : 5}
        align="center"
        justify={collapsed ? "center" : "space-between"}
        flexShrink={0}
        borderBottom="1px solid"
        borderColor="hive.border"
      >
        <HStack spacing={3} as={Link} to="/" _hover={{ textDecoration: "none" }}>
          <Flex
            w="36px"
            h="36px"
            minW="36px"
            borderRadius="lg"
            bg="brand.500"
            align="center"
            justify="center"
            boxShadow="0 0 20px rgba(255, 179, 0, 0.3)"
          >
            <FiZap size={18} color="black" />
          </Flex>
          {!collapsed && (
            <Text
              fontSize="lg"
              fontWeight="bold"
              bgGradient="linear(to-r, brand.300, brand.500)"
              bgClip="text"
              whiteSpace="nowrap"
            >
              KnowledgeHive
            </Text>
          )}
        </HStack>
        {!collapsed && (
          <Box
            as="button"
            onClick={() => setCollapsed(true)}
            color="hive.textMuted"
            _hover={{ color: "hive.text" }}
            transition="color 0.2s"
            cursor="pointer"
            p={1}
          >
            <FiChevronLeft size={16} />
          </Box>
        )}
      </Flex>

      {/* Expand Button (collapsed) */}
      {collapsed && (
        <Flex justify="center" py={2} flexShrink={0}>
          <Box
            as="button"
            onClick={() => setCollapsed(false)}
            color="hive.textMuted"
            _hover={{ color: "hive.text" }}
            transition="color 0.2s"
            cursor="pointer"
            p={1}
          >
            <FiChevronRight size={16} />
          </Box>
        </Flex>
      )}

      {/* Navigation */}
      <VStack spacing={1} align="stretch" flex="1" py={4} px={collapsed ? 2 : 3}>
        {navSections.map((section, si) => (
          <Box key={section.title} mb={2}>
            {/* Section Title */}
            {!collapsed && (
              <Text
                fontSize="10px"
                fontWeight="700"
                letterSpacing="0.1em"
                color="hive.textMuted"
                px={3}
                mb={2}
                mt={si > 0 ? 2 : 0}
                opacity={0.6}
              >
                {section.title}
              </Text>
            )}

            {si > 0 && collapsed && (
              <Divider borderColor="hive.border" opacity={0.3} my={2} />
            )}

            {/* Nav Items */}
            {section.items.map(({ path, label, icon: NavIcon, id }) => {
              const isActive = location.pathname === path;
              const navItem = (
                <Flex
                  as={Link}
                  to={path}
                  id={id}
                  key={path}
                  px={collapsed ? 0 : 3}
                  py="10px"
                  borderRadius="lg"
                  align="center"
                  justify={collapsed ? "center" : "flex-start"}
                  gap={3}
                  fontSize="sm"
                  fontWeight={isActive ? "600" : "400"}
                  color={isActive ? "brand.400" : "hive.textMuted"}
                  bg={isActive ? "rgba(255, 179, 0, 0.08)" : "transparent"}
                  borderLeft={isActive && !collapsed ? "3px solid" : "3px solid transparent"}
                  borderColor={isActive ? "brand.500" : "transparent"}
                  _hover={{
                    bg: isActive ? "rgba(255, 179, 0, 0.12)" : "rgba(255, 255, 255, 0.04)",
                    color: isActive ? "brand.400" : "hive.text",
                    textDecoration: "none",
                  }}
                  transition="all 0.2s ease"
                  position="relative"
                >
                  <Icon as={NavIcon} boxSize={collapsed ? 5 : "18px"} flexShrink={0} />
                  {!collapsed && (
                    <Text whiteSpace="nowrap">{label}</Text>
                  )}
                  {isActive && (
                    <Box
                      position="absolute"
                      right="-3px"
                      top="50%"
                      transform="translateY(-50%)"
                      w="3px"
                      h="60%"
                      borderRadius="full"
                      bg="brand.500"
                      display={collapsed ? "block" : "none"}
                    />
                  )}
                </Flex>
              );

              return collapsed ? (
                <Tooltip key={path} label={label} placement="right" hasArrow bg="hive.card" color="hive.text">
                  {navItem}
                </Tooltip>
              ) : (
                navItem
              );
            })}
          </Box>
        ))}
      </VStack>

      {/* Status + Version Footer */}
      <Box
        px={collapsed ? 2 : 4}
        py={3}
        borderTop="1px solid"
        borderColor="hive.border"
        flexShrink={0}
      >
        {!collapsed ? (
          <VStack spacing={2} align="stretch">
            <HStack spacing={2} justify="space-between">
              <HStack spacing={2}>
                <Box w="7px" h="7px" borderRadius="full" bg="green.400" boxShadow="0 0 8px rgba(74,222,128,0.5)" />
                <Text fontSize="xs" color="hive.textMuted">System Online</Text>
              </HStack>
              <Badge
                fontSize="9px"
                colorScheme="whiteAlpha"
                variant="subtle"
                borderRadius="md"
              >
                v1.0.0
              </Badge>
            </HStack>
          </VStack>
        ) : (
          <Flex justify="center">
            <Tooltip label="System Online" placement="right" hasArrow>
              <Box w="7px" h="7px" borderRadius="full" bg="green.400" boxShadow="0 0 8px rgba(74,222,128,0.5)" />
            </Tooltip>
          </Flex>
        )}
      </Box>
    </Box>
  );
}
