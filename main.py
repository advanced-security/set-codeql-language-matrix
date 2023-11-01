import os
import requests
import json
import sys

token = sys.argv[1]
endpoint = sys.argv[2]
exclude = sys.argv[3]
codeql_languages = ["cpp", "csharp", "go", "java", "javascript", "python", "ruby", "typescript", "kotlin", "swift"]


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

    intersection = list(set(languages) & set(codeql_languages))
    return intersection

# return a list of objects from language list if they are not in the exclude list
def exclude_languages(language_list):
    excluded = [x.strip() for x in exclude.split(',')]
    output = list(set(language_list).difference(excluded))
    print("languages={}".format(output))
    return output

# Set the output of the action
def set_action_output(output_name, value) :
    if "GITHUB_OUTPUT" in os.environ :
        with open(os.environ["GITHUB_OUTPUT"], "a") as f :
            print("Detected languages: {0}={1}".format(output_name, value), file=f)

def main():
    languages = get_languages()
    language_list = build_languages_list(languages)
    output = exclude_languages(language_list)
    set_action_output("languages", json.dumps(output))

if __name__ == '__main__':
    main()


