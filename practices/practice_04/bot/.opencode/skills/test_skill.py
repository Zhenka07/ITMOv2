#!/usr/bin/env python3
"""
Test Suite for OpenCode Skill: test-driven-development.
Проверяет корректность манифеста скилла, наличие справочников,
а также практическое соответствие кода проекта TDD-методологии.
"""

import unittest
import os
import re
import subprocess

SKILL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "test-driven-development"))
BOT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

class TestSkillManifest(unittest.TestCase):
    def setUp(self):
        self.skill_file = os.path.join(SKILL_DIR, "SKILL.md")
        self.reference_file = os.path.join(SKILL_DIR, "writing-good-tests.md")

    def test_skill_files_exist(self):
        """Проверка физического наличия файлов скилла"""
        self.assertTrue(os.path.exists(self.skill_file), "SKILL.md must exist")
        self.assertTrue(os.path.exists(self.reference_file), "writing-good-tests.md must exist")

    def test_skill_frontmatter(self):
        """Проверка YAML-метаданных (frontmatter) в SKILL.md"""
        with open(self.skill_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Проверка разделителей frontmatter
        self.assertTrue(content.startswith("---"), "SKILL.md must start with YAML frontmatter '---'")
        parts = content.split("---", 2)
        self.assertGreaterEqual(len(parts), 3, "Frontmatter must have opening and closing '---'")

        frontmatter = parts[1]
        # Проверка имени скилла
        name_match = re.search(r"^name:\s*([a-zA-Z0-9_\-]+)", frontmatter, re.MULTILINE)
        self.assertIsNotNone(name_match, "Frontmatter must contain 'name'")
        self.assertEqual(name_match.group(1).strip(), "test-driven-development")

        # Проверка описания
        desc_match = re.search(r"^description:\s*(.+)", frontmatter, re.MULTILINE)
        self.assertIsNotNone(desc_match, "Frontmatter must contain 'description'")
        self.assertTrue(len(desc_match.group(1).strip()) > 10, "Description must be meaningful")

    def test_tdd_phases_defined(self):
        """Проверка наличия всех трех ключевых шагов TDD: Red, Green, Refactor"""
        with open(self.skill_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("Red", content, "SKILL.md must describe Phase 1: Red (failing test)")
        self.assertIn("Green", content, "SKILL.md must describe Phase 2: Green (minimal implementation)")
        self.assertIn("Refactor", content, "SKILL.md must describe Phase 3: Refactor (clean code)")

    def test_reference_guide_content(self):
        """Проверка содержания справочника writing-good-tests.md"""
        with open(self.reference_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("Table-Driven Tests", content, "Must explain table-driven tests")
        self.assertIn("t.Run", content, "Must mention subtests with t.Run")
        self.assertIn("t.Errorf", content, "Must explain clear error reporting")


class TestTDDApplicationInCodebase(unittest.TestCase):
    """Проверка того, что тесты в репозитории реально следуют предписаниям скилла"""
    def setUp(self):
        self.test_file = os.path.join(BOT_ROOT, "client", "events", "telegram", "commands_test.go")

    def test_codebase_has_table_driven_tests(self):
        """Проверка, что в кодовой базе реализованы Table-Driven Tests согласно скиллу"""
        self.assertTrue(os.path.exists(self.test_file), "commands_test.go must exist")
        with open(self.test_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Должен быть срез анонимных структур []struct
        self.assertIn("[]struct", content, "Tests must use table-driven slice of structs")
        # Должен быть запуск подтестов t.Run
        self.assertIn("t.Run", content, "Tests must execute subtests via t.Run")

    def test_go_tests_pass_successfully(self):
        """Запуск тестов пакета через go test для подтверждения фазы Green"""
        cmd = ["go", "test", "-v", "./client/events/telegram/..."]
        res = subprocess.run(cmd, cwd=BOT_ROOT, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Go tests failed:\n{res.stderr or res.stdout}")
        self.assertIn("PASS: TestValidateURL", res.stdout)
        self.assertIn("PASS: TestIsURL", res.stdout)


if __name__ == "__main__":
    unittest.main()
