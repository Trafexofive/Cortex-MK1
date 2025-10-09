"""
==============================================================================
NETWORK MANAGER - Docker Network Management
==============================================================================
Manages Docker networks for session isolation.
==============================================================================
"""

import docker
from typing import Optional, Dict
from loguru import logger


class NetworkManager:
    """Manages Docker networks for session isolation."""
    
    def __init__(self):
        self.client = docker.from_env()
        self.session_networks: Dict[str, str] = {}  # session_id -> network_id
        logger.info("🌐 Network manager initialized")
    
    def create_session_network(self, session_id: str) -> str:
        """Create a private network for a session."""
        network_name = f"session_{session_id}"
        
        try:
            # Check if network already exists
            if session_id in self.session_networks:
                return self.session_networks[session_id]
            
            # Create network
            network = self.client.networks.create(
                name=network_name,
                driver="bridge",
                internal=False,  # Allow external access (for pulling images, etc.)
                labels={
                    "cortex.session_id": session_id,
                    "cortex.managed": "true"
                }
            )
            
            self.session_networks[session_id] = network.id
            logger.info(f"🌐 Created private network: {network_name} ({network.short_id})")
            
            return network.id
            
        except docker.errors.APIError as e:
            logger.error(f"Failed to create network for session {session_id}: {e}")
            raise
    
    def get_session_network(self, session_id: str) -> Optional[str]:
        """Get network ID for a session."""
        return self.session_networks.get(session_id)
    
    def remove_session_network(self, session_id: str) -> bool:
        """Remove a session's private network."""
        network_id = self.session_networks.get(session_id)
        if not network_id:
            return False
        
        try:
            network = self.client.networks.get(network_id)
            network.remove()
            
            del self.session_networks[session_id]
            logger.info(f"🗑️  Removed network for session: {session_id}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to remove network for session {session_id}: {e}")
            return False
    
    def cleanup_all_session_networks(self) -> int:
        """Cleanup all managed session networks."""
        removed = 0
        
        try:
            # Find all networks with our label
            networks = self.client.networks.list(filters={"label": "cortex.managed=true"})
            
            for network in networks:
                try:
                    network.remove()
                    removed += 1
                    logger.info(f"Removed network: {network.name}")
                except Exception as e:
                    logger.warning(f"Failed to remove network {network.name}: {e}")
            
            # Clear tracking
            self.session_networks.clear()
            
        except Exception as e:
            logger.error(f"Failed to cleanup networks: {e}")
        
        return removed
