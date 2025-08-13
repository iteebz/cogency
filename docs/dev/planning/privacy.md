# Privacy & Encryption Design

## Current State

- Memory stored in plaintext (SQLite/Supabase)
- User conversations persist unencrypted
- No privacy controls for memory data
- Developers need memory access for debugging

## Privacy Concerns

1. **Sensitive Data in Memory** - Personal info, work context, private conversations
2. **Cross-Session Persistence** - Data survives beyond single interactions
3. **Third-Party Storage** - Supabase deployments expose data to external service
4. **Developer Access** - Production debugging requires memory inspection
5. **Compliance** - GDPR, HIPAA, SOC2 requirements for encrypted storage

## Proposed Solutions

### 1. Local Memory Encryption

#### User-Controlled Encryption Keys
```python
# User provides encryption key
agent = Agent("assistant", 
    memory=True,
    encryption_key="user-provided-key-32-chars"
)

# Or auto-generate and return to user
agent, encryption_key = Agent.create_with_encryption("assistant")
# User must store encryption_key safely
```

#### Key Derivation from User Context
```python
# Derive key from user ID + master secret
def derive_user_key(user_id: str, master_secret: str) -> str:
    """Derive deterministic encryption key for user."""
    import hashlib
    import hmac
    
    key_material = f"{user_id}:{master_secret}"
    return hmac.new(
        master_secret.encode(),
        key_material.encode(),
        hashlib.sha256
    ).hexdigest()[:32]

agent = Agent("assistant", 
    memory=True,
    master_secret=os.getenv("MEMORY_MASTER_SECRET")
)
```

### 2. Selective Encryption Strategy

#### Encrypt Memory, Preserve Embeddings
```python
# Memory content encrypted
encrypted_memory = {
    "user_id": "alice",
    "content": encrypt("I work at Google and prefer Python"),
    "embedding": [0.1, 0.2, ...],  # Unencrypted for similarity search
    "metadata": {
        "timestamp": "2024-01-01",
        "session_id": encrypt("session_123")
    }
}
```

#### Searchable Encryption for Embeddings
```python
# Generate embeddings from unencrypted text, then encrypt the text
async def store_memory(self, user_id: str, content: str):
    # Generate embedding first
    embedding = await self.embed.embed([content])
    
    # Encrypt the content
    encrypted_content = encrypt(content, self.get_user_key(user_id))
    
    # Store both
    await self.storage.store({
        "user_id": user_id,
        "content": encrypted_content,
        "embedding": embedding[0],
        "encrypted": True
    })
```

### 3. Development vs Production Keys

#### Environment-Based Key Management
```python
class EncryptionConfig:
    def __init__(self, environment: str = "production"):
        if environment == "development":
            # Fixed dev key for easier debugging
            self.master_key = "dev-master-key-fixed-32-chars"
            self.allow_plaintext_export = True
        else:
            # Production requires real secret management
            self.master_key = os.getenv("MEMORY_MASTER_SECRET")
            self.allow_plaintext_export = False
            
            if not self.master_key:
                raise ValueError("MEMORY_MASTER_SECRET required in production")
```

#### Developer Memory Access
```python
# Development: Export plaintext memory for debugging
agent.export_memory(user_id="alice", format="plaintext")  # Dev only

# Production: Export encrypted memory with dev key
agent.export_memory(
    user_id="alice", 
    format="encrypted",
    decrypt_with="dev-key-for-debugging"
)
```

### 4. Implementation Architecture

#### Encryption Layer
```python
# New module: src/cogency/privacy/encryption.py
class MemoryEncryption:
    def __init__(self, key: str):
        from cryptography.fernet import Fernet
        import base64
        import hashlib
        
        # Derive Fernet key from user key
        key_bytes = hashlib.sha256(key.encode()).digest()
        fernet_key = base64.urlsafe_b64encode(key_bytes)
        self.cipher = Fernet(fernet_key)
    
    def encrypt(self, text: str) -> str:
        """Encrypt text to base64 string."""
        return self.cipher.encrypt(text.encode()).decode()
    
    def decrypt(self, encrypted: str) -> str:
        """Decrypt base64 string to text."""
        return self.cipher.decrypt(encrypted.encode()).decode()
```

#### Storage Layer Integration
```python
# Modify: src/cogency/memory/memory.py
class Memory:
    def __init__(self, encryption_key: str = None):
        self.encryption = MemoryEncryption(encryption_key) if encryption_key else None
    
    async def remember(self, user_id: str, content: str, human: bool = True):
        # Generate embedding from plaintext
        embedding = await self.embed.embed([content])
        
        # Encrypt content if encryption enabled
        stored_content = (
            self.encryption.encrypt(content) 
            if self.encryption 
            else content
        )
        
        await self.storage.store({
            "user_id": user_id,
            "content": stored_content,
            "embedding": embedding[0],
            "human": human,
            "encrypted": bool(self.encryption),
            "timestamp": datetime.utcnow()
        })
    
    async def recall(self, user_id: str, query: str) -> str:
        # Search using embedding (always unencrypted)
        results = await self.storage.search_similar(user_id, query)
        
        # Decrypt results if needed
        memories = []
        for result in results:
            content = (
                self.encryption.decrypt(result["content"])
                if result.get("encrypted") and self.encryption
                else result["content"]
            )
            memories.append(content)
        
        return "\n".join(memories)
```

### 5. User API Design

#### Simple Encryption
```python
# Auto-managed encryption (easiest)
agent = Agent("assistant", memory=True, encrypt_memory=True)
encryption_key = agent.get_encryption_key()  # User must store this

# User-provided key (most secure)
agent = Agent("assistant", 
    memory=True,
    encryption_key="user-secret-key-32-characters"
)
```

#### Memory Export/Import
```python
# Export encrypted memory for backup
backup = agent.export_memory(user_id="alice", include_key=False)

# Import with user's key
agent.import_memory(backup, encryption_key="user-key")

# Development: plaintext export
agent.export_memory(user_id="alice", format="plaintext", dev_mode=True)
```

### 6. Migration Strategy

#### Backward Compatibility
```python
# Existing unencrypted memory continues to work
agent = Agent("assistant", memory=True)  # No encryption

# New encrypted memory opt-in
agent = Agent("assistant", memory=True, encrypt_memory=True)

# Mixed mode: encrypt new, preserve old
agent = Agent("assistant", memory=True, 
    encrypt_memory=True,
    migrate_existing=False  # Don't re-encrypt old memories
)
```

#### Migration Tool
```python
# Encrypt existing plaintext memories
agent.migrate_to_encrypted(
    user_id="alice",
    encryption_key="new-key",
    backup_plaintext=True  # Safety net
)
```

### 7. Compliance Features

#### Data Retention Controls
```python
agent = Agent("assistant", 
    memory=True,
    encrypt_memory=True,
    retention_days=90,  # Auto-delete old memories
    gdpr_compliant=True  # Enable right-to-deletion
)

# GDPR: Delete all user data
agent.delete_user_data(user_id="alice", permanent=True)
```

#### Audit Logging
```python
# Track memory operations for compliance
audit_log = agent.get_memory_audit(user_id="alice")
# [
#   {"action": "store", "timestamp": "...", "encrypted": true},
#   {"action": "recall", "timestamp": "...", "query_hash": "..."}
# ]
```

## Implementation Priority

1. **Basic encryption/decryption** - Core privacy protection
2. **Development key management** - Enable debugging
3. **User API design** - Simple encryption opt-in
4. **Migration strategy** - Backward compatibility
5. **Export/import tools** - Data portability  
6. **Compliance features** - Production requirements

## Files to Create/Modify

- New: `src/cogency/privacy/` - Encryption module
- New: `src/cogency/privacy/encryption.py` - Core encryption
- New: `src/cogency/privacy/keys.py` - Key management
- Modify: `src/cogency/memory/memory.py` - Encryption integration
- Modify: `src/cogency/storage/sqlite/base.py` - Storage layer
- Modify: `src/cogency/storage/supabase.py` - Remote storage
- New: `docs/privacy.md` - User documentation

## Dependencies

Add to `pyproject.toml`:
```toml
cryptography = ">=42.0.0"  # For Fernet encryption
```

## Security Considerations

1. **Key Storage** - Users responsible for key security
2. **Key Rotation** - Support for changing encryption keys
3. **Memory Leaks** - Ensure encryption keys don't persist in memory
4. **Development Safety** - Dev keys clearly marked, never in production
5. **Embedding Privacy** - Embeddings remain unencrypted for search
6. **Transport Security** - HTTPS for Supabase, encrypted at rest