from ..database import Database
from ..queries.system import SystemQueries


class SystemController:
    def __init__(self, database: Database):
        self.database = database

    def health(self) -> dict[str, str]:
        with self.database.connect() as connection:
            SystemQueries.check_health(connection)
        return {"status": "ok"}
