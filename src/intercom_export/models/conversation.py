"""
Data models for Intercom conversations and related entities.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any

@dataclass
class Author:
    """Represents a message author (user or admin)."""
    id: str
    name: str
    type: str  # user, admin, bot
    email: Optional[str] = None

@dataclass
class Message:
    """Represents a single message in a conversation."""
    id: str
    body: str
    author: Author
    created_at: datetime
    type: str  # comment, note, assignment
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'Message':
        """Create a Message instance from API response data."""
        return cls(
            id=data['id'],
            body=data.get('body', ''),
            author=Author(
                id=data['author']['id'],
                name=data['author']['name'],
                type=data['author']['type'],
                email=data['author'].get('email')
            ),
            created_at=datetime.utcfromtimestamp(data['created_at']) + timedelta(hours=2),
            type=data['part_type'],
            metadata={
                k: v for k, v in data.items()
                if k not in ['id', 'body', 'author', 'created_at', 'part_type']
            }
        )

@dataclass
class Conversation:
    """Represents a complete Intercom conversation."""
    id: str
    created_at: datetime
    updated_at: datetime
    title: Optional[str] = None
    state: str = 'open'
    messages: List[Message] = field(default_factory=list)
    custom_attributes: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    source: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'Conversation':
        """Create a Conversation instance from API response data."""
        messages = []
        
        # Add initial message if present.
        if 'conversation_message' in data:
            messages.append(Message.from_api_data({
                **data['conversation_message'],
                'part_type': 'comment'
            }))
        
        # Add subsequent messages.
        if 'conversation_parts' in data:
            parts = data['conversation_parts'].get('conversation_parts', [])
            for part in parts:
                try:
                    if isinstance(part, dict) and part.get('body'):
                        messages.append(Message.from_api_data(part))
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning(f"Skipping invalid conversation part: {e}")
        
        messages.sort(key=lambda m: m.created_at)
        
        return cls(
            id=data['id'],
            created_at=datetime.utcfromtimestamp(data['created_at']) + timedelta(hours=2),
            updated_at=datetime.utcfromtimestamp(data['updated_at']) + timedelta(hours=2),
            title=data.get('title'),
            state=data.get('state', 'open'),
            messages=messages,
            custom_attributes=data.get('custom_attributes', {}),
            tags=[
                tag.get('name', tag) if isinstance(tag, dict) else tag 
                for tag in (
                    data.get('tags') if isinstance(data.get('tags'), list)
                    else data.get('tags', {}).get('tags', [])
                )
            ],
            source=data.get('source', {}),
            metadata={
                k: v for k, v in data.items()
                if k not in [
                    'id', 'created_at', 'updated_at', 'title',
                    'state', 'conversation_parts', 'custom_attributes',
                    'tags', 'source', 'conversation_message'
                ]
            }
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation to a dictionary format."""
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'title': self.title,
            'state': self.state,
            'messages': [
                {
                    'id': msg.id,
                    'body': msg.body,
                    'author': {
                        'id': msg.author.id,
                        'name': msg.author.name,
                        'type': msg.author.type,
                        'email': msg.author.email
                    },
                    'created_at': msg.created_at.isoformat(),
                    'type': msg.type,
                    'metadata': msg.metadata
                }
                for msg in self.messages
            ],
            'custom_attributes': self.custom_attributes,
            'tags': self.tags,
            'source': self.source,
            'metadata': self.metadata
        }
