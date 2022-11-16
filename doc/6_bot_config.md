# Bot Config

```json
{
    "bot": {
        ...
    },
    "telegram_api": {
        ...
    },
    "db_connection": {
        ...
    },
    "debug": {
        ...
    },
    "data_files": {
        ...
    },
    "phrase_files": {
        ...
    },
    "achievement_file": "./data/achievements/achievement_info.json",
    "update_database_schema": false,
    "delete_data_and_recreate_database_schema": false,
    "database_schema": "prod"
}
```

Debug overwrites some in game definitions, so that the game can be played faster through for development purposes.
if `is_active` is set to true, the debug mode will be used. Tasks only take one iteration instead of three (vocab guessing and sentence correction) and the discussion tasks takes less time. In the future more fine grained options could be implemented. E.g. explicitly defining the number of iterations `"iteration": 2"`.

```json
    "debug": {
        "is_active": true,
    },
```
