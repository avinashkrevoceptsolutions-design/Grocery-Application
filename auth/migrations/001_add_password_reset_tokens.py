"""
Migration: Add password_reset_tokens table

This migration creates the password_reset_tokens table for managing
password reset functionality.
"""

def upgrade(db):
    """
    Apply migration.
    """
    # Create password_reset_tokens table
    db.execute("""
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id INTEGER PRIMARY KEY AUTO_INCREMENT,
            user_id INTEGER NOT NULL,
            token VARCHAR(255) NOT NULL UNIQUE,
            expires_at DATETIME NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
            is_used BOOLEAN DEFAULT FALSE NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            INDEX idx_user_id (user_id),
            INDEX idx_token (token),
            INDEX idx_expires_at (expires_at),
            INDEX idx_is_used (is_used),
            INDEX idx_user_id_expires_at (user_id, expires_at),
            INDEX idx_token_expires_at (token, expires_at)
        )
    """)
    
    db.commit()
    print("✓ Created password_reset_tokens table")


def downgrade(db):
    """
    Rollback migration.
    """
    db.execute("DROP TABLE IF EXISTS password_reset_tokens")
    db.commit()
    print("✓ Dropped password_reset_tokens table")