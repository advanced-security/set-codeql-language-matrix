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
      matrix: ${{ steps.set-matrix.outputs.languages }}
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
      matrix: 
        language: ${{ fromJSON(needs.create-matrix.outputs.matrix) }}

    steps:
    - name: Checkout repository
      uses: actions/checkout@v3

    # Initializes the CodeQL tools for scanning.
    - name: Initialize CodeQL
      uses: github/codeql-action/init@v3
      with:
        languages: ${{ matrix.language }}
 
    # Autobuild attempts to build any compiled languages  (C/C++, C#, or Java).
    - name: Autobuild
      uses: github/codeql-action/autobuild@v3

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
      matrix: ${{ steps.set-matrix.outputs.languages }}
    steps:
      - name: Get languages from repo
        id: set-matrix
        uses: advanced-security/set-codeql-language-matrix@v1
        with:
          access-token: ${{ secrets.GITHUB_TOKEN }}
          endpoint: ${{ github.event.repository.languages_url }}
          exclude: 'java, python'

```

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

## Support

Got a question or issue?  Open an issue in this repo and tag any of the folks in [CODEOWNERS](./CODEOWNERS.md).
