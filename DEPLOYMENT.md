# 🚀 Deployment Guide

This guide covers multiple deployment options for the AI Document Processor.

## 📋 Prerequisites

Before deploying, ensure you have:
- ✅ OpenAI API key with GPT-4o access
- ✅ Domain name (optional)
- ✅ SSL certificates (for production)

## 🐳 Option 1: Docker Deployment (Recommended)

### Local Server / VPS Deployment

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/ai-document-processor.git
cd ai-document-processor

# 2. Create production environment file
cp .env.example .env.production
# Edit .env.production with your keys

# 3. Build and run with Docker Compose
docker-compose -f deploy/docker/docker-compose.prod.yml up -d

# 4. Check services
docker-compose -f deploy/docker/docker-compose.prod.yml ps
```

Access at: `http://your-server-ip`

### Using Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c deploy/docker/docker-compose.prod.yml docprocessor

# Check services
docker service ls
```

## 🚄 Option 2: Railway Deployment

Railway offers easy deployment with automatic SSL and scaling.

### Steps:
1. Install Railway CLI: `npm install -g @railway/cli`
2. Login: `railway login`
3. Initialize project:
```bash
cd ai-document-processor
railway init
```
4. Add environment variables in Railway dashboard:
   - `OPENAI_API_KEY`
   - `AWS_ACCESS_KEY_ID` (optional)
   - `AWS_SECRET_ACCESS_KEY` (optional)

5. Deploy:
```bash
railway up
```

Your app will be available at: `https://your-app.railway.app`

## 🔺 Option 3: Vercel + Supabase

Perfect for serverless deployment.

### Frontend (Vercel):
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy frontend
cd frontend
vercel

# Set environment variables
vercel env add NEXT_PUBLIC_API_URL
```

### Backend (Separate service):
Deploy backend to Railway, Render, or Heroku and update `NEXT_PUBLIC_API_URL`.

## 🎯 Option 4: Render Deployment

Render offers free tier with automatic deploys.

1. Fork the repository
2. Connect GitHub to Render
3. Create new Web Service
4. Use `deploy/render/render.yaml` as blueprint
5. Add environment variables:
   - `OPENAI_API_KEY`
   - Database is auto-provisioned

## ☁️ Option 5: AWS Deployment

### Using AWS Copilot

```bash
# Install Copilot
curl -Lo copilot https://github.com/aws/copilot-cli/releases/latest/download/copilot-linux
chmod +x copilot
sudo mv copilot /usr/local/bin/copilot

# Initialize application
copilot app init ai-document-processor

# Deploy environments
copilot env deploy --name production

# Deploy services
copilot svc deploy --name api --env production
copilot svc deploy --name frontend --env production
```

### Using ECS with Fargate

See `deploy/aws/cloudformation.yaml` for infrastructure as code.

## 🌐 Option 6: Kubernetes Deployment

```bash
# Apply configurations
kubectl apply -f deploy/k8s/

# Check pods
kubectl get pods -n document-processor

# Get service URL
kubectl get svc -n document-processor
```

## 🔒 SSL/TLS Configuration

### Using Let's Encrypt

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Generate certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

### Using Cloudflare

1. Add your domain to Cloudflare
2. Update DNS to point to your server
3. Enable "Full (strict)" SSL mode
4. Use Cloudflare origin certificates

## 📊 Monitoring

### Health Checks

All deployments include health check endpoints:
- Frontend: `GET /`
- Backend: `GET /health`
- API Docs: `GET /docs`

### Recommended Monitoring Tools

- **Uptime**: UptimeRobot, Pingdom
- **Logs**: LogDNA, Papertrail
- **APM**: New Relic, DataDog
- **Error Tracking**: Sentry

## 🔧 Environment Variables

### Required
```env
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://...
```

### Optional
```env
# AWS S3
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
S3_BUCKET_NAME=...

# Monitoring
SENTRY_DSN=...
NEW_RELIC_LICENSE_KEY=...

# Email (for notifications)
SMTP_HOST=...
SMTP_PORT=...
SMTP_USER=...
SMTP_PASSWORD=...
```

## 🚨 Troubleshooting

### Common Issues

1. **Port conflicts**: Use the port detection script
   ```bash
   ./scripts/check-ports.sh
   ```

2. **Memory issues**: Increase Docker memory
   ```bash
   docker-compose -f deploy/docker/docker-compose.prod.yml up -d --scale worker=1
   ```

3. **Database connection**: Check connection string
   ```bash
   docker-compose exec api python -c "from app.db import engine; print(engine.url)"
   ```

## 🎯 Performance Optimization

### Caching
- Enable Redis caching
- Use CDN for static assets
- Cache API responses

### Scaling
- Horizontal scaling: Add more workers
- Vertical scaling: Increase resources
- Auto-scaling: Use cloud provider features

## 📱 Mobile Considerations

The frontend is responsive and works on mobile devices. For better performance:
- Enable service workers
- Use progressive web app features
- Optimize images

## 🔄 Continuous Deployment

### GitHub Actions
```yaml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to production
        run: |
          # Your deployment commands
```

## 📞 Support

- GitHub Issues: [Report issues](https://github.com/yourusername/ai-document-processor/issues)
- Discord: [Join community](https://discord.gg/yourdiscord)
- Email: support@yourdomain.com