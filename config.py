import json
from pathlib import Path

ASSETS_PATH = Path("server_assets/")
CATEGORIES_PATH = ASSETS_PATH / "categories"

class _Config:
	"""
	Configuration management for the asset server.
	Loads settings from config.json on first import and provides constants and helper functions for accessing them.
	The class is set up as a singleton to ensure the config is only loaded once, and the constants are globally accessible.
	"""

	_instance = None ## holds the singleton instance of _Config

    # Singleton pattern to load config only once
	def __new__(cls, path: str | Path | None = None):
		if cls._instance is None:
			cls._instance = super().__new__(cls)
			cls._instance._load(path)
		return cls._instance

	def _load(self, path: str | Path | None = None) -> None:
		"""
		Load configuration data from disk and populate attributes.

		This will prefer `config.json` in the provided `path` (or the
		current working directory). If `config.json` is missing but
		`config.json.example` exists, that file is used. If neither exists,
		no file is read and defaults are left as None/empty.
		"""
		base = Path(path) if path else Path.cwd()
		cfg_path = base / "config.json"
		example_path = base / "config.json.example"

		# Choose which config file to use (prefer `config.json`). If
		# neither file exists, leave `cfg` as None and skip loading.
		if cfg_path.exists():
			cfg = cfg_path
		elif example_path.exists():
			cfg = example_path
		else:
			cfg = None

		data = {}
		if cfg is not None and cfg.exists():
			data = json.loads(cfg.read_text(encoding="utf-8"))

		self.server_name = data.get("server_name")
		self.motd = data.get("motd")
		self.assets_directory = data.get("assets_directory")
		self.categories = tuple(data.get("categories", []))


# instantiate on import (singleton)
_cfg = _Config()

# globally accessible constants
SERVERNAME = _cfg.server_name # name of the server
SERVER_VERSION = "indev 0.1"  # version string of the server, can be updated as needed
MOTD = _cfg.motd			  # message of the day, for further info about the server
ASSETS_DIRECTORY = _cfg.assets_directory or "server_assets" # base directory for assets
CATEGORIES = _cfg.categories  # tuple of category names, loaded from config.json

__all__ = [
	"ASSETS_PATH",
	"CATEGORIES_PATH",
	"SERVERNAME",
	"SERVER_VERSION",
	"MOTD",
	"ASSETS_DIRECTORY",
	"CATEGORIES",
]

def _create_category_paths_if_missing() -> None:
	"""
	Creates the necessary directory structure for the asset server if it doesn't already exist.
	"""

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
