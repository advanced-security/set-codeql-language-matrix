# Set CodeQL Language Matrix

This action reads the languages API for your repository and sets the CodeQL supported languages as the job matrix for your Actions run.

## Background 

The default Actions workflow for CodeQL auto-populates the job matrix with your repo's supported CodeQL languages.  However, as new code is added to a repository, that language matrix is not updated.  You need to manually add those languages to the matrix definition to have CodeQL scan them.  

This action reads the repository languages API and adds all supported languages to the job matrix.  No additional configuration is required.

Learn more about the supported CodeQL languages [here](https://docs.github.com/en/free-pro-team@latest/github/finding-security-vulnerabilities-and-errors-in-your-code/configuring-code-scanning#changing-the-languages-that-are-analyzed)

## How to use this action

Call this action before defining the CodeQL analyze job strategy, then set the matrix to the output from the action: `${{ fromJSON(needs.create-matrix.outputs.matrix) }}`

**Example**
``` yaml
name: "CodeQL Auto Language"

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '17 19 * * 6'

jobs:
  create-matrix:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.set-matrix.outputs.matrix }}
    steps:
      - name: Get languages from repo
        id: set-matrix
        uses: advanced-security/set-codeql-language-matrix@v1
        with:
          access-token: ${{ secrets.GITHUB_TOKEN }}
          endpoint: ${{ github.event.repository.languages_url }}
          
  analyze:
    needs: create-matrix
    if: ${{ needs.create-matrix.outputs.matrix != '[]' }}
    name: Analyze
    runs-on: ubuntu-latest
    permissions:
      actions: read
      contents: read
      security-events: write

    strategy:
      fail-fast: false
      matrix: ${{ fromJSON(needs.create-matrix.outputs.matrix) }}

    steps:
    - name: Checkout repository
      uses: actions/checkout@v3

    # Initializes the CodeQL tools for scanning.
    - name: Initialize CodeQL
      uses: github/codeql-action/init@v3
      with:
        languages: ${{ matrix.language }}
        build-mode: ${{ matrix.build-mode }}

    - if: matrix.build-mode == 'manual'
      shell: bash
      run: |
        echo 'If you are using a "manual" build mode for one or more of the' \
          'languages you are analyzing, replace this with the commands to build' \
          'your code, for example:'
        echo '  make bootstrap'
        echo '  make release'
        exit 1

    - name: Perform CodeQL Analysis
      uses: github/codeql-action/analyze@v3
      with:
        category: "/language:${{matrix.language}}"
```      

### Excluding CodeQL Languages
It's possible you may choose to exclude specific languages from your CodeQL scans. In that case, use the `exclude` input.

Example:
``` yaml
  create-matrix:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.set-matrix.outputs.matrix }}
    steps:
      - name: Get languages from repo
        id: set-matrix
        uses: advanced-security/set-codeql-language-matrix@v1
        with:
          access-token: ${{ secrets.GITHUB_TOKEN }}
          endpoint: ${{ github.event.repository.languages_url }}
          exclude: 'java, python'

```

### Build Mode Override
By default, the action sets the build mode to:
- `none` for most languages (python, javascript, ruby, rust, actions, etc.)
- `manual` for languages that typically require custom build steps (go, swift, java)

If you want to override this behavior and use manual build mode for specific languages, use the `build-mode-manual-override` input:

``` yaml
  create-matrix:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.set-matrix.outputs.matrix }}
    steps:
      - name: Get languages from repo
        id: set-matrix
        uses: advanced-security/set-codeql-language-matrix@v1
        with:
          access-token: ${{ secrets.GITHUB_TOKEN }}
          endpoint: ${{ github.event.repository.languages_url }}
          build-mode-manual-override: 'python, ruby'
```

### Actions support

The GitHub API for [List repository languages](https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28#list-repository-languages) does not by default include "YAML"/"GitHub Actions". This is particularly useful if your repository contains GitHub Actions workflows that you want to include in CodeQL analysis.

To add support for this to your repo, you must add a `.gitattributes` file with the following contents:

```
.github/workflows/*.yml linguist-detectable -linguist-vendored
.github/workflows/*.yaml linguist-detectable -linguist-vendored
```

These directives tell GitHub's linguist to detect YAML files in the `.github/workflows/` directory as a language and not treat them as vendored code, making them visible in the repository languages API.

### Swift support
If you want to include Swift in your CodeQL analysis, you need to ensure that the action runs on a macOS runner. This is because Swift analysis with CodeQL requires a macOS environment. You can achieve this by making the `runs-on` field in your workflow conditional based on the language being analyzed.

Example:
``` yaml
  analyze:
    needs: create-matrix
    if: ${{ needs.create-matrix.outputs.matrix != '[]' }}
    name: Analyze
    runs-on: ${{ matrix.language == 'swift' && 'macos-latest' || 'ubuntu-latest' }}
    permissions:
      actions: read
      contents: read
      security-events: write
```

If you want to run all languages **other than Swift** on a specific group of runners, you can adjust the `runs-on` line in your workflow as shown in the following example:
``` yaml
    runs-on: ${{ matrix.language == 'swift' && 'macos-latest' || fromJSON('{"group":"runner-group-name"}') }}
```

## License 

This project is licensed under the terms of the MIT open source license. Please refer to [MIT](./LICENSE.md) for the full terms.

## Maintainers 

Take a look at [CODEOWNERS](./CODEOWNERS.md) to identify the maintainers.  

Contributions are welcome! If you have an idea for a new feature or improvement, please open an issue or submit a pull request. Maintainers should use the [Contributing Guide](./CONTRIBUTING.md) to control version updates.

## Support

Got a question or issue?  Open an issue in this repo and tag any of the folks in [CODEOWNERS](./CODEOWNERS.md).
