"""TLS trust policy for outbound httpx HTTPS (RSS, OpenAI, Telegram, OG, Hugging Face Hub)."""

from __future__ import annotations

import logging

import httpx

from app.core.config import Settings

logger: logging.Logger = logging.getLogger(__name__)


def httpx_verify_arg(cfg: Settings) -> bool | str:
    """Return httpx ``verify=`` value: path to PEM bundle, True, or False."""
    if not cfg.http_verify_ssl:
        if not getattr(httpx_verify_arg, "_insecure_warned", False):
            logger.warning(
                "Outbound HTTPS TLS verification is disabled (http_verify_ssl=false). "
                "Use only for local debugging."
            )
            setattr(httpx_verify_arg, "_insecure_warned", True)
        return False
    bundle: str = (cfg.http_ca_bundle_path or "").strip()
    return bundle if bundle else True


def configure_huggingface_hub_http(cfg: Settings) -> None:
    """Use the same TLS trust policy for Hugging Face Hub (sentence-transformers downloads).

    ``huggingface_hub`` keeps its own global ``httpx.Client``; it does not read
    ``HTTP_VERIFY_SSL`` unless we install a custom client factory here.
    """
    backend: str = cfg.semantic_embedding_backend.strip().lower()
    if backend not in ("sentence_transformers", "sentence-transformers", "st"):
        return
    from huggingface_hub.utils import set_client_factory
    from huggingface_hub.utils._http import hf_request_event_hook

    verify: bool | str = httpx_verify_arg(cfg)

    def factory() -> httpx.Client:
        return httpx.Client(
            event_hooks={"request": [hf_request_event_hook]},
            follow_redirects=True,
            timeout=None,
            verify=verify,
        )

    set_client_factory(factory)
