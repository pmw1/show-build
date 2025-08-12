"""
AssetID Service - Central ID generation and management
Provides unique identifiers for all entities in the system.
Tracks complete history of ID generation and relationships.
"""
import uuid
import time
import hashlib
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime
import random
import string


class AssetIDService:
    """
    Central service for generating and managing AssetIDs.
    
    AssetID Format: {prefix}{timestamp}{random}
    Example: SEG1734567890ABC123
    
    Prefixes:
    - ORG: Organization
    - SHW: Show
    - SSN: Season
    - EPS: Episode
    - BLK: Block
    - SEG: Segment
    - SCR: Script
    - ELM: Element
    - CUE: Cue
    """
    
    # Entity type prefixes
    PREFIXES = {
        "organization": "ORG",
        "show": "SHW",
        "season": "SSN",
        "episode": "EPS",
        "block": "BLK",
        "segment": "SEG",
        "script": "SCR",
        "element": "ELM",
        "cue": "CUE",
        "generic": "AST"  # Generic asset
    }
    
    @classmethod
    def generate(cls, entity_type: str = "generic", metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a new unique AssetID (without database tracking).
        For tracked IDs, use request_asset_id() instead.
        
        Args:
            entity_type: Type of entity (segment, episode, etc.)
            metadata: Optional metadata to incorporate into ID generation
            
        Returns:
            Unique AssetID string
        """
        # Get prefix for entity type
        prefix = cls.PREFIXES.get(entity_type.lower(), cls.PREFIXES["generic"])
        
        # Timestamp component (milliseconds since epoch, base36 encoded for brevity)
        timestamp = int(time.time() * 1000)
        timestamp_str = cls._to_base36(timestamp)[-8:]  # Last 8 chars of base36 timestamp
        
        # Random component for uniqueness
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        # Combine components
        asset_id = f"{prefix}{timestamp_str}{random_str}"
        
        return asset_id.upper()
    
    @classmethod
    def request_asset_id(cls, db: Session, 
                        entity_type: str,
                        reason: str,
                        requested_by: Optional[str] = None,
                        linked_to: Optional[List[Dict[str, str]]] = None,
                        context: Optional[Dict] = None) -> str:
        """
        Request a new AssetID with full tracking and history.
        
        Args:
            db: Database session
            entity_type: Type of entity (segment, episode, etc.)
            reason: Reason for requesting ID (create, import, duplicate, etc.)
            requested_by: User or system requesting the ID
            linked_to: List of related AssetIDs [{"asset_id": "...", "link_type": "..."}]
            context: Additional context about the request
            
        Returns:
            New AssetID with full tracking in database
        """
        from models_assetid import AssetIDRegistry, AssetIDRelationship, AssetIDPendingMessage
        from models_v2 import AssetMessage
        
        # Generate the ID
        asset_id = cls.generate(entity_type)
        
        # Create registry entry
        registry_entry = AssetIDRegistry(
            asset_id=asset_id,
            entity_type=entity_type,
            request_reason=reason,
            requested_by=requested_by,
            request_context=context or {},
            initial_links=linked_to or []
        )
        
        db.add(registry_entry)
        
        # Create relationship entries if linked
        if linked_to:
            for link in linked_to:
                relationship = AssetIDRelationship(
                    source_asset_id=asset_id,
                    target_asset_id=link.get("asset_id"),
                    relationship_type=link.get("link_type", "related_to"),
                    created_by=requested_by,
                    context={"initial_link": True}
                )
                db.add(relationship)
        
        # Check for pending messages for this AssetID
        pending_messages = db.query(AssetIDPendingMessage).filter(
            AssetIDPendingMessage.pending_asset_id == asset_id,
            AssetIDPendingMessage.delivered == "false"
        ).all()
        
        # Deliver any pending messages
        for pending_msg in pending_messages:
            # Check if not expired
            if pending_msg.expires_at and pending_msg.expires_at < datetime.utcnow():
                continue
                
            # Create actual message
            message = AssetMessage(
                asset_id=asset_id,
                message_type=pending_msg.message_type,
                content=pending_msg.content,
                user_id=pending_msg.created_by
            )
            db.add(message)
            
            # Mark as delivered
            pending_msg.delivered = "true"
            pending_msg.delivered_at = datetime.utcnow()
        
        db.commit()
        
        return asset_id
    
    @classmethod
    def get_asset_history(cls, db: Session, asset_id: str) -> Dict[str, Any]:
        """
        Get complete history and metadata for an AssetID.
        
        Args:
            db: Database session
            asset_id: AssetID to look up
            
        Returns:
            Complete history including creation, relationships, and messages
        """
        from models_assetid import AssetIDRegistry, AssetIDRelationship
        from models_v2 import AssetMessage
        
        # Get registry entry
        registry = db.query(AssetIDRegistry).filter(
            AssetIDRegistry.asset_id == asset_id
        ).first()
        
        if not registry:
            return None
        
        # Get all relationships
        relationships_as_source = db.query(AssetIDRelationship).filter(
            AssetIDRelationship.source_asset_id == asset_id
        ).all()
        
        relationships_as_target = db.query(AssetIDRelationship).filter(
            AssetIDRelationship.target_asset_id == asset_id
        ).all()
        
        # Get messages
        messages = db.query(AssetMessage).filter(
            AssetMessage.asset_id == asset_id
        ).order_by(AssetMessage.created_at.desc()).all()
        
        return {
            "asset_id": asset_id,
            "entity_type": registry.entity_type,
            "created_at": registry.created_at,
            "requested_by": registry.requested_by,
            "request_reason": registry.request_reason,
            "request_context": registry.request_context,
            "initial_links": registry.initial_links,
            "status": registry.is_active,
            "relationships": {
                "as_source": [
                    {
                        "target": r.target_asset_id,
                        "type": r.relationship_type,
                        "created_at": r.created_at
                    } for r in relationships_as_source
                ],
                "as_target": [
                    {
                        "source": r.source_asset_id,
                        "type": r.relationship_type,
                        "created_at": r.created_at
                    } for r in relationships_as_target
                ]
            },
            "messages": [
                {
                    "type": m.message_type,
                    "content": m.content,
                    "created_at": m.created_at,
                    "user": m.user_id
                } for m in messages
            ],
            "metadata": registry.meta_data
        }
    
    @classmethod
    def generate_with_checksum(cls, entity_type: str = "generic") -> str:
        """
        Generate AssetID with checksum for verification.
        
        Returns:
            AssetID with 2-char checksum suffix
        """
        base_id = cls.generate(entity_type)
        checksum = cls._calculate_checksum(base_id)
        return f"{base_id}{checksum}"
    
    @classmethod
    def verify_checksum(cls, asset_id: str) -> bool:
        """
        Verify if an AssetID with checksum is valid.
        
        Args:
            asset_id: AssetID to verify
            
        Returns:
            True if checksum is valid
        """
        if len(asset_id) < 3:
            return False
        
        base_id = asset_id[:-2]
        provided_checksum = asset_id[-2:]
        calculated_checksum = cls._calculate_checksum(base_id)
        
        return provided_checksum == calculated_checksum
    
    @classmethod
    def extract_type(cls, asset_id: str) -> str:
        """
        Extract entity type from AssetID.
        
        Args:
            asset_id: AssetID to analyze
            
        Returns:
            Entity type string
        """
        # Reverse lookup prefix
        prefix = asset_id[:3] if len(asset_id) >= 3 else ""
        
        for entity_type, type_prefix in cls.PREFIXES.items():
            if type_prefix == prefix:
                return entity_type
        
        return "unknown"
    
    @classmethod
    def _to_base36(cls, num: int) -> str:
        """Convert number to base36 string."""
        alphabet = string.digits + string.ascii_lowercase
        base36 = ''
        
        while num:
            num, i = divmod(num, 36)
            base36 = alphabet[i] + base36
        
        return base36 or '0'
    
    @classmethod
    def _calculate_checksum(cls, asset_id: str) -> str:
        """Calculate 2-character checksum for AssetID."""
        hash_obj = hashlib.md5(asset_id.encode())
        hash_hex = hash_obj.hexdigest()
        
        # Take first 2 chars of hash and convert to uppercase alphanumeric
        checksum_num = int(hash_hex[:4], 16) % (36 * 36)
        
        chars = string.ascii_uppercase + string.digits
        first_char = chars[checksum_num // 36]
        second_char = chars[checksum_num % 36]
        
        return f"{first_char}{second_char}"
    
    @classmethod
    def link_assets(cls, db: Session, source_id: str, target_id: str, 
                    link_type: str = "related", metadata: Optional[Dict] = None):
        """
        Create a link between two AssetIDs.
        
        Args:
            db: Database session
            source_id: Source AssetID
            target_id: Target AssetID
            link_type: Type of relationship
            metadata: Additional metadata for the link
        """
        from models_v2 import AssetLink
        
        link = AssetLink(
            source_asset_id=source_id,
            target_asset_id=target_id,
            link_type=link_type,
            meta_data=metadata or {}
        )
        
        db.add(link)
        db.commit()
        
        return link
    
    @classmethod
    def add_message(cls, db: Session, asset_id: str, message: str, 
                    message_type: str = "note", user_id: Optional[str] = None):
        """
        Attach a message to an AssetID.
        If AssetID doesn't exist yet, stores as pending message.
        
        Args:
            db: Database session
            asset_id: AssetID to attach message to
            message: Message content
            message_type: Type of message (note, warning, production)
            user_id: Optional user identifier
        """
        from models_v2 import AssetMessage
        from models_assetid import AssetIDRegistry, AssetIDPendingMessage
        
        # Check if AssetID exists
        exists = db.query(AssetIDRegistry).filter(
            AssetIDRegistry.asset_id == asset_id
        ).first()
        
        if exists:
            # AssetID exists, create regular message
            msg = AssetMessage(
                asset_id=asset_id,
                message_type=message_type,
                content=message,
                user_id=user_id
            )
            db.add(msg)
        else:
            # AssetID doesn't exist yet, create pending message
            pending_msg = AssetIDPendingMessage(
                pending_asset_id=asset_id,
                message_type=message_type,
                content=message,
                created_by=user_id,
                context={"auto_pending": True}
            )
            db.add(pending_msg)
        
        db.commit()
        return True
    
    @classmethod
    def add_pending_message(cls, db: Session, future_asset_id: str, message: str,
                           message_type: str = "note", priority: int = 5,
                           expires_at: Optional[datetime] = None, 
                           user_id: Optional[str] = None,
                           context: Optional[Dict] = None):
        """
        Add a message for an AssetID that will be created in the future.
        
        Args:
            db: Database session
            future_asset_id: AssetID that will be created later
            message: Message content
            message_type: Type of message
            priority: Message priority (1-10)
            expires_at: Optional expiration date
            user_id: User creating the message
            context: Additional context
        """
        from models_assetid import AssetIDPendingMessage
        
        pending_msg = AssetIDPendingMessage(
            pending_asset_id=future_asset_id,
            message_type=message_type,
            content=message,
            priority=priority,
            expires_at=expires_at,
            created_by=user_id,
            context=context or {}
        )
        
        db.add(pending_msg)
        db.commit()
        
        return pending_msg
    
    @classmethod
    def get_pending_messages(cls, db: Session, asset_id: str):
        """
        Get all pending messages for a future AssetID.
        
        Args:
            db: Database session
            asset_id: AssetID to check for pending messages
            
        Returns:
            List of pending messages
        """
        from models_assetid import AssetIDPendingMessage
        
        return db.query(AssetIDPendingMessage).filter(
            AssetIDPendingMessage.pending_asset_id == asset_id,
            AssetIDPendingMessage.delivered == "false"
        ).order_by(AssetIDPendingMessage.priority.desc()).all()
    
    @classmethod
    def get_messages(cls, db: Session, asset_id: str):
        """
        Get all messages for an AssetID.
        
        Args:
            db: Database session
            asset_id: AssetID to get messages for
            
        Returns:
            List of messages
        """
        from models_v2 import AssetMessage
        
        return db.query(AssetMessage).filter(
            AssetMessage.asset_id == asset_id
        ).order_by(AssetMessage.created_at.desc()).all()
    
    @classmethod
    def get_links(cls, db: Session, asset_id: str, direction: str = "both"):
        """
        Get all links for an AssetID.
        
        Args:
            db: Database session
            asset_id: AssetID to get links for
            direction: "source", "target", or "both"
            
        Returns:
            List of asset links
        """
        from models_v2 import AssetLink
        from sqlalchemy import or_
        
        query = db.query(AssetLink)
        
        if direction == "source":
            query = query.filter(AssetLink.source_asset_id == asset_id)
        elif direction == "target":
            query = query.filter(AssetLink.target_asset_id == asset_id)
        else:  # both
            query = query.filter(
                or_(
                    AssetLink.source_asset_id == asset_id,
                    AssetLink.target_asset_id == asset_id
                )
            )
        
        return query.all()


# Convenience function for FastAPI dependency injection
def get_asset_id_service():
    """Get AssetID service instance for dependency injection."""
    return AssetIDService()