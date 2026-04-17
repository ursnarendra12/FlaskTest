# Flask Backend API

## Overview
This project is a backend service built using Flask that handles user authentication, API routing, and database operations. It is designed to simulate a real-world microservice with modular architecture and middleware handling.

## Architecture
- Layered structure: Routes → Services → Database
- Authentication handled using middleware
- Redis used for caching/session handling
- Config-driven environment setup

## Features
- REST API endpoints for user operations
- Token-based authentication middleware
- Database integration for persistent storage
- Redis integration for performance optimization
- Modular and scalable project structure

## Tech Stack
- Python (Flask)
- Redis
- SQLAlchemy
- REST APIs

## How to Run
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set environment variables (create `.env`)
4. Run the application: `python main.py`

## Notes
This project demonstrates backend API design, middleware implementation, and integration with caching and database layers.
