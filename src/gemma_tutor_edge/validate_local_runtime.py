from __future__ import annotations

from .config import Settings


def main() -> int:
    settings = Settings(validate_llama_assets=True, llm_backend="llama_cpp")
    print("Local llama.cpp asset validation passed.")
    print(f"GGUF: {settings.resolved_llama_gguf_path}")
    print(f"MMPROJ: {settings.resolved_llama_mmproj_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
