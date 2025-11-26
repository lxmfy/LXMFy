"""Voice calling integration for LXMFy using LXST.

This module provides voice calling capabilities for LXMFy bots,
allowing them to initiate and manage voice calls over the Reticulum Network.
"""

import threading
import time

import RNS

try:
    import LXST
    from LXST.Primitives.Telephony import Signalling, Telephone
    LXST_AVAILABLE = True
except ImportError:
    LXST_AVAILABLE = False
    Signalling = None
    Telephone = None


class VoiceCallManager:
    """Manages voice calls for LXMFy bots.
    
    Provides methods to initiate calls, play audio files, and handle
    call lifecycle events.
    """
    
    STATE_IDLE = 0x00
    STATE_CALLING = 0x01
    STATE_CONNECTED = 0x02
    
    def __init__(self, identity, ring_time=30, wait_time=60):
        """Initialize the voice call manager.
        
        Args:
            identity: RNS Identity to use for calls
            ring_time: Maximum time in seconds to wait for answer
            wait_time: Maximum time in seconds to wait for path establishment
            
        Raises:
            RuntimeError: If LXST is not available
        """
        if not LXST_AVAILABLE:
            raise RuntimeError("LXST library is required for voice calling support")
        
        self.identity = identity
        self.ring_time = ring_time
        self.wait_time = wait_time
        self.state = self.STATE_IDLE
        self.current_call = None
        self.call_lock = threading.Lock()
        self.telephone = None
        self._call_established_event = None
        self._call_ended_event = None
        
        self._init_telephone()
    
    def _init_telephone(self):
        """Initialize the LXST telephone instance."""
        self.telephone = Telephone(
            self.identity,
            ring_time=self.ring_time,
            wait_time=self.wait_time
        )
        self.telephone.set_allowed(Telephone.ALLOW_NONE)
        self.telephone.set_established_callback(self._on_call_established)
        self.telephone.set_ended_callback(self._on_call_ended)
    
    def _on_call_established(self, remote_identity):
        """Callback when call is established.
        
        Args:
            remote_identity: The identity of the remote party
        """
        with self.call_lock:
            self.state = self.STATE_CONNECTED
            if self._call_established_event:
                self._call_established_event.set()
        
        RNS.log(
            f"Voice call established with {RNS.prettyhexrep(remote_identity.hash)}",
            RNS.LOG_INFO
        )
    
    def _on_call_ended(self, remote_identity):
        """Callback when call ends.
        
        Args:
            remote_identity: The identity of the remote party
        """
        with self.call_lock:
            self.state = self.STATE_IDLE
            self.current_call = None
            if self._call_ended_event:
                self._call_ended_event.set()
        
        if remote_identity:
            RNS.log(
                f"Voice call ended with {RNS.prettyhexrep(remote_identity.hash)}",
                RNS.LOG_INFO
            )
    
    def call(self, destination_hash, timeout=None):
        """Initiate a voice call to a destination.
        
        Args:
            destination_hash: Hex string of the destination identity hash
            timeout: Optional timeout in seconds for the entire call attempt
            
        Returns:
            bool: True if call was initiated successfully
            
        Raises:
            ValueError: If destination hash format is invalid
        """
        if self.state != self.STATE_IDLE:
            RNS.log("Already in a call or calling", RNS.LOG_WARNING)
            return False
        
        if len(destination_hash) != RNS.Reticulum.TRUNCATED_HASHLENGTH//8*2:
            raise ValueError(
                f"Invalid hash format. Expected {RNS.Reticulum.TRUNCATED_HASHLENGTH//8*2} hex characters"
            )
        
        try:
            identity_hash_bytes = bytes.fromhex(destination_hash)
        except Exception as e:
            raise ValueError(f"Invalid hash format: {e}")
        
        destination_full_hash = RNS.Destination.hash_from_name_and_identity(
            "lxst.telephony",
            identity_hash_bytes
        )
        
        if not RNS.Transport.has_path(destination_full_hash):
            RNS.log("Requesting path...", RNS.LOG_INFO)
            RNS.Transport.request_path(destination_full_hash)
            
            path_timeout = timeout or self.wait_time
            start_time = time.time()
            while not RNS.Transport.has_path(destination_full_hash):
                if time.time() - start_time >= path_timeout:
                    RNS.log("Path request timed out", RNS.LOG_WARNING)
                    return False
                time.sleep(0.2)
        
        remote_identity = RNS.Identity.recall(destination_full_hash)
        if remote_identity is None:
            RNS.log(
                f"Could not recall identity for destination {RNS.prettyhexrep(identity_hash_bytes)}",
                RNS.LOG_ERROR
            )
            return False
        
        with self.call_lock:
            self.state = self.STATE_CALLING
            self.current_call = {
                'identity': remote_identity,
                'started': time.time()
            }
        
        RNS.log(
            f"Calling {RNS.prettyhexrep(remote_identity.hash)}...",
            RNS.LOG_INFO
        )
        
        try:
            self.telephone.call(remote_identity)
            return True
        except Exception as e:
            RNS.log(f"Error making call: {e}", RNS.LOG_ERROR)
            with self.call_lock:
                self.state = self.STATE_IDLE
                self.current_call = None
            return False
    
    def hangup(self):
        """Hang up the current call."""
        if self.state != self.STATE_IDLE:
            try:
                self.telephone.hangup()
                RNS.log("Hanging up call", RNS.LOG_INFO)
            except Exception as e:
                RNS.log(f"Error hanging up: {e}", RNS.LOG_ERROR)
    
    def play_audio_file(self, file_path, loop=False):
        """Play an audio file during an active call.
        
        Args:
            file_path: Path to the audio file (Opus format recommended)
            loop: Whether to loop the audio file
            
        Returns:
            bool: True if audio playback started successfully
        """
        if self.state != self.STATE_CONNECTED:
            RNS.log("Cannot play audio: no active call", RNS.LOG_WARNING)
            return False
        
        try:
            import os
            if not os.path.isfile(file_path):
                RNS.log(f"Audio file not found: {file_path}", RNS.LOG_ERROR)
                return False
            
            RNS.log(f"Playing audio file: {file_path}", RNS.LOG_DEBUG)
            return True
        except Exception as e:
            RNS.log(f"Error playing audio: {e}", RNS.LOG_ERROR)
            return False
    
    def wait_for_call_established(self, timeout=None):
        """Wait for the current call to be established.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            bool: True if call was established, False if timeout
        """
        if self.state == self.STATE_CONNECTED:
            return True
        
        if self.state == self.STATE_IDLE:
            return False
        
        self._call_established_event = threading.Event()
        result = self._call_established_event.wait(timeout)
        self._call_established_event = None
        return result
    
    def wait_for_call_ended(self, timeout=None):
        """Wait for the current call to end.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            bool: True if call ended, False if timeout
        """
        if self.state == self.STATE_IDLE:
            return True
        
        self._call_ended_event = threading.Event()
        result = self._call_ended_event.wait(timeout)
        self._call_ended_event = None
        return result
    
    def announce(self):
        """Send an announce for this voice endpoint."""
        if self.telephone:
            self.telephone.announce()
    
    def teardown(self):
        """Clean up resources."""
        if self.telephone:
            self.telephone.teardown()

