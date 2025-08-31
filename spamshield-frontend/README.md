# SpamShield Frontend

A modern React frontend for the SpamShield GroupMe anti-spam bot, featuring live spam prediction and real-time monitoring.

## 🚀 Features

- **Live Spam Detection** - Test messages with real-time AI predictions
- **Interactive Dashboard** - Monitor bot performance and statistics
- **Professional UI** - Modern, responsive design with Tailwind CSS
- **Real-time Data** - Live statistics and activity feeds
- **Mobile Responsive** - Works perfectly on all devices

## 🛠️ Tech Stack

- **React 18** - Modern React with hooks
- **Tailwind CSS** - Utility-first CSS framework
- **Chart.js** - Interactive data visualization
- **Axios** - HTTP client for API calls
- **React Router** - Client-side routing

## 📁 Project Structure

```
spamshield-frontend/
├── public/
│   └── index.html          # HTML template
├── src/
│   ├── components/         # React components
│   │   ├── Header.jsx
│   │   ├── Hero.jsx
│   │   ├── PredictionBox.jsx  # 🎯 Main feature
│   │   ├── Dashboard.jsx
│   │   ├── Stats.jsx
│   │   ├── Charts.jsx
│   │   └── Footer.jsx
│   ├── services/
│   │   └── api.js          # API service layer
│   ├── App.jsx             # Main app component
│   ├── index.js            # Entry point
│   └── index.css           # Global styles
├── package.json
├── tailwind.config.js
└── README.md
```

## 🚀 Quick Start

### Prerequisites
- Node.js (v16 or higher)
- npm or yarn
- Python 3.8+ (for API server)

### Installation

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Start the API server** (in another terminal):
   ```bash
   cd ..  # Go back to project root
   python api/prediction_server.py
   ```

3. **Start the React development server:**
   ```bash
   npm start
   ```

4. **Open your browser:**
   - Frontend: http://localhost:3000
   - API: http://localhost:5001

## 🎯 Key Features

### Live Spam Detection
The main feature allows users to:
- Enter any message for instant spam analysis
- See confidence scores and predictions
- View processed text and AI reasoning
- Try example messages to test the system

### Dashboard
- Real-time statistics from the bot
- Interactive charts showing spam detection trends
- Recent activity feed
- Protected groups overview

### Professional Design
- Modern gradient backgrounds
- Responsive layout for all devices
- Smooth animations and transitions
- Professional color scheme

## 🔧 Development

### Available Scripts

```bash
npm start          # Start development server
npm run build      # Build for production
npm test           # Run tests
npm run eject      # Eject from Create React App
```

### API Integration

The frontend communicates with the Python API server:
- **Base URL**: http://localhost:5001/api
- **Prediction Endpoint**: POST /api/predict
- **Statistics**: GET /api/stats
- **Health Check**: GET /api/health

### Environment Variables

Create a `.env` file in the frontend directory:
```env
REACT_APP_API_URL=http://localhost:5001/api
```

## 🎨 Customization

### Styling
- Uses Tailwind CSS for styling
- Custom gradients and colors in `index.css`
- Responsive design with mobile-first approach

### Components
- Modular component architecture
- Reusable components for consistency
- Easy to extend and modify

## 📱 Mobile Support

Fully responsive design that works on:
- **Desktop** - Full dashboard experience
- **Tablet** - Adaptive layout
- **Mobile** - Touch-friendly interface

## 🚀 Deployment

### Build for Production
```bash
npm run build
```

### Deploy Options
- **Netlify** - Drag and drop the `build` folder
- **Vercel** - Connect GitHub repository
- **AWS S3** - Upload build files
- **GitHub Pages** - Deploy from repository

### Environment Setup
For production deployment, update the API URL:
```env
REACT_APP_API_URL=https://your-api-domain.com/api
```

## 🔒 Security

- API calls use HTTPS in production
- No sensitive data stored in frontend
- CORS properly configured
- Input validation on all forms

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is part of the SpamShield GroupMe bot and follows the same license terms.

## 🆘 Troubleshooting

### Common Issues

**API Connection Failed**
- Ensure the Python API server is running
- Check that the API URL is correct
- Verify CORS settings

**Build Errors**
- Clear node_modules and reinstall: `rm -rf node_modules && npm install`
- Check Node.js version compatibility

**Styling Issues**
- Ensure Tailwind CSS is properly configured
- Check that PostCSS is installed

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review the API documentation
3. Open an issue on GitHub
