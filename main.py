import os
import requests
import json
import sys

token = sys.argv[1]
endpoint = sys.argv[2]
exclude = sys.argv[3] if len(sys.argv) > 3 else ""
build_mode_manual_override = sys.argv[4] if len(sys.argv) > 4 else ""
standard_language_names = sys.argv[5] if len(sys.argv) > 5 else ""
changed_files_input = sys.argv[6] if len(sys.argv) > 6 else ""
# Opt-in: use the standard combined CodeQL language names (e.g. "javascript-typescript")
# as used by github/codeql-action, instead of the legacy single names (e.g. "javascript").
# Defaults to False to preserve backward compatibility with existing workflows.
use_standard_language_names = standard_language_names.strip().lower() in ("true", "1", "yes")
codeql_languages = ["actions", "cpp", "c-cpp", "csharp", "go", "java", "java-kotlin", "javascript",
                     "javascript-typescript", "python", "ruby", "rust", "typescript", "kotlin", "swift"]

# File extensions used to detect each CodeQL language in a list of changed files.
# Only used when the `changed-files` input is provided, to narrow the matrix down
# to languages actually touched by a pull request.
# Note: "javascript" and "java" include their combined-language extensions too
# (.ts/.tsx and .kt/.kts respectively), since in legacy (non-standard-language-names)
# mode those slugs are the combined bucket that typescript/kotlin map into.
language_extensions = {
    "actions": [".yml", ".yaml"],
    "cpp": [".c", ".cc", ".cpp", ".cxx", ".c++", ".h", ".hh", ".hpp", ".hxx", ".h++", ".inc", ".ino"],
    "c-cpp": [".c", ".cc", ".cpp", ".cxx", ".c++", ".h", ".hh", ".hpp", ".hxx", ".h++", ".inc", ".ino"],
    "csharp": [".cs"],
    "go": [".go"],
    "java": [".java", ".kt", ".kts"],
    "java-kotlin": [".java", ".kt", ".kts"],
    "javascript": [".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts"],
    "javascript-typescript": [".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts"],
    "python": [".py"],
    "ruby": [".rb"],
    "rust": [".rs"],
    "typescript": [".ts", ".tsx", ".mts", ".cts"],
    "kotlin": [".kt", ".kts"],
    "swift": [".swift"],
}


# Connect to the languages API and return languages
def get_languages():
    headers = {'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github.v3+json'}
    response = requests.get(endpoint, headers=headers)
    return response.json()

# Find the intersection of the languages returned by the API and the languages supported by CodeQL
def build_languages_list(languages):
    original_languages = [language.lower() for language in languages.keys()]
    mapped_languages = []
    language_mapping = {}  # Track mapped language -> list of original languages
    
    for orig_lang in original_languages:
        mapped_lang = orig_lang
        if orig_lang == "c#":
            mapped_lang = "csharp"
        elif orig_lang in ("c++", "c"):
            mapped_lang = "c-cpp" if use_standard_language_names else "cpp"
        elif orig_lang == "typescript":
            mapped_lang = "javascript-typescript" if use_standard_language_names else "javascript"
        elif orig_lang == "javascript" and use_standard_language_names:
            mapped_lang = "javascript-typescript"
        elif orig_lang == "kotlin":
            mapped_lang = "java-kotlin" if use_standard_language_names else "java"
        elif orig_lang == "java" and use_standard_language_names:
            mapped_lang = "java-kotlin"
        elif orig_lang == "yaml":
            mapped_lang = "actions"
        
        mapped_languages.append(mapped_lang)
        
        # Track all original languages that map to this CodeQL language
        if mapped_lang not in language_mapping:
            language_mapping[mapped_lang] = []
        language_mapping[mapped_lang].append(orig_lang)
    
    print("After mapping:", mapped_languages)
    intersection = list(set(mapped_languages) & set(codeql_languages))
    print("Intersection:", intersection)
    return intersection, language_mapping

# return a list of objects from language list if they are not in the exclude list
def exclude_languages(language_list):
    if not exclude:
        return language_list
    excluded = [x.strip() for x in exclude.split(',')]
    output = list(set(language_list).difference(excluded))
    print("languages={}".format(output))
    return output

# Parse the changed-files input into a list of file paths.
# Accepts a JSON array (e.g. from tj-actions/changed-files with json output),
# or a comma/newline/space separated list of paths (e.g. `git diff --name-only`).
# Returns None when no changed files were provided, so callers can distinguish
# "no filtering requested" from "filtering requested, but nothing matched".
def parse_changed_files(raw):
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [str(f).strip() for f in parsed if str(f).strip()]
    except ValueError:
        pass
    return [f.strip() for f in raw.replace(",", "\n").split() if f.strip()]

# Narrow a list of CodeQL languages down to only those with a changed file
# matching one of their known extensions. If changed_files is None (the
# `changed-files` input was not supplied), the language list is returned
# unmodified to preserve the action's existing default behavior.
def filter_by_changed_files(language_list, changed_files):
    if changed_files is None:
        return language_list

    normalized_files = [f.replace("\\", "/").lower() for f in changed_files]
    filtered = []
    for language in language_list:
        extensions = language_extensions.get(language, [])
        for file_path in normalized_files:
            if not any(file_path.endswith(ext) for ext in extensions):
                continue
            if language == "actions" and "/.github/workflows/" not in "/" + file_path:
                continue
            filtered.append(language)
            break

    print("Changed files:", changed_files)
    print("Languages after changed-files filter:", filtered)
    return filtered

# Determine build mode for each language
def get_build_mode(language, original_languages=None):
    # Languages that should use manual build mode by default
    # Check original languages first if available
    if original_languages:
        # If any of the original languages require manual build mode, use manual
        for orig_lang in original_languages:
            if orig_lang in ["kotlin", "go", "swift"]:
                manual_by_default = True
                break
        else:
            manual_by_default = False
    else:
        # Fallback to mapped language check
        manual_by_default = language in ["go", "swift"]
    
    # Check if user overrode build mode to manual
    if build_mode_manual_override:
        override_languages = [x.strip() for x in build_mode_manual_override.split(',')]
        if language in override_languages:
            return "manual"
        if original_languages:
            for orig_lang in original_languages:
                if orig_lang in override_languages:
                    return "manual"
    
    # Use default logic
    if manual_by_default:
        return "manual"
    else:
        return "none"

# Build the matrix include format
def build_matrix(language_list, language_mapping):
    include = []
    for language in language_list:
        original_languages = language_mapping.get(language, [language])
        build_mode = get_build_mode(language, original_languages)
        include.append({
            "language": language,
            "build-mode": build_mode
        })
    
    matrix = {"include": include}
    print("Matrix:", matrix)
    return matrix

# Set the output of the action
def set_action_output(output_name, value) :
    if "GITHUB_OUTPUT" in os.environ :
        with open(os.environ["GITHUB_OUTPUT"], "a") as f :
            print("{0}={1}".format(output_name, value), file=f)

def main():
    languages = get_languages()
    language_list, language_mapping = build_languages_list(languages)
    filtered_languages = exclude_languages(language_list)
    changed_files = parse_changed_files(changed_files_input)
    filtered_languages = filter_by_changed_files(filtered_languages, changed_files)
    matrix = build_matrix(filtered_languages, language_mapping)
    set_action_output("matrix", json.dumps(matrix))
    # Keep the old output for backward compatibility
    set_action_output("languages", json.dumps(filtered_languages))

if __name__ == '__main__':
    main()
