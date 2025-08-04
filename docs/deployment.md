# Deployment

## Production Docker Setup

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  app:
    build: 
      context: .
      dockerfile: Dockerfile.prod
    ports:
      - "8000:8000"
    environment:
      - ENV=production
      - WORKERS=4
    deploy:
      resources:
        limits:
          memory: 8G
        reservations:
          memory: 4G
    volumes:
      - /dev/snd:/dev/snd
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl
```

## Kubernetes Deployment

```yaml
# k8s/deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: graphrag-agent-mk1
spec:
  replicas: 3
  selector:
    matchLabels:
      app: graphrag-agent-mk1
  template:
    metadata:
      labels:
        app: graphrag-agent-mk1
    spec:
      containers:
      - name: app
        image: graphrag-agent-mk1:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        volumeMounts:
        - name: models
          mountPath: /app/voice/models
        - name: audio-device
          mountPath: /dev/snd
      volumes:
      - name: models
        persistentVolumeClaim:
          claimName: models-pvc
      - name: audio-device
        hostPath:
          path: /dev/snd
```
