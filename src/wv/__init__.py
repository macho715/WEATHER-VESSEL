"""웨더 베슬 패키지. Weather Vessel package."""

from importlib import metadata


def get_version() -> str:
    """패키지 버전 조회. Return package version."""

    try:
        return metadata.version("weather-vessel")
    except metadata.PackageNotFoundError:
        return "0.0.0"


__all__ = ["get_version"]
