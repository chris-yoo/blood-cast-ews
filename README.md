# Bloodcast - Blood Supply Early Warning System

An AI-driven web application that forecasts blood supply shortages and provides intelligent analysis.

## Tech Stack

- **Frontend**: Next.js 14+ (App Router), Tailwind CSS, Lucide React, shadcn/ui
- **Backend**: FastAPI (Python)
- **AI**: OpenAI API (gpt-4o)

## Project Structure

```
blood-cast-ews/
├── frontend/          # Next.js application
├── backend/        # FastAPI application
└── data/            # CSV data files
```

## Setup Instructions

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies (already installed):
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

### Backend Setup

#### Using Conda (Recommended)

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a conda environment:
```bash
conda create -n bloodcast python=3.10 -y
conda activate bloodcast
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file from the example:
```bash
cp .env.example .env
```

5. Add your OpenAI API key to `.env`:
```
OPENAI_API_KEY=your_actual_api_key_here
```

6. Run the FastAPI server:
```bash
python -m uvicorn main:app --reload
```

#### Using venv (Alternative)

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file from the example:
```bash
cp .env.example .env
```

5. Add your OpenAI API key to `.env`:
```
OPENAI_API_KEY=your_actual_api_key_here
```

6. Run the FastAPI server:
```bash
python -m uvicorn main:app --reload
```

The backend will be available at `http://localhost:8000` or `http://127.0.0.1:8000`

**Note:** Make sure to activate the conda environment (`conda activate bloodcast`) before running the server.

## Features

### Home Page (Dashboard)
- Visual display of forecasted blood shortages for 1, 2, and 3 months ahead
- Color-coded severity indicators (Yellow/Orange/Red)
- Interactive shortage cards with detail modals
- "Chat with AI" and "Generate Report" actions

### Chat AI Page
- Conversational interface for asking questions about blood supply
- Region and Blood Type selection
- Pre-filled context when navigating from shortage cards
- Real-time AI responses

### Report Generation
- AI-powered analysis of specific shortages
- PDF export functionality
- Copy to clipboard feature

## API Endpoints

### POST /analyze
Analyzes a blood supply shortage and generates a detailed report.

**Request Body:**
```json
{
  "region": "Seoul-Central",
  "bloodType": "A",
  "month": 1
}
```

**Response:**
```json
{
  "report": "Detailed analysis report...",
  "region": "Seoul-Central",
  "bloodType": "A",
  "month": 1
}
```

### POST /chat
Handles conversational Q&A about blood supply forecasts.

**Request Body:**
```json
{
  "message": "Why is it decreasing?",
  "region": "Seoul-Central",
  "bloodType": "A"
}
```

**Response:**
```json
{
  "response": "AI response text..."
}
```

## Development Notes

- The application uses mock data for now (see `frontend/lib/mockData.ts`)
- CSV data is available in `data/blood_inventory.csv` for future integration
- CORS is enabled for localhost:3000
- The design follows HCI principles with a medical/blood service color palette (Red, White, Soft Grays)

## License

MIT

