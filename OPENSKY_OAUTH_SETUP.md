# OpenSky Network OAuth 2.0 Setup

## Enhanced Authentication

The backend now supports **OAuth 2.0 client credentials flow** for OpenSky Network, which is the recommended authentication method.

## Benefits

1. **Automatic Token Refresh**: Tokens are automatically refreshed when they expire
2. **Higher Rate Limits**: 4,000 requests/day with authenticated access
3. **More Reliable**: Follows OpenSky's recommended authentication method
4. **Secure**: Uses standard OAuth 2.0 flow

## Setup Options

### Option 1: OAuth 2.0 (Recommended)

Add to `backend/.env`:

```env
OPENSKY_CLIENT_ID=your-client-id
OPENSKY_CLIENT_SECRET=your-client-secret
```

### Option 2: Pre-obtained Bearer Token

If you already have a Bearer token:

```env
OPENSKY_ACCESS_TOKEN=your-bearer-token-here
```

**Note**: Bearer tokens expire, so OAuth is preferred.

### Option 3: Basic Auth (Legacy)

```env
OPENSKY_USERNAME=your-username
OPENSKY_PASSWORD=your-password
```

## Priority Order

The backend will use authentication in this order:

1. **OAuth 2.0** (if `OPENSKY_CLIENT_ID` and `OPENSKY_CLIENT_SECRET` are set)
2. **Bearer Token** (if `OPENSKY_ACCESS_TOKEN` is set)
3. **Basic Auth** (if `OPENSKY_USERNAME` and `OPENSKY_PASSWORD` are set)
4. **Anonymous** (no authentication, limited rate)

## Getting OAuth Credentials

1. Go to [OpenSky Network](https://openskynetwork.org/)
2. Register/login to your account
3. Navigate to API settings
4. Create an API client to get `client_id` and `client_secret`

## How It Works

The code automatically:
1. Exchanges `client_id` and `client_secret` for an access token
2. Uses the token in `Authorization: Bearer` header
3. Refreshes the token automatically when it expires (typically 30 minutes)
4. Falls back gracefully if authentication fails

## Example Usage

Once configured, the backend will automatically authenticate on startup:

```python
# In backend/services/opensky_client.py
client = OpenSkyClient()  # Automatically authenticates if credentials are set

# All API calls use the authenticated session
states = await client.get_current_states()
```

## Verification

Check your backend logs on startup. You should see:

```
Using OAuth 2.0 authentication for OpenSky Network
✓ OpenSky OAuth authentication successful (token expires in 1800s)
```

Or:

```
Using Bearer token authentication for OpenSky Network
```

## Troubleshooting

### "OAuth authentication failed"
- Check that `OPENSKY_CLIENT_ID` and `OPENSKY_CLIENT_SECRET` are correct
- Verify credentials in your OpenSky Network account
- Check that credentials don't have extra spaces

### "Token expired"
- If using Bearer token, it may have expired
- Switch to OAuth 2.0 for automatic token refresh
- Get a new token from OpenSky Network

### "Rate limit exceeded"
- Verify authentication is working (check logs)
- OAuth/Bearer token should give you 4,000 requests/day
- Anonymous access is limited to 100 requests/day

## Code Reference

The implementation is based on the OpenSky Network Python tracker script, which demonstrates:
- Proper OAuth 2.0 client credentials flow
- Token refresh management
- Error handling and fallbacks
- Extended state vector support (aircraft category)

