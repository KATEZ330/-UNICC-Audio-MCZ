# API Documentation

## iFlytek Audio Moderation API Integration

### Configuration

The application uses iFlytek's Audio Moderation API for content analysis. To use the API, you need to:

1. Register an account on iFlytek's platform
2. Create an application to get API credentials
3. Configure the credentials in `api_config.json`:

```json
{
    "app_id": "your_app_id",
    "api_key": "your_api_key",
    "api_secret": "your_api_secret"
}
```

### API Endpoints

- Base URL: `https://audit.iflyaisol.com/audit/v2/audio`
- Method: POST
- Content-Type: application/json

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| accessKeyId | string | Yes | API Key |
| appId | string | Yes | Application ID |
| utc | string | Yes | UTC timestamp |
| uuid | string | Yes | Unique request ID |
| signature | string | Yes | API signature |
| audio | string | Yes | Base64 encoded audio data |

### Response Format

```json
{
    "code": 0,
    "message": "success",
    "data": {
        "sensitive": ["detected_sensitive_content"],
        "porn": ["detected_pornographic_content"],
        "abuse": ["detected_abusive_content"]
    }
}
```

### Error Codes

| Code | Description |
|------|-------------|
| 0 | Success |
| 1001 | Invalid parameters |
| 1002 | Authentication failed |
| 1003 | API quota exceeded |
| 1004 | Server error |
| 1005 | Audio format not supported |

### Rate Limits

- Maximum file size: 10MB
- Maximum duration: 60 minutes
- Rate limit: 100 requests per minute

### Security

- All API requests are signed using HMAC-SHA256
- API credentials should be kept secure
- Do not share or commit API credentials to version control

### Best Practices

1. Always validate audio files before sending
2. Implement proper error handling
3. Cache API responses when possible
4. Monitor API usage and quotas
5. Keep API credentials secure 