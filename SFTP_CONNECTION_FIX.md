# SFTP Connection "Transport Shut Down" Fix

## Problem

Users were experiencing errors:
```
Upstream error (Upstream: http://localhost:8002/files) - 
{"detail":"Failed to list files: Authentication failed: transport shut down or saw EOF"}
```

This error occurred when:
- SFTP connections were timing out
- Connections were being closed prematurely
- Network interruptions caused connection failures
- Users had to "log back in" after each error

## Root Cause

1. **No Connection Health Checking**: The code didn't verify if connections were still active before use
2. **No Automatic Reconnection**: Failed connections weren't automatically retried
3. **No Keepalive**: Connections could timeout due to inactivity
4. **Poor Error Handling**: Connection errors weren't handled gracefully

## Solution

### 1. Connection Health Checking

Added `_ensure_connected()` method that:
- Checks if transport is active
- Verifies connection with lightweight operation (`getcwd()`)
- Automatically reconnects if connection is dead

### 2. Automatic Retry Logic

Updated `list_files()` to:
- Check connection health before use
- Automatically reconnect on connection errors
- Retry the operation once after reconnection
- Handle specific connection errors (`SSHException`, `EOFError`, `OSError`)

### 3. Keepalive Configuration

Added keepalive to prevent connection timeouts:
```python
transport.set_keepalive(30)  # Send keepalive every 30 seconds
```

### 4. Improved Connection Management

- Better cleanup in `disconnect()` (handles errors gracefully)
- Disable SSH agent and key lookup (prevents authentication issues)
- Clean up existing connections before reconnecting

## Code Changes

**File**: `src/obs_sftp_file_processor/sftp_service.py`

### New Method: `_ensure_connected()`
- Checks connection health before operations
- Automatically reconnects if needed
- Handles edge cases gracefully

### Updated Method: `list_files()`
- Calls `_ensure_connected()` before use
- Catches connection errors and retries once
- Better error logging

### Updated Method: `connect()`
- Sets keepalive to prevent timeouts
- Disables SSH agent/key lookup
- Better cleanup before connecting

### Updated Method: `disconnect()`
- Handles errors gracefully
- Prevents exceptions during cleanup

## Benefits

1. **Automatic Recovery**: Connections automatically reconnect on failure
2. **Better Reliability**: Health checks prevent using dead connections
3. **Reduced Errors**: Keepalive prevents timeout-related failures
4. **Better UX**: Users don't need to "log back in" manually

## Testing

Test scenarios:
1. **Normal Operation**: Should work as before
2. **Connection Timeout**: Should automatically reconnect
3. **Network Interruption**: Should retry and recover
4. **Server Restart**: Should reconnect on next request

## Additional Recommendations

### 1. Monitor Connection Health

Add logging to track reconnection frequency:
```python
logger.info(f"SFTP reconnected (count: {reconnect_count})")
```

### 2. Connection Pooling (Future Enhancement)

For high-traffic scenarios, consider connection pooling:
- Maintain a pool of active connections
- Reuse connections across requests
- Rotate connections to prevent timeouts

### 3. Configuration Options

Add configurable options:
- `keepalive_interval`: Adjust keepalive frequency
- `max_reconnect_attempts`: Limit retry attempts
- `connection_timeout`: Adjust timeout values

### 4. Health Endpoint

Add SFTP health check endpoint:
```python
@app.get("/health/sftp")
async def sftp_health():
    try:
        with sftp_service:
            sftp_service.list_files(".")
        return {"status": "healthy"}
    except:
        return {"status": "unhealthy"}
```

## Related Issues

- Connection timeouts
- Network interruptions
- Server-side connection limits
- Authentication failures

## Notes

- The fix maintains backward compatibility
- No API changes required
- Works transparently for existing code
- Improves reliability without changing behavior

