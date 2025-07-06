# Bad Employee Chart

## Development

### Release Steps

1. Increment version number in Chart.yaml
1. Run the steps in [[verify/test release]]

### Verify/test release

1. `helm dependency build charts/bad-employee`
1. `helm lint charts`
1. `helm template charts/bad-employee/`
1. `helm install bad-employee-bot charts/bad-employee --dry-run`

### Development Setup

1. `sudo snap install --classic`
1. `scp username@cluster-host:/etc/rancher/k3s/k3s.yaml ~/.kube/k3s-elite5.kubeconfig`
1. `chmod 600 ~/.kube/k3s-elite5.kubeconfig`
1. `nano ~/.kube/k3s-elite5.kubeconfig`, then modify the server address
1. `export KUBECONFIG=~/.kube/k3s-elite5.kubeconfig`

### Installing the development version

1. `helm upgrade --install bad-employee-bot charts/bad-employee --set workload.main.podSpec.containers.main.env.DISCORD_APP_TOKEN="YOUR_DISCORD_APP_TOKEN" --set workload.main.podSpec.containers.main.env.GEMINI_API_KEY="YOUR_GEMINI_API_KEY" --set global.fallbackDefaults.storageClass=longhorn`
