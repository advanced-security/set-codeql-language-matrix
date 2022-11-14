# set-codeql-languages

This action reads the languages API for your repository and sets the CodeQL supported languages as the job matrix for your Actions run.

## Why use this action?

The default Actions workflow for CodeQL auto-populates the job matrix with your repo's supported CodeQL languages.  However, as new code is added to a repository, that language matrix is not updated.  You need to manually add those languages to the matrix definition to have CodeQL scan them.  

This action reads the repository languages API and adds all supported languages to the job matrix.  No additional configuration is required.

## How to use this action

Call this action before defining the CodeQL analyze job strategy, then set the matrix to the output from the action: `${{ fromJSON(needs.create-matrix.outputs.matrix) }}`

**Example**
```
name: "CodeQL"

on: workflow_dispatch

jobs:
  create-matrix:
    name: Set CodeQL Languages
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.set-matrix.outputs.languages }}
    steps:
      - name: Get languages from repo
        id: get-languages
        uses: leftrightleft/set-codeql-languages@main
        with:
          access-token: ${{ secrets.GITHUB_TOKEN }}
          endpoint: ${{ github.event.repository.languages_url }}
          
  analyze:
    needs: create-matrix
    name: Analyze
    runs-on: ubuntu-latest
    permissions:
      actions: read
      contents: read
      security-events: write

    strategy:
      fail-fast: false
      matrix: 
        language: ${{ fromJSON(needs.create-matrix.outputs.matrix) }} # Set output from create-matrix job
        # CodeQL supports [ 'cpp', 'csharp', 'go', 'java', 'javascript', 'python' ]

    steps:
    - name: Checkout repository
      uses: actions/checkout@v2

    - name: Initialize CodeQL
      uses: github/codeql-action/init@v2
      with:
        languages: ${{ matrix.language }}

    - name: Autobuild
      uses: github/codeql-action/autobuild@v1

    - name: Perform CodeQL Analysis
      uses: github/codeql-action/analyze@v2