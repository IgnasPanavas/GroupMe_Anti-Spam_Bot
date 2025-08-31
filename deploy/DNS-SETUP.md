# DNS Setup Guide for ignaspanavas.com

This guide will help you set up a subdomain for your SpamShield frontend.

## 🌐 **Recommended Subdomain Options**

- `spamshield.ignaspanavas.com` - Professional and clear
- `bot.ignaspanavas.com` - Short and memorable
- `shield.ignaspanavas.com` - Simple and catchy

## 📋 **DNS Configuration Steps**

### **Step 1: Choose Your Hosting Platform**

#### **Option A: Netlify (Recommended)**
1. Deploy using: `./deploy/netlify-deploy.sh`
2. Netlify will provide you with nameservers or CNAME records

#### **Option B: Vercel**
1. Deploy using: `./deploy/vercel-deploy.sh`
2. Vercel will provide you with CNAME records

#### **Option C: AWS S3**
1. Deploy using: `./deploy/aws-deploy.sh`
2. You'll get an S3 website URL

### **Step 2: Configure DNS Records**

#### **For Netlify/Vercel (CNAME Method)**
Add this CNAME record at your domain registrar:

```
Type: CNAME
Name: spamshield (or your chosen subdomain)
Value: your-deployment-url.netlify.app (or vercel.app)
TTL: 3600 (or default)
```

#### **For AWS S3 (A Record Method)**
If using Route 53:
```
Type: A
Name: spamshield
Value: [S3 bucket endpoint]
TTL: 300
```

### **Step 3: Update Environment Variables**

Create a `.env.production` file in `spamshield-frontend/`:
```env
REACT_APP_API_URL=https://your-api-domain.com/api
```

## 🔧 **Domain Registrar Instructions**

### **Popular Registrars:**

#### **GoDaddy**
1. Log into your GoDaddy account
2. Go to "My Products" → "DNS"
3. Find your domain and click "DNS"
4. Add CNAME record:
   - Type: CNAME
   - Name: spamshield
   - Value: your-deployment-url.netlify.app
   - TTL: 1 hour

#### **Namecheap**
1. Log into your Namecheap account
2. Go to "Domain List" → "Manage"
3. Click "Advanced DNS"
4. Add CNAME record:
   - Type: CNAME Record
   - Host: spamshield
   - Value: your-deployment-url.netlify.app
   - TTL: Automatic

#### **Google Domains**
1. Log into Google Domains
2. Select your domain
3. Go to "DNS" → "Custom records"
4. Add CNAME record:
   - Type: CNAME
   - Name: spamshield
   - Value: your-deployment-url.netlify.app
   - TTL: 1 hour

## ⏱️ **DNS Propagation**

- **CNAME records**: 15 minutes to 48 hours
- **A records**: 15 minutes to 48 hours
- **Nameservers**: 24-48 hours

## 🔍 **Testing Your Setup**

1. **Check DNS propagation:**
   ```bash
   nslookup spamshield.ignaspanavas.com
   ```

2. **Test website access:**
   ```bash
   curl -I http://spamshield.ignaspanavas.com
   ```

3. **Check SSL certificate** (if using HTTPS):
   ```bash
   openssl s_client -connect spamshield.ignaspanavas.com:443
   ```

## 🚀 **Quick Deployment Commands**

### **Netlify (Easiest)**
```bash
cd spamshield-frontend
chmod +x ../deploy/netlify-deploy.sh
../deploy/netlify-deploy.sh
```

### **Vercel**
```bash
cd spamshield-frontend
chmod +x ../deploy/vercel-deploy.sh
../deploy/vercel-deploy.sh
```

### **AWS S3**
```bash
cd spamshield-frontend
chmod +x ../deploy/aws-deploy.sh
../deploy/aws-deploy.sh
```

## 🎯 **Recommended Setup**

1. **Use Netlify** for the easiest deployment
2. **Choose subdomain**: `spamshield.ignaspanavas.com`
3. **Set up CNAME record** pointing to your Netlify URL
4. **Wait for DNS propagation** (usually 15-30 minutes)
5. **Test your site** at the new URL

## 🔒 **SSL/HTTPS**

- **Netlify/Vercel**: Automatic SSL certificates
- **AWS S3**: Requires CloudFront for HTTPS
- **All platforms**: Free Let's Encrypt certificates available

## 📞 **Support**

If you encounter issues:
1. Check DNS propagation with `nslookup`
2. Verify CNAME records are correct
3. Contact your domain registrar's support
4. Check hosting platform documentation
