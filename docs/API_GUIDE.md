# API Usage Guide

## Base URL
`http://localhost:8000/api/v1`

## Authentication
Include JWT token in Authorization header:
`Authorization: Bearer <token>`

## Key Endpoints

### Get Forms
```
GET /forms/
```
Returns all available Kobo forms

### Get Specific Form  
```
GET /forms/{form_id}
```
Returns form structure with questions

### Submit Data
```
POST /submissions/
```
Submit wildlife incident data

### Health Checks
```
GET /health/
GET /health/database
GET /health/kobo
```

## Response Format

All responses follow this structure:
```json
{
    "data": {...},
    "message": "Success",
    "status_code": 200
}
```

Errors:
```json
{
    "error": {
        "message": "Error description",
        "type": "ErrorType",
        "status_code": 400
    }
}
```
