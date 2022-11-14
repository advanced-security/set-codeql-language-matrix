import os
import requests
import json
import sys

token = sys.argv[1]
endpoint = sys.argv[2]
codeql_languages = ["cpp", "csharp", "go", "java", "javascript", "python", "ruby"]


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

    intersection = list(set(languages) & set(codeql_languages))
    return intersection

# Set the output of the action
def set_action_output(output_name, value) :
    if "GITHUB_OUTPUT" in os.environ :
        with open(os.environ["GITHUB_OUTPUT"], "a") as f :
            print("{0}={1}".format(output_name, value), file=f)
    print("{0}={1}".format(output_name, value))

def main():
    languages = get_languages()
    output = build_languages_list(languages)
    set_action_output("languages", json.dumps(output))

if __name__ == '__main__':
    main()


