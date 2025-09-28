# Weather Vessel - Logistics Control Tower v2.5

A comprehensive maritime logistics control system with real-time vessel tracking, weather integration, and AI-powered decision support.

## Features

### 🗺️ Real-time Vessel Tracking
- Interactive Leaflet map with vessel route visualization
- Real-time position updates and progress tracking
- Route optimization and ETA calculations

### 🌤️ Weather Integration
- Marine weather data from Open-Meteo API
- ADNOC weather screenshots interpreted by AI for rapid risk flagging
- Clipboard paste and drag-and-drop ingestion for screenshot uploads
- IOI (Index of Operability) calculation (0-100 scale)
- Go/No-Go decision support based on weather conditions
- Real-time marine snapshot display (wave height, wind speed)

### 🤖 AI-Powered Features
- Daily logistics briefing generation
- AI assistant for logistics questions
- Risk analysis and mitigation recommendations
- File upload support (PDF, images, CSV)
- Dedicated AI weather insight panel for screenshot uploads

### 📊 Schedule Management
- Voyage schedule management with CSV/JSON import
- Weather-linked schedule adjustments
- Risk simulation and control
- Live status updates

### ♿ Accessibility (WCAG 2.2 AA)
- Keyboard navigation support
- Screen reader compatibility
- High contrast mode support
- 44px minimum touch targets
- Skip links and ARIA attributes

## Technology Stack

- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Styling**: Tailwind CSS
- **Maps**: Leaflet.js 1.9.4
- **Backend**: FastAPI (Python)
- **AI Integration**: OpenAI API
- **Performance**: Web Workers, requestIdleCallback

## Installation

1. Clone the repository:
```bash
git clone https://github.com/macho715/WEATHER-VESSEL.git
cd WEATHER-VESSEL
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables (supports `.env` file in project root):
```bash
echo "OPENAI_API_KEY=your-openai-api-key" >> .env
# or export directly for the current shell
export OPENAI_API_KEY="your-openai-api-key"
```

4. Start the FastAPI server:
```bash
python -m uvicorn openai_gateway:app --host 0.0.0.0 --port 8000 --reload
```

5. Open `logistics_control_tower_v2.html` in your browser

## Usage

### Basic Operations
- **Vessel Tracking**: View real-time vessel position and route
- **Schedule Upload**: Import voyage schedules via CSV/JSON
- **Weather Data**: Upload weather data (CSV) or ADNOC screenshots for risk analysis
- **AI Assistant**: Ask questions about logistics operations
- **Daily Briefing**: Generate AI-powered operational summaries

### Advanced Features
- **IOI Analysis**: Automatic operability assessment
- **Risk Simulation**: Test different scenarios
- **Weather Linking**: Automatic schedule adjustments based on weather
- **File Analysis**: Upload documents for AI analysis

## API Endpoints

- `GET /health` - Health check
- `POST /api/assistant` - AI assistant chat
- `POST /api/briefing` - Generate daily briefing

## Performance Optimizations

- **Web Workers**: Marine data fetching in background threads
- **Idle Callbacks**: Non-blocking UI updates
- **Passive Event Listeners**: Optimized scroll/touch handling
- **Lazy Loading**: Efficient resource management

## Accessibility Features

- **Keyboard Navigation**: Full keyboard support
- **Screen Reader**: ARIA labels and roles
- **High Contrast**: System preference detection
- **Touch Targets**: 44px minimum size compliance
- **Focus Management**: Proper focus handling in modals

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Open-Meteo for marine weather data
- Leaflet for mapping functionality
- OpenAI for AI capabilities
- Tailwind CSS for styling framework