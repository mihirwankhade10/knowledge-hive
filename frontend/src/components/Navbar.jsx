/**
 * KnowledgeHive - Navbar Component
 *
 * Top navigation bar with logo, page links, and status indicator.
 */
import { Box, Flex, HStack, Text, IconButton, Badge, Link as ChakraLink } from "@chakra-ui/react";
import { Link, useLocation } from "react-router-dom";
import { FiHome, FiMessageSquare, FiActivity, FiZap } from "react-icons/fi";

const navItems = [
  { path: "/", label: "Dashboard", icon: FiHome },
  { path: "/chat", label: "Chat", icon: FiMessageSquare },
  { path: "/agents", label: "Agent Flow", icon: FiActivity },
];

export default function Navbar() {
  const location = useLocation();

  return (
    <Box
      as="nav"
      position="fixed"
      top="0"
      left="0"
      right="0"
      zIndex="1000"
      bg="rgba(10, 10, 15, 0.85)"
      backdropFilter="blur(20px)"
      borderBottom="1px solid"
      borderColor="hive.border"
    >
      <Flex
        maxW="1400px"
        mx="auto"
        h="64px"
        px={6}
        align="center"
        justify="space-between"
      >
        {/* Logo */}
        <HStack spacing={3} as={Link} to="/" _hover={{ textDecoration: "none" }}>
          <Flex
            w="36px"
            h="36px"
            borderRadius="lg"
            bg="brand.500"
            align="center"
            justify="center"
            boxShadow="0 0 20px rgba(255, 179, 0, 0.3)"
          >
            <FiZap size={20} color="black" />
          </Flex>
          <Text
            fontSize="xl"
            fontWeight="bold"
            bgGradient="linear(to-r, brand.300, brand.500)"
            bgClip="text"
          >
            KnowledgeHive
          </Text>
        </HStack>

        {/* Navigation Links */}
        <HStack spacing={1}>
          {navItems.map(({ path, label, icon: Icon }) => {
            const isActive = location.pathname === path;
            return (
              <ChakraLink
                as={Link}
                to={path}
                key={path}
                px={4}
                py={2}
                borderRadius="lg"
                display="flex"
                alignItems="center"
                gap={2}
                fontSize="sm"
                fontWeight={isActive ? "600" : "400"}
                color={isActive ? "brand.400" : "hive.textMuted"}
                bg={isActive ? "hive.accentGlow" : "transparent"}
                _hover={{
                  bg: "hive.cardHover",
                  color: "hive.text",
                  textDecoration: "none",
                }}
                transition="all 0.2s ease"
              >
                <Icon size={16} />
                {label}
              </ChakraLink>
            );
          })}
        </HStack>

        {/* Status Badge */}
        <HStack spacing={2}>
          <Badge
            colorScheme="green"
            variant="subtle"
            px={3}
            py={1}
            borderRadius="full"
            fontSize="xs"
          >
            <HStack spacing={1}>
              <Box w="6px" h="6px" borderRadius="full" bg="green.400" />
              <Text>Online</Text>
            </HStack>
          </Badge>
        </HStack>
      </Flex>
    </Box>
  );
}
