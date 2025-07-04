{{/*
Expand the name of the chart.
*/}}
{{- define "bad-employee-bot.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "bad-employee-bot.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart-level labels to be applied to every resource that comes from this chart.
*/}}
{{- define "bad-employee-bot.labels" -}}
helm.sh/chart: {{ include "bad-employee-bot.name" . }}-{{ .Chart.Version }}
{{ include "bad-employee-bot.selectorLabels" . }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "bad-employee-bot.selectorLabels" -}}
app.kubernetes.io/name: {{ include "bad-employee-bot.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "bad-employee-bot.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "bad-employee-bot.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Get the name of the secret to use
*/}}
{{- define "bad-employee-bot.secretName" -}}
{{- .Values.existingSecret | default (include "bad-employee-bot.fullname" .) }}
{{- end }}
