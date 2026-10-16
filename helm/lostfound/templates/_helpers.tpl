{{- define "lostfound.labels" -}}
app.kubernetes.io/part-of: campus-lost-and-found
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end }}

{{- define "lostfound.backendImage" -}}
{{ .Values.backend.image }}:{{ required "backend.tag must be set to a Git commit SHA" .Values.backend.tag }}
{{- end }}

{{- define "lostfound.frontendImage" -}}
{{ .Values.frontend.image }}:{{ required "frontend.tag must be set to a Git commit SHA" .Values.frontend.tag }}
{{- end }}
