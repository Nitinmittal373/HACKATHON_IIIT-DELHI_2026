import os
import tempfile

# Tests never touch the real database or the real TinyFish key
os.environ["DATABASE_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ.setdefault("TINYFISH_API_KEY", "test-key")
os.environ["RATE_LIMIT_PER_MINUTE"] = "100"
