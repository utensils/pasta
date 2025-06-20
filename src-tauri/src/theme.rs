/// Module for handling system theme detection and application
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Theme {
    Light,
    Dark,
}

impl Theme {
    /// Detects the current system theme preference
    pub fn detect_system_theme() -> Self {
        // This is handled by CSS media queries in our implementation
        // but we could extend this to detect programmatically if needed
        Theme::Light // Default
    }
}

/// Configuration for theme-aware colors
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ThemeColors {
    pub text_primary: String,
    pub text_secondary: String,
    pub bg_primary: String,
    pub bg_secondary: String,
    pub accent_color: String,
}

impl ThemeColors {
    pub fn for_theme(theme: Theme) -> Self {
        match theme {
            Theme::Light => Self {
                text_primary: "#000000".to_string(),
                text_secondary: "#666666".to_string(),
                bg_primary: "#ffffff".to_string(),
                bg_secondary: "#f6f6f6".to_string(),
                accent_color: "#007aff".to_string(),
            },
            Theme::Dark => Self {
                text_primary: "#ffffff".to_string(),
                text_secondary: "#999999".to_string(),
                bg_primary: "#1e1e1e".to_string(),
                bg_secondary: "#2a2a2a".to_string(),
                accent_color: "#0a84ff".to_string(),
            },
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_theme_colors_for_light_theme() {
        let colors = ThemeColors::for_theme(Theme::Light);
        assert_eq!(colors.text_primary, "#000000");
        assert_eq!(colors.bg_primary, "#ffffff");
        assert_eq!(colors.accent_color, "#007aff");
    }

    #[test]
    fn test_theme_colors_for_dark_theme() {
        let colors = ThemeColors::for_theme(Theme::Dark);
        assert_eq!(colors.text_primary, "#ffffff");
        assert_eq!(colors.bg_primary, "#1e1e1e");
        assert_eq!(colors.accent_color, "#0a84ff");
    }

    #[test]
    fn test_theme_equality() {
        assert_eq!(Theme::Light, Theme::Light);
        assert_eq!(Theme::Dark, Theme::Dark);
        assert_ne!(Theme::Light, Theme::Dark);
    }
}
