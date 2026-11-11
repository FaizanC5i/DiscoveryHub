"""
Rate limiting with slowapi.

Analogy: a bouncer counting how many times the same person knocks on the door.
Five wrong passwords in a minute from one client means the bouncer stops
answering for a while. Without this, an attacker can try thousands of passwords
per minute against one account (credential stuffing).

The limiter keys on the client's IP address. Storage is in memory, which is fine
for one development server. With several server processes, switch to a shared
store such as Redis so the counts are not split across processes.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
