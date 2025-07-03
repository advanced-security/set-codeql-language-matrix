import os
import requests
import json
import sys

token = sys.argv[1]
endpoint = sys.argv[2]
exclude = sys.argv[3] if len(sys.argv) > 3 else ""
build_mode_manual_override = sys.argv[4] if len(sys.argv) > 4 else ""
codeql_languages = ["actions", "cpp", "csharp", "go", "java", "javascript", "python", "ruby", "rust", "typescript", "kotlin", "swift"]


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
        elif orig_lang == "c++":
            mapped_lang = "cpp"
        elif orig_lang == "c":
            mapped_lang = "cpp"
        elif orig_lang == "typescript":
            mapped_lang = "javascript"
        elif orig_lang == "kotlin":
            mapped_lang = "java"
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
        manual_by_default = language in ["go", "swift", "java"]
    
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
    matrix = build_matrix(filtered_languages, language_mapping)
    set_action_output("matrix", json.dumps(matrix))
    # Keep the old output for backward compatibility
    set_action_output("languages", json.dumps(filtered_languages))

if __name__ == '__main__':
    main()
