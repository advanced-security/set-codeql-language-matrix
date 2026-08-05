import importlib
import json
import sys
import unittest


def load_main(args):
    """Import (or re-import) main.py as if it were invoked with the given CLI args."""
    sys.argv = ["main.py"] + args
    if "main" in sys.modules:
        return importlib.reload(sys.modules["main"])
    return importlib.import_module("main")


class ParseChangedFilesTests(unittest.TestCase):
    def setUp(self):
        self.main = load_main(["token", "http://example.invalid/languages"])

    def test_empty_input_returns_none(self):
        self.assertIsNone(self.main.parse_changed_files(""))
        self.assertIsNone(self.main.parse_changed_files("   "))
        self.assertIsNone(self.main.parse_changed_files(None))

    def test_comma_separated_list(self):
        self.assertEqual(
            self.main.parse_changed_files("src/app.py, src/index.js"),
            ["src/app.py", "src/index.js"],
        )

    def test_newline_and_space_separated_list(self):
        self.assertEqual(
            self.main.parse_changed_files("src/app.py\nsrc/index.js cmd/main.go"),
            ["src/app.py", "src/index.js", "cmd/main.go"],
        )

    def test_json_array(self):
        self.assertEqual(
            self.main.parse_changed_files(json.dumps(["a.py", "b.go"])),
            ["a.py", "b.go"],
        )


class FilterByChangedFilesTests(unittest.TestCase):
    def setUp(self):
        # standard-language-names=true
        self.main = load_main(["token", "http://example.invalid/languages", "", "", "true"])

    def test_none_changed_files_returns_input_unmodified(self):
        languages = ["python", "go"]
        self.assertEqual(self.main.filter_by_changed_files(languages, None), languages)

    def test_filters_to_matching_language_only(self):
        languages = ["python", "javascript-typescript", "go"]
        result = self.main.filter_by_changed_files(languages, ["src/app.py", "README.md"])
        self.assertEqual(result, ["python"])

    def test_actions_requires_workflows_directory(self):
        self.assertEqual(
            self.main.filter_by_changed_files(["actions"], ["config/settings.yaml"]), []
        )
        self.assertEqual(
            self.main.filter_by_changed_files(["actions"], [".github/workflows/ci.yml"]),
            ["actions"],
        )

    def test_case_insensitive_matching(self):
        self.assertEqual(self.main.filter_by_changed_files(["go"], ["cmd/MAIN.GO"]), ["go"])

    def test_legacy_javascript_matches_typescript_files(self):
        # With standard-language-names off, "javascript" is the combined js/ts bucket.
        main = load_main(["token", "http://example.invalid/languages"])
        self.assertEqual(main.filter_by_changed_files(["javascript"], ["src/app.ts"]), ["javascript"])

    def test_legacy_java_matches_kotlin_files(self):
        # With standard-language-names off, "java" is the combined java/kotlin bucket.
        main = load_main(["token", "http://example.invalid/languages"])
        self.assertEqual(main.filter_by_changed_files(["java"], ["src/Main.kt"]), ["java"])

    def test_no_matching_language_returns_empty_list(self):
        self.assertEqual(
            self.main.filter_by_changed_files(["python", "go"], ["docs/readme.md"]), []
        )


if __name__ == "__main__":
    unittest.main()
