from .constants import (
    HERO_IMAGE_URL,
    LOGO_ICON,
    LOGO_TEXT,
    PROJECT_FULL_NAME,
    PROJECT_NAME,
    WEBSITE_URL,
)


def project_config(request):
    return {
        "PROJECT_NAME": PROJECT_NAME,
        "PROJECT_FULL_NAME": PROJECT_FULL_NAME,
        "LOGO_ICON": LOGO_ICON,
        "LOGO_TEXT": LOGO_TEXT,
        "WEBSITE_URL": WEBSITE_URL,
        "HERO_IMAGE_URL": HERO_IMAGE_URL,
    }
