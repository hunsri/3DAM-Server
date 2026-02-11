import json
from pathlib import Path

ASSETS_PATH = Path("server_assets/")
CATEGORIES_PATH = ASSETS_PATH / "categories"

class _Config:

	_instance = None

    # Singleton pattern to load config only once
	def __new__(cls, path: str | Path | None = None):
		if cls._instance is None:
			cls._instance = super().__new__(cls)
			cls._instance._load(path)
		return cls._instance

	def _load(self, path: str | Path | None = None) -> None:
		base = Path(path) if path else Path.cwd()
		cfg = base / "config.json"
		if not cfg.exists():
			alt = base / "config.json.example"
			cfg = alt if alt.exists() else cfg

		data = {}
		if cfg.exists():
			data = json.loads(cfg.read_text(encoding="utf-8"))

		self.server_name = data.get("server_name")
		self.motd = data.get("motd")
		self.port = data.get("port")
		self.assets_directory = data.get("assets_directory")
		self.max_connections = data.get("max_connections")
		self.categories = tuple(data.get("categories", []))


# instantiate on import (singleton)
_cfg = _Config()

# globally accessible constants
SERVERNAME = _cfg.server_name
SERVER_VERSION = "indev"
MOTD = _cfg.motd
PORT = _cfg.port
ASSETS_DIRECTORY = _cfg.assets_directory or "server_assets"
MAX_CONNECTIONS = _cfg.max_connections
CATEGORIES = _cfg.categories

__all__ = [
	"ASSETS_PATH",
	"CATEGORIES_PATH",
	"SERVERNAME",
	"SERVER_VERSION",
	"MOTD",
	"PORT",
	"ASSETS_DIRECTORY",
	"MAX_CONNECTIONS",
	"CATEGORIES",
]

def _create_category_paths_if_missing() -> None:
	# Create all categories found in CATEGORIES if they don't exist
	if CATEGORIES is None:
		return
	
	ASSETS_PATH.mkdir(parents=True, exist_ok=True)
	CATEGORIES_PATH.mkdir(parents=True, exist_ok=True)
	for category in CATEGORIES:
		(CATEGORIES_PATH / category).mkdir(exist_ok=True)

# creates found category directories on import
_create_category_paths_if_missing()

def get_server_info() -> dict:
	"""Return basic server info as a JSON-serializable dict."""
	return {
		"server_name": SERVERNAME,
		"server_version": SERVER_VERSION,
		"motd": MOTD,
		"categories": list(CATEGORIES) if CATEGORIES is not None else [],
	}

def get_server_info_json(**kwargs) -> str:
	"""Return the server info as a JSON string. Any kwargs are forwarded to json.dumps."""
	return json.dumps(get_server_info(), **kwargs)

__all__.extend([
	"get_server_info",
	"get_server_info_json",
])
