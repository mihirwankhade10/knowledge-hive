/**
 * KnowledgeHive - Custom Chakra UI Theme
 *
 * Honey/amber-themed dark mode design system.
 * Premium look with golden accents.
 */
import { extendTheme } from "@chakra-ui/react";

const theme = extendTheme({
  config: {
    initialColorMode: "dark",
    useSystemColorMode: false,
  },
  fonts: {
    heading: `'Inter', -apple-system, BlinkMacSystemFont, sans-serif`,
    body: `'Inter', -apple-system, BlinkMacSystemFont, sans-serif`,
    mono: `'JetBrains Mono', 'Fira Code', monospace`,
  },
  colors: {
    brand: {
      50: "#FFF8E1",
      100: "#FFECB3",
      200: "#FFE082",
      300: "#FFD54F",
      400: "#FFCA28",
      500: "#FFC107",
      600: "#FFB300",
      700: "#FFA000",
      800: "#FF8F00",
      900: "#FF6F00",
    },
    hive: {
      bg: "#0A0A0F",
      card: "#12121A",
      cardHover: "#1A1A25",
      border: "#2A2A35",
      surface: "#16161F",
      text: "#E8E8ED",
      textMuted: "#8888A0",
      accent: "#FFB300",
      accentGlow: "rgba(255, 179, 0, 0.15)",
      success: "#4ADE80",
      error: "#F87171",
      warning: "#FBBF24",
      info: "#60A5FA",
    },
  },
  styles: {
    global: {
      "html, body": {
        bg: "hive.bg",
        color: "hive.text",
        lineHeight: "tall",
      },
      "*::selection": {
        bg: "brand.500",
        color: "black",
      },
      "::-webkit-scrollbar": {
        width: "6px",
      },
      "::-webkit-scrollbar-track": {
        bg: "transparent",
      },
      "::-webkit-scrollbar-thumb": {
        bg: "hive.border",
        borderRadius: "3px",
      },
    },
  },
  components: {
    Button: {
      variants: {
        brand: {
          bg: "brand.500",
          color: "black",
          fontWeight: "600",
          _hover: {
            bg: "brand.400",
            transform: "translateY(-1px)",
            boxShadow: "0 4px 20px rgba(255, 179, 0, 0.3)",
          },
          _active: {
            bg: "brand.600",
            transform: "translateY(0)",
          },
          transition: "all 0.2s ease",
        },
        ghost: {
          color: "hive.textMuted",
          _hover: {
            bg: "hive.cardHover",
            color: "hive.text",
          },
        },
      },
    },
    Card: {
      baseStyle: {
        container: {
          bg: "hive.card",
          borderColor: "hive.border",
          borderWidth: "1px",
          borderRadius: "xl",
        },
      },
    },
    Input: {
      variants: {
        filled: {
          field: {
            bg: "hive.surface",
            borderColor: "hive.border",
            _hover: { bg: "hive.cardHover" },
            _focus: {
              bg: "hive.surface",
              borderColor: "brand.500",
              boxShadow: "0 0 0 1px var(--chakra-colors-brand-500)",
            },
          },
        },
      },
      defaultProps: {
        variant: "filled",
      },
    },
  },
});

export default theme;
