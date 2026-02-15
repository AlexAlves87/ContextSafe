"""Tests for whitespace boundary preservation in anonymization replacement."""

import pytest


class TestReplacementWhitespace:
    """Tests that replacement preserves word boundaries."""

    def test_no_extra_space_when_followed_by_space(self):
        """If next char is already a space, don't add another."""
        text = "D. Juan García presentó recurso"
        # Entity "Juan García" at [3:15], next char is ' '
        start, end = 3, 15
        alias = "Persona_001"

        after_char = text[end:end + 1] if end < len(text) else ""
        space_suffix = " " if after_char.isalnum() else ""
        result = text[:start] + alias + space_suffix + text[end:]

        assert result == "D. Persona_001 presentó recurso"

    def test_adds_space_when_touching_word(self):
        """If next char is a letter, a space must be inserted."""
        # Simulate entity span that ends right at next word
        text = "contactó WhatsAppya en diciembre"
        start, end = 9, 17  # "WhatsApp"
        alias = "Plataforma_001"

        after_char = text[end:end + 1] if end < len(text) else ""
        space_suffix = " " if after_char.isalnum() else ""
        result = text[:start] + alias + space_suffix + text[end:]

        assert result == "contactó Plataforma_001 ya en diciembre"

    def test_no_extra_space_at_end_of_text(self):
        """If entity is at end of text, no trailing space."""
        text = "firmado por Juan García"
        start, end = 12, 23  # "Juan García"
        alias = "Persona_001"

        after_char = text[end:end + 1] if end < len(text) else ""
        space_suffix = " " if after_char.isalnum() else ""
        result = text[:start] + alias + space_suffix + text[end:]

        assert result == "firmado por Persona_001"

    def test_no_extra_space_before_punctuation(self):
        """If next char is punctuation, no space needed."""
        text = "firmado por Juan García."
        start, end = 12, 23  # "Juan García"
        alias = "Persona_001"

        after_char = text[end:end + 1] if end < len(text) else ""
        space_suffix = " " if after_char.isalnum() else ""
        result = text[:start] + alias + space_suffix + text[end:]

        assert result == "firmado por Persona_001."

    def test_adds_space_before_digit(self):
        """If next char is a digit, a space must be inserted."""
        text = "contactó WhatsApp3 veces"
        start, end = 9, 17  # "WhatsApp"
        alias = "Plataforma_001"

        after_char = text[end:end + 1] if end < len(text) else ""
        space_suffix = " " if after_char.isalnum() else ""
        result = text[:start] + alias + space_suffix + text[end:]

        assert result == "contactó Plataforma_001 3 veces"
