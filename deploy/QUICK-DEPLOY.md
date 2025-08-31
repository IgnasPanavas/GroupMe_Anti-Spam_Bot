# Quick Deployment Guide

## 🚀 **Vercel Deployment (Recommended)**

### **Option 1: GitHub Integration (Easiest)**
1. **Push your code to GitHub**
2. **Go to [vercel.com](https://vercel.com)**
3. **Import your repository**
4. **Vercel will automatically detect it's a React app**
5. **Deploy!**

### **Option 2: Vercel CLI**
```bash
cd spamshield-frontend
npm install -g vercel
vercel --prod
```

## 🌐 **Netlify Deployment (Alternative)**

### **Option 1: Drag & Drop**
1. **Build the app:**
   ```bash
   cd spamshield-frontend
   npm run build
   ```
2. **Go to [netlify.com](https://netlify.com)**
3. **Drag the `build` folder to deploy**

### **Option 2: GitHub Integration**
1. **Connect your GitHub repo to Netlify**
2. **Set build command:** `npm run build`
3. **Set publish directory:** `build`
4. **Deploy!**

## 🔧 **Fix for Build Issues**

If you encounter build errors, try these fixes:

### **1. Clear npm cache:**
```bash
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

### **2. Use legacy peer deps:**
```bash
npm install --legacy-peer-deps
```

### **3. Update Node.js version:**
- Use Node.js 18.x (LTS)
- Avoid Node.js 22.x for now

## 🌐 **Custom Domain Setup**

### **For Vercel:**
1. **Deploy your app**
2. **Go to Project Settings → Domains**
3. **Add custom domain:** `spamshield.ignaspanavas.com`
4. **Update DNS records** at your domain registrar

### **For Netlify:**
1. **Deploy your app**
2. **Go to Site Settings → Domain management**
3. **Add custom domain:** `spamshield.ignaspanavas.com`
4. **Update DNS records** at your domain registrar

## 📋 **DNS Records**

Add this CNAME record at your domain registrar:
```
Type: CNAME
Name: spamshield
Value: your-deployment-url.vercel.app (or netlify.app)
TTL: 3600
```

## 🎯 **Recommended Steps**

1. **Use Vercel** (easiest deployment)
2. **Connect your GitHub repo**
3. **Deploy automatically**
4. **Add custom domain**
5. **Update DNS records**
6. **Test your site!**

## 🔍 **Testing**

After deployment:
1. **Test the main site**
2. **Test the prediction feature**
3. **Test on mobile**
4. **Check all links work**

## 🆘 **Troubleshooting**

### **Build Fails:**
- Check Node.js version (use 18.x)
- Clear npm cache
- Use `--legacy-peer-deps`

### **Domain Not Working:**
- Wait for DNS propagation (15-30 minutes)
- Check DNS records are correct
- Verify SSL certificate

### **API Not Working:**
- Update API URL in environment variables
- Ensure API server is running
- Check CORS settings
