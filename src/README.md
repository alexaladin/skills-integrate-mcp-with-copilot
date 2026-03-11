# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. (Admin mode) Create local teacher credentials:

   ```
   cp teachers.example.json teachers.json
   ```

   Update `teachers.json` with local teacher usernames/passwords.

3. Run the application:

   ```
   python app.py
   ```

4. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

### Authentication (Admin)

| Method | Endpoint       | Description                                                                                 |
| ------ | -------------- | ------------------------------------------------------------------------------------------- |
| POST   | `/auth/login`  | Authenticate as a teacher; returns an `X-Admin-Token` for use in protected endpoints        |
| POST   | `/auth/logout` | Invalidate the current admin token (requires `X-Admin-Token` header)                        |
| GET    | `/auth/status` | Check whether an admin token is currently valid (requires `X-Admin-Token` header)           |

### Activities

| Method | Endpoint                                                          | Description                                                                        |
| ------ | ----------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count                |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up a student for an activity (requires `X-Admin-Token` header)                |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Remove a student from an activity (requires `X-Admin-Token` header)            |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in memory, which means data will be reset when the server restarts.
