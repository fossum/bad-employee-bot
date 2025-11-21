# Bad Employee Discord Bot

## How to Install

## How to Run Locally

1. Generate a Gemini API token. https://aistudio.google.com/apikey
1. Set the GEMINI_API_KEY environment variable. .env file is recommended.
1. Generate a Discord API token.
    1. https://discord.com/developers/applications
    1. Click on the Bot tab.
    1. Reset the token and save the value somewhere safe. Or just copy it to the next step.
1. Set the DISCORD_APP_TOKEN environment variable.

## Helm Chart Development

This project includes a Helm chart for Kubernetes deployment located in `charts/bad-employee/`.

### Prerequisites

- Helm 3.x installed (included in the devcontainer)

### Updating Chart Dependencies

The chart depends on the TrueCharts common library. To update the `Chart.lock` file:

```bash
cd charts/bad-employee
helm dependency update
```

This will:
- Download the latest version of dependencies specified in `Chart.yaml`
- Update `Chart.lock` with the exact versions
- Store dependency charts in the `charts/` subdirectory

### Testing the Chart

To test the chart locally:

```bash
# Lint the chart
helm lint charts/bad-employee

# Template the chart to see rendered manifests
helm template bad-employee charts/bad-employee

# Dry-run install
helm install bad-employee charts/bad-employee --dry-run --debug
```
