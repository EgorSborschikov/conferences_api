from pydantic_settings import BaseSettings
import os
from supabase import create_client, Client

class Settings(BaseSettings):
    url: str = os.environ.get("https://ivnawbetsjveqvdazara.supabase.co")
    key: str = os.environ.get("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml2bmF3YmV0c2p2ZXF2ZGF6YXJhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDEyNjUwMDIsImV4cCI6MjA1Njg0MTAwMn0.9TfaJa_vtO4oxaWwp7c0svpKcplDhBv8OoE7nA8fpIE")
    supabase: Client = create_client(url, key)

settings = Settings()