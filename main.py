import os
import requests
import json
import sys

token = sys.argv[1]
endpoint = sys.argv[2]
exclude = sys.argv[3] if len(sys.argv) > 3 else ""
build_mode_override = sys.argv[4] if len(sys.argv) > 4 else ""
codeql_languages = ["actions", "cpp", "csharp", "go", "java", "javascript", "python", "ruby", "rust", "typescript", "kotlin", "swift"]


# Connect to the languages API and return languages
def get_languages():
    headers = {'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github.v3+json'}
    response = requests.get(endpoint, headers=headers)
    return response.json()

# Find the intersection of the languages returned by the API and the languages supported by CodeQL
def build_languages_list(languages):
    languages = [language.lower() for language in languages.keys()]
    for i in range(len(languages)):
        if languages[i] == "c#":
            languages[i] = ("csharp")
        if languages[i] == "c++":
            languages[i] = ("cpp")
        if languages[i] == "c":
            languages[i] = ("cpp")
        if languages[i] == "typescript":
            languages[i] = ("javascript")
        if languages[i] == "kotlin":
            languages[i] = ("java")
        if languages[i] == "yaml":
            languages[i] = ("actions")
    print("After mapping:", languages)
    intersection = list(set(languages) & set(codeql_languages))
    print("Intersection:", intersection)
    return intersection

# return a list of objects from language list if they are not in the exclude list
def exclude_languages(language_list):
    if not exclude:
        return language_list
    excluded = [x.strip() for x in exclude.split(',')]
    output = list(set(language_list).difference(excluded))
    print("languages={}".format(output))
    return output

# Determine build mode for each language
def get_build_mode(language):
    # Languages that should use manual build mode by default
    manual_languages = ["go", "swift", "java"]
    
    # Check if user overrode build mode
    if build_mode_override:
        override_languages = [x.strip() for x in build_mode_override.split(',')]
        if language in override_languages:
            return "manual"
    
    # Use default logic
    if language in manual_languages:
        return "manual"
    else:
        return "none"

# Build the matrix include format
def build_matrix(language_list):
    include = []
    for language in language_list:
        build_mode = get_build_mode(language)
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
    language_list = build_languages_list(languages)
    filtered_languages = exclude_languages(language_list)
    matrix = build_matrix(filtered_languages)
    set_action_output("matrix", json.dumps(matrix))
    # Keep the old output for backward compatibility
    set_action_output("languages", json.dumps(filtered_languages))

if __name__ == '__main__':
    main()
