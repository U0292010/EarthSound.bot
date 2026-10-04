from dataclasses import dataclass
from typing import Any

from app.repositories.sqlite import SQLiteRepository


@dataclass(frozen=True)
class AchievementDefinition:
    achievement_key: str
    title: str
    description: str
    statistic: str
    target_count: int


ACHIEVEMENTS = (
    AchievementDefinition(
        "first_sound",
        "First Sound",
        "Generate your first Earth Jukebox audio track.",
        "audios",
        1,
    ),
    AchievementDefinition(
        "earth_explorer",
        "Earth Explorer",
        "Explore data from three different locations.",
        "locations",
        3,
    ),
    AchievementDefinition(
        "data_scientist",
        "Data Scientist",
        "Explore all five Earth data layers.",
        "datasets",
        5,
    ),
    AchievementDefinition(
        "climate_listener",
        "Climate Listener",
        "Listen to Temperature, Sea Level, and Cloud Coverage.",
        "climate_audios",
        3,
    ),
    AchievementDefinition(
        "earth_composer",
        "Earth Composer",
        "Generate five Earth Jukebox audio tracks.",
        "audios",
        5,
    ),
)


class ActivityService:
    def __init__(self, repository: SQLiteRepository) -> None:
        self.repository = repository

    async def initialize(self) -> None:
        await self.repository.initialize()
        await self.repository.seed_achievements(ACHIEVEMENTS)

    async def record_activity(
        self,
        user: Any,
        activity_type: str,
        details: dict[str, Any] | None = None,
    ) -> list[AchievementDefinition]:
        await self.repository.log_activity(user, activity_type, details=details)
        return await self._refresh_achievements(int(user.id))

    async def record_selection(
        self,
        user: Any,
        dataset_key: str,
        location_key: str,
        source: str,
        start_year: int | None = None,
        end_year: int | None = None,
    ) -> list[AchievementDefinition]:
        await self.repository.save_selection(
            user,
            dataset_key,
            location_key,
            source,
            start_year,
            end_year,
        )
        return await self._refresh_achievements(int(user.id))

    async def record_generated_audio(
        self,
        user: Any,
        dataset_key: str,
        location_key: str,
        file_name: str,
        audio_data: bytes,
        source: str,
        start_year: int | None = None,
        end_year: int | None = None,
    ) -> list[AchievementDefinition]:
        await self.repository.save_generated_audio(
            user,
            dataset_key,
            location_key,
            file_name,
            audio_data,
            source,
            start_year,
            end_year,
        )
        return await self._refresh_achievements(int(user.id))

    async def get_achievements(self, telegram_id: int) -> list[Any]:
        return await self.repository.get_achievements(telegram_id)

    async def get_recent_activity(self, telegram_id: int, limit: int = 10) -> list[Any]:
        return await self.repository.get_recent_activity(telegram_id, limit)

    async def _refresh_achievements(
        self,
        telegram_id: int,
    ) -> list[AchievementDefinition]:
        statistics = await self.repository.get_achievement_statistics(telegram_id)
        unlocked = []
        for achievement in ACHIEVEMENTS:
            value = statistics[achievement.statistic]
            progress = min(100, round(value * 100 / achievement.target_count))
            newly_unlocked = await self.repository.update_achievement_progress(
                telegram_id,
                achievement.achievement_key,
                progress,
                value >= achievement.target_count,
            )
            if newly_unlocked:
                unlocked.append(achievement)
        return unlocked


def format_achievement_unlocks(achievements: list[AchievementDefinition]) -> str:
    return "\n".join(f"🏆 {item.title} unlocked! {item.description}" for item in achievements)


def format_achievement_list(rows: list[Any]) -> str:
    lines = []
    for row in rows:
        status = "✅" if row["unlocked_at"] else f"{row['progress']}%"
        lines.append(f"{status} {row['title']} · {row['description']}")
    return "🏆 Achievements\n\n" + "\n".join(lines)


def format_activity_history(rows: list[Any]) -> str:
    if not rows:
        return "No activity recorded yet."

    lines = []
    for row in rows:
        dataset = row["dataset_key"] or "app"
        location = f" / {row['location_key']}" if row["location_key"] else ""
        lines.append(f"{row['created_at']} · {row['activity_type']} · {dataset}{location}")
    return "Recent activity\n\n" + "\n".join(lines)