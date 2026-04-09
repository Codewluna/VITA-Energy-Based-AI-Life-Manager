# VITA Backend — Setup Guide

Complete step-by-step instructions to run the VITA AI Life Manager backend.
No paid API keys required. Uses a rule-based AI engine built into the app.

---

## Project Structure

```
vita-backend/
  app.py                              <- Flask entry point (run this)
  requirements.txt                    <- Python dependencies
  .env                                <- Environment variables
  VITA_API.postman_collection.json    <- Import into Postman
  README.md                           <- This file

  models/
    schemas.py                        <- MongoDB document schemas

  routes/
    auth.py                           <- Register, login, profile
    tasks.py                          <- Task CRUD
    energy.py                         <- Energy logging
    wellbeing.py                      <- Water, food, movement, rest
    chat.py                           <- VITA AI message responding

  services/
    vita_brain.py                     <- Rule-based AI engine (no API key)
    auth_utils.py                     <- JWT helpers

  static/
    index.html                        <- Frontend (served by Flask)
```

---

## Step 1 — Install Prerequisites

You need:
- Python 3.10 or higher
- MongoDB (Community Edition)
- Postman (for API testing)

Check Python version:
```
python --version
```

---

## Step 2 — Install MongoDB

### Windows
1. Go to: https://www.mongodb.com/try/download/community
2. Download MongoDB Community Server (MSI installer)
3. Run the installer, choose "Complete" setup
4. MongoDB installs as a Windows Service and starts automatically

Verify it is running:
```
mongosh
```
You should see a prompt. Type `exit` to leave.

### macOS (using Homebrew)
```
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

### Linux (Ubuntu/Debian)
```
sudo apt install -y mongodb
sudo systemctl start mongodb
sudo systemctl enable mongodb
```

---

## Step 3 — Set Up the Python Environment

Navigate into the project folder:
```
cd vita-backend
```

Create a virtual environment:
```
python -m venv venv
```

Activate it:
- Windows:  `venv\Scripts\activate`
- Mac/Linux: `source venv/bin/activate`

Install dependencies:
```
pip install -r requirements.txt
```

---

## Step 4 — Configure Environment Variables

Open `.env` and confirm these values:

```
MONGO_URI=mongodb://localhost:27017/vitadb
SECRET_KEY=vita-super-secret-key-change-in-production
FLASK_ENV=development
FLASK_DEBUG=1
PORT=5000
```

Leave MONGO_URI as-is if MongoDB is running locally on the default port.
Change SECRET_KEY to something random before any public deployment.

---

## Step 5 — Run the Backend

With your virtual environment active:
```
python app.py
```

You should see:
```
  VITA backend starting on http://localhost:5000
  MongoDB URI: mongodb://localhost:27017/vitadb
```

Test it is working:
Open your browser and go to:
```
http://localhost:5000/api/health
```

You should see:
```json
{
  "status": "VITA backend online",
  "database": "connected",
  "version": "1.0.0"
}
```

---

## Step 6 — Open the Frontend

While the backend is running, open the frontend in your browser:
```
http://localhost:5000/static/index.html
```

Or open the file `static/index.html` directly in a browser.
The frontend is pre-configured to connect to `http://localhost:5000/api`.

---

## Step 7 — Test with Postman

1. Open Postman
2. Click "Import" (top left)
3. Select the file: `VITA_API.postman_collection.json`
4. The collection loads with all endpoints pre-configured

### Workflow to test everything:

Step A — Register an account:
- Open "Auth > Register"
- Send the request
- The token is saved automatically to collection variables

Step B — Log your energy:
- Open "Energy > Log Energy Level"
- Change `"level"` to one of: `high`, `medium`, `low`, `depleted`
- Send — you get back an AI insight message

Step C — Create a task:
- Open "Tasks > Create Task"
- Change the name/energy/category fields
- Send — task is created and returned

Step D — Send a chat message:
- Open "Chat > Send Message"
- Change `"message"` to any question, e.g. "What should I do first today?"
- Send — VITA responds based on your energy, tasks, and wellbeing data

Step E — Log wellbeing:
- Use "Wellbeing > Add Water", "Log Meal", "Log Movement", "Log Rest"
- Each call updates today's record

---

## API Reference Summary

### Auth
| Method | Endpoint             | Description              | Auth |
|--------|----------------------|--------------------------|------|
| POST   | /api/auth/register   | Create account           | No   |
| POST   | /api/auth/login      | Login, receive JWT token | No   |
| GET    | /api/auth/me         | Get profile              | Yes  |

### Tasks
| Method | Endpoint                    | Description          | Auth |
|--------|-----------------------------|----------------------|------|
| GET    | /api/tasks                  | Get all tasks        | Yes  |
| POST   | /api/tasks                  | Create task          | Yes  |
| PATCH  | /api/tasks/:id              | Update task fields   | Yes  |
| POST   | /api/tasks/:id/toggle       | Toggle done/undone   | Yes  |
| DELETE | /api/tasks/:id              | Delete task          | Yes  |

### Energy
| Method | Endpoint              | Description                      | Auth |
|--------|-----------------------|----------------------------------|------|
| POST   | /api/energy           | Log energy + get AI insight      | Yes  |
| GET    | /api/energy/history   | Last 14 energy log entries       | Yes  |

### Wellbeing
| Method | Endpoint              | Description                          | Auth |
|--------|-----------------------|--------------------------------------|------|
| GET    | /api/wellbeing        | Get today's wellbeing record         | Yes  |
| PATCH  | /api/wellbeing        | Update water/movement/rest/meal      | Yes  |
| GET    | /api/wellbeing/tip    | Get a random VITA wellness tip       | Yes  |

PATCH /api/wellbeing accepts these body fields:
- `water: <int>`       — set absolute water count
- `add_water: <int>`   — add to water count
- `add_move: <int>`    — add minutes of movement
- `add_rest: <int>`    — add minutes of rest
- `log_meal: true`     — log current time as last meal

### Chat
| Method | Endpoint          | Description                       | Auth |
|--------|-------------------|-----------------------------------|------|
| POST   | /api/chat         | Send message, get VITA response   | Yes  |
| GET    | /api/chat/history | Last 30 messages                  | Yes  |
| DELETE | /api/chat         | Clear all chat history            | Yes  |

### Auth Header Format
All protected endpoints require:
```
Authorization: Bearer <your_jwt_token>
```

---

## How the AI Response Engine Works

VITA does not use any external API. The `services/vita_brain.py` file contains:

1. Intent detection — analyses the user's message for keywords related to
   energy, food, water, movement, rest, focus, overwhelm, and task prioritisation

2. Context loading — before responding, the engine reads the user's current
   energy level, task list, and today's wellbeing data from MongoDB

3. Response generation — selects the most relevant response template
   and fills in real data (task names, energy level, water count, etc.)

4. Energy matching — when asked to prioritise tasks, sorts the user's
   pending tasks by how closely their energy requirement matches the
   user's current state

To add more response patterns, edit `services/vita_brain.py`:
- Add keywords to `detect_intent()`
- Add a response block in `generate_response()`
- Add tip strings to `WELLBEING_TIPS` or `ENERGY_INSIGHTS`

---

## Common Issues

MongoDB connection error:
- Make sure MongoDB is running before starting Flask
- Windows: check Services for "MongoDB" or run `net start MongoDB`
- Mac: run `brew services start mongodb-community`

Port already in use:
- Change `PORT=5001` in `.env` and update the frontend API constant:
  In `static/index.html` change `const API = "http://localhost:5000/api";`
  to `const API = "http://localhost:5001/api";`

CORS error in browser:
- The backend has CORS enabled for all origins in development
- If you see CORS errors, confirm the Flask server is running

Token expired:
- JWT tokens last 7 days
- Log in again to get a fresh token
