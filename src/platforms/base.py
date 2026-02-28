"""Base class for all platform uploaders."""


class BasePlatformUploader:
    name = "base"

    def create_product(
        self,
        title: str,
        description: str,
        price_usd: float,
        pdf_path: str,
        cover_path: str | None = None,
        tags: list[str] | None = None,
    ) -> dict:
        """
        Upload a digital product to the platform.
        Returns: {"url": "product_url", "product_id": "...", "platform": self.name}
        """
        raise NotImplementedError
