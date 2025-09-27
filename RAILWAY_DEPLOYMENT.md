# Railway Deployment Guide for CashifyGCmart

This guide will help you deploy your React application to Railway using Docker.

## Prerequisites

- A Railway account (sign up at [railway.app](https://railway.app))
- Your project code pushed to a Git repository (GitHub, GitLab, or Bitbucket)
- Docker installed locally (for testing)

## Files Created for Railway Deployment

The following files have been created/optimized for Railway deployment:

### 1. `Dockerfile`
- Multi-stage build for production optimization
- Uses Node.js 20 (required for react-router-dom@7.9.3)
- Includes security best practices (non-root user)
- Health check configuration
- Optimized for Railway's environment

### 2. `.dockerignore`
- Excludes unnecessary files from Docker build context
- Reduces build time and image size
- Excludes development files, logs, and temporary files

### 3. `railway.json`
- Railway-specific configuration
- Defines build and deployment settings
- Health check configuration
- Restart policy settings

## Deployment Steps

### Step 1: Prepare Your Repository

1. Ensure all files are committed to your Git repository:
   ```bash
   git add .
   git commit -m "Add Railway deployment configuration"
   git push origin main
   ```

### Step 2: Deploy to Railway

#### Option A: Deploy via Railway Dashboard

1. Go to [railway.app](https://railway.app) and sign in
2. Click "New Project"
3. Select "Deploy from GitHub repo" (or your preferred Git provider)
4. Choose your repository
5. Railway will automatically detect the Dockerfile and start building
6. Wait for the build to complete (usually 2-5 minutes)

#### Option B: Deploy via Railway CLI

1. Install Railway CLI:
   ```bash
   npm install -g @railway/cli
   ```

2. Login to Railway:
   ```bash
   railway login
   ```

3. Initialize and deploy:
   ```bash
   railway init
   railway up
   ```

### Step 3: Configure Environment Variables

If your app uses environment variables, set them in Railway:

1. Go to your project dashboard
2. Click on your service
3. Go to "Variables" tab
4. Add your environment variables:
   - `REACT_APP_BACKEND_URL` (if you have a backend)
   - Any other environment variables your app needs

### Step 4: Custom Domain (Optional)

1. In your Railway project dashboard
2. Go to "Settings" → "Domains"
3. Add your custom domain
4. Configure DNS records as instructed

## Local Testing

Before deploying, you can test the Docker build locally:

```bash
# Build the Docker image
docker build -t cashifygcmart-app .

# Run the container
docker run -d -p 3000:3000 --name cashifygcmart-test cashifygcmart-app

# Test the application
curl http://localhost:3000

# Clean up
docker stop cashifygcmart-test && docker rm cashifygcmart-test
```

## Railway Configuration Details

### Build Configuration
- **Builder**: Dockerfile
- **Dockerfile Path**: `Dockerfile`
- **Build Command**: Automatically detected from Dockerfile

### Runtime Configuration
- **Start Command**: `serve -s build -l tcp://0.0.0.0:$PORT`
- **Port**: Automatically assigned by Railway (uses `$PORT` environment variable)
- **Health Check**: Configured to check root path (`/`)

### Security Features
- Non-root user execution
- Minimal Alpine Linux base image
- Multi-stage build to reduce final image size
- Health checks for container monitoring

## Monitoring and Logs

1. **View Logs**: Go to your Railway project → Service → "Deployments" tab
2. **Monitor Performance**: Use Railway's built-in metrics
3. **Health Checks**: Railway will automatically restart containers if health checks fail

## Troubleshooting

### Common Issues

1. **Build Failures**:
   - Check that all dependencies are properly listed in `package.json`
   - Ensure Node.js version compatibility (we're using Node 20)

2. **Runtime Errors**:
   - Check Railway logs for error messages
   - Verify environment variables are set correctly
   - Ensure the app listens on the correct port (Railway sets `$PORT`)

3. **Health Check Failures**:
   - Verify the app responds to requests on the root path
   - Check that the serve command is working correctly

### Debug Commands

```bash
# View Railway logs
railway logs

# Connect to Railway shell
railway shell

# Check service status
railway status
```

## Performance Optimization

The Dockerfile includes several optimizations:

1. **Multi-stage build**: Separates build and runtime environments
2. **Layer caching**: Optimized layer ordering for better caching
3. **Minimal runtime**: Only includes necessary files in the final image
4. **Alpine Linux**: Smaller base image for faster deployments

## Cost Considerations

- Railway offers a free tier with usage limits
- Monitor your usage in the Railway dashboard
- Consider upgrading to a paid plan for production workloads

## Next Steps

1. Set up monitoring and alerting
2. Configure custom domain
3. Set up CI/CD for automatic deployments
4. Configure backup strategies for your data

## Support

- Railway Documentation: [docs.railway.app](https://docs.railway.app)
- Railway Community: [discord.gg/railway](https://discord.gg/railway)
- Project Issues: Create an issue in your repository

---

Your CashifyGCmart application is now ready for Railway deployment! 🚀
