"""Common data models for stat cards."""

from datetime import datetime

from pydantic import BaseModel, Field


class PlayerStats(BaseModel):
    """Common format for all game stats.

    This is the contract every provider must fulfill.
    The renderer never knows where the data came from.
    """

    # Identity
    game: str = Field(..., description="Game key (valorant, cs2_faceit, cs2_premier)")
    player_name: str = Field(..., description="Display name of the player")
    player_id: str = Field(..., description="Unique ID (Riot ID, FACEIT nick, SteamID)")

    # Rank and level
    current_rank: str | None = Field(None, description="Current rank/tier name")
    peak_rank: str | None = Field(None, description="Highest rank achieved")
    level: int | None = Field(None, description="Account level or numeric rating")

    # General stats
    total_matches: int = Field(0, description="Total matches played")
    wins: int = Field(0, description="Total wins")
    win_rate: float = Field(0.0, description="Win rate percentage (0-100)")

    # K/D
    kills: int = Field(0, description="Total kills")
    deaths: int = Field(0, description="Total deaths")
    kd_ratio: float = Field(0.0, description="Kill/Death ratio")

    # Recent matches (simplified)
    recent_matches: list[dict] = Field(
        default_factory=list,
        description="Last 5-10 matches with basic info",
    )

    # Metadata
    last_updated: datetime = Field(
        default_factory=datetime.now,
        description="When these stats were fetched",
    )

    def get_win_rate_display(self) -> str:
        """Formatted win rate for display."""
        return f"{self.win_rate:.1f}%"

    def get_kd_display(self) -> str:
        """Formatted K/D for display."""
        return f"{self.kd_ratio:.2f}"