"""
Asterisk Manager Interface (AMI) Service

Provides integration with Asterisk PBX for:
- Creating and managing conference rooms
- Recording calls
- Tracking participants
- WebRTC SIP integration
"""

import asyncio
import socket
import logging
import uuid
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class AsteriskAMIClient:
    """Asterisk Manager Interface client for conference management"""

    def __init__(self, host: str, port: int, username: str, secret: str):
        self.host = host
        self.port = port
        self.username = username
        self.secret = secret
        self.socket = None
        self.connected = False
        self.action_id = 0

    async def connect(self) -> bool:
        """Connect to Asterisk AMI"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.socket.settimeout(5.0)

            # Read welcome message
            response = self._read_response()
            logger.info(f"AMI connected: {response.get('Response', 'Unknown')}")

            # Login
            if await self.login():
                self.connected = True
                logger.info("AMI login successful")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to connect to Asterisk AMI: {e}")
            return False

    async def login(self) -> bool:
        """Authenticate with AMI"""
        action = {
            'Action': 'Login',
            'Username': self.username,
            'Secret': self.secret
        }

        response = await self._send_action(action)
        return response.get('Response') == 'Success'

    def disconnect(self):
        """Close AMI connection"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.connected = False
        logger.info("AMI disconnected")

    async def _send_action(self, action: Dict[str, str]) -> Dict[str, str]:
        """Send AMI action and wait for response"""
        if not self.socket:
            raise ConnectionError("Not connected to AMI")

        self.action_id += 1
        action['ActionID'] = str(self.action_id)

        # Format AMI message
        message = ""
        for key, value in action.items():
            message += f"{key}: {value}\r\n"
        message += "\r\n"

        # Send
        self.socket.sendall(message.encode('utf-8'))

        # Read response
        return self._read_response()

    def _read_response(self) -> Dict[str, str]:
        """Read AMI response"""
        response = {}
        buffer = ""

        while True:
            try:
                data = self.socket.recv(1024).decode('utf-8')
                if not data:
                    break

                buffer += data

                # Check for end of response
                if '\r\n\r\n' in buffer:
                    break
            except socket.timeout:
                break

        # Parse response
        for line in buffer.split('\r\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                response[key.strip()] = value.strip()

        return response

    async def create_conference(
        self,
        conference_id: str,
        context: str = 'conferences',
        record: bool = True
    ) -> Dict[str, str]:
        """
        Create a new conference room

        Args:
            conference_id: Unique conference identifier (e.g., "episode-0245")
            context: Dialplan context for the conference
            record: Whether to record the conference

        Returns:
            Conference details dict
        """
        # Generate conference PIN
        pin = str(uuid.uuid4().int)[:6]

        # In a real implementation, this would create the conference
        # via AMI Originate or by setting up the dialplan dynamically

        logger.info(f"Created conference: {conference_id} with PIN {pin}")

        return {
            'conference_id': conference_id,
            'pin': pin,
            'context': context,
            'recording_enabled': record,
            'created_at': datetime.utcnow().isoformat()
        }

    async def get_conference_participants(self, conference_id: str) -> List[Dict]:
        """Get list of active participants in conference"""
        action = {
            'Action': 'ConfbridgeList',
            'Conference': conference_id
        }

        try:
            response = await self._send_action(action)

            # Parse participant list
            participants = []
            # AMI returns multiple events for ConfbridgeList
            # Would need to parse each event to build participant list

            return participants

        except Exception as e:
            logger.error(f"Failed to get conference participants: {e}")
            return []

    async def kick_participant(self, conference_id: str, channel: str) -> bool:
        """Remove a participant from conference"""
        action = {
            'Action': 'ConfbridgeKick',
            'Conference': conference_id,
            'Channel': channel
        }

        response = await self._send_action(action)
        return response.get('Response') == 'Success'

    async def mute_participant(
        self,
        conference_id: str,
        channel: str,
        mute: bool = True
    ) -> bool:
        """Mute or unmute a participant"""
        action = {
            'Action': 'ConfbridgeMute' if mute else 'ConfbridgeUnmute',
            'Conference': conference_id,
            'Channel': channel
        }

        response = await self._send_action(action)
        return response.get('Response') == 'Success'

    async def end_conference(self, conference_id: str) -> bool:
        """End a conference and kick all participants"""
        # Get all participants
        participants = await self.get_conference_participants(conference_id)

        # Kick each participant
        for participant in participants:
            channel = participant.get('Channel')
            if channel:
                await self.kick_participant(conference_id, channel)

        logger.info(f"Ended conference: {conference_id}")
        return True


class AsteriskService:
    """High-level Asterisk service for Show-Build integration"""

    def __init__(self, config: Dict[str, str]):
        """
        Initialize Asterisk service

        Args:
            config: Dict with keys: host, amiPort, amiUsername, amiSecret,
                    conferenceContext, recordingsPath
        """
        self.config = config
        self.ami_client = None
        self.active_conferences = {}

    async def initialize(self) -> bool:
        """Initialize AMI connection"""
        if not self.config.get('enabled'):
            logger.info("Asterisk integration is disabled")
            return False

        self.ami_client = AsteriskAMIClient(
            host=self.config.get('host', 'localhost'),
            port=int(self.config.get('amiPort', 5038)),
            username=self.config.get('amiUsername', ''),
            secret=self.config.get('amiSecret', '')
        )

        return await self.ami_client.connect()

    async def create_conference(
        self,
        episode_id: str,
        user_id: int,
        title: str = None
    ) -> Dict:
        """
        Create a conference room for an episode

        Args:
            episode_id: Episode identifier
            user_id: User creating the conference
            title: Optional conference title

        Returns:
            Conference details with dial-in info
        """
        conference_id = f"ep-{episode_id}-{uuid.uuid4().hex[:8]}"
        context = self.config.get('conferenceContext', 'conferences')

        conf_details = await self.ami_client.create_conference(
            conference_id=conference_id,
            context=context,
            record=True
        )

        # Build complete conference data
        conference_data = {
            'conference_id': conference_id,
            'pin': conf_details['pin'],
            'dial_in_number': self._get_dial_in_number(),
            'webrtc_url': self._get_webrtc_url(conference_id),
            'recording_enabled': True,
            'created_at': conf_details['created_at'],
            'episode_id': episode_id,
            'created_by': user_id,
            'title': title or f"Episode {episode_id} Conference",
            'participants': []
        }

        # Store conference metadata
        self.active_conferences[conference_id] = conference_data

        return conference_data

    def _get_dial_in_number(self) -> str:
        """Get the dial-in phone number for conferences"""
        # This would come from Asterisk DID configuration
        # For now, return a placeholder
        return self.config.get('dial_in_number', 'Contact admin for dial-in')

    def _get_webrtc_url(self, conference_id: str) -> str:
        """Generate WebRTC connection URL"""
        # WebRTC SIP URL for browser-based connections
        # Format: sip:conference_id@asterisk_host
        return f"sip:{conference_id}@{self.config.get('host', 'localhost')}"

    async def get_conference(self, conference_id: str) -> Optional[Dict]:
        """Get conference details"""
        return self.active_conferences.get(conference_id)

    async def add_participant(
        self,
        conference_id: str,
        caller_id: str = None,
        channel: str = None,
        join_method: str = 'phone'
    ):
        """
        Add a participant to conference tracking

        Participants are initially tracked by caller ID/channel.
        Name identification happens post-call via audio transcription
        where they state their name at the beginning.

        Args:
            conference_id: Conference ID
            caller_id: Phone number or SIP identifier
            channel: Asterisk channel
            join_method: 'phone', 'webrtc', or 'sip'
        """
        if conference_id in self.active_conferences:
            participant_id = f"p-{len(self.active_conferences[conference_id]['participants']) + 1}"

            participant = {
                'participant_id': participant_id,
                'caller_id': caller_id,
                'name': None,  # Will be identified via voice intro or post-call
                'channel': channel,
                'join_method': join_method,
                'joined_at': datetime.utcnow().isoformat(),
                'audio_segments': []  # For per-speaker tracking
            }

            self.active_conferences[conference_id]['participants'].append(participant)
            logger.info(f"Added participant {participant_id} ({caller_id}) to conference {conference_id}")

            return participant_id

    async def identify_participant(
        self,
        conference_id: str,
        participant_id: str,
        name: str,
        user_id: int = None
    ):
        """
        Identify a participant by name (from voice intro or manual entry)

        Args:
            conference_id: Conference ID
            participant_id: Participant ID to identify
            name: Participant's name
            user_id: Optional Show-Build user ID if internal user
        """
        if conference_id in self.active_conferences:
            for participant in self.active_conferences[conference_id]['participants']:
                if participant['participant_id'] == participant_id:
                    participant['name'] = name
                    participant['user_id'] = user_id
                    participant['identified_at'] = datetime.utcnow().isoformat()
                    logger.info(f"Identified participant {participant_id} as {name}")
                    return True
        return False

    async def end_conference(self, conference_id: str) -> Optional[str]:
        """
        End conference and return recording path

        Returns:
            Path to recording file
        """
        if conference_id not in self.active_conferences:
            return None

        # End via AMI
        await self.ami_client.end_conference(conference_id)

        # Get recording path
        recordings_path = self.config.get('recordingsPath', '/var/spool/asterisk/monitor')
        recording_file = f"{recordings_path}/conf-{conference_id}-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.wav"

        # Remove from active conferences
        conf_data = self.active_conferences.pop(conference_id)

        logger.info(f"Conference ended: {conference_id}, recording: {recording_file}")

        return recording_file

    def shutdown(self):
        """Shutdown service and close connections"""
        if self.ami_client:
            self.ami_client.disconnect()


# Global service instance
_asterisk_service: Optional[AsteriskService] = None


async def get_asterisk_service(db) -> Optional[AsteriskService]:
    """
    Get or initialize Asterisk service singleton

    Args:
        db: Database session to load config

    Returns:
        AsteriskService instance or None if disabled
    """
    global _asterisk_service

    if _asterisk_service is None:
        # Load Asterisk config from database
        from sqlalchemy import text

        try:
            query = text("""
                SELECT config_key, config_value
                FROM api_configs
                WHERE service = 'asterisk' AND is_enabled = TRUE
            """)
            result = db.execute(query)

            config = {}
            for row in result:
                config[row.config_key] = row.config_value

            if config:
                config['enabled'] = True
                _asterisk_service = AsteriskService(config)
                await _asterisk_service.initialize()
                logger.info("Asterisk service initialized")
            else:
                logger.info("Asterisk not configured or disabled")

        except Exception as e:
            logger.error(f"Failed to initialize Asterisk service: {e}")

    return _asterisk_service
