import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from main import geo_groups, password_data

# Импорты экстракторов
from extractors.godofwins_extractor import GodofwinsExtractor
from extractors.rolling_extractor import RollingExtractor
from extractors.nfs_extractor import NeedForSpinExtractor 
from extractors.wld_extractor import WildTokyoExtractor
from extractors.hugo_extractor import HugoExtractor
from extractors.winshark_extractor import WinsharkExtractor
from extractors.spinlander_extractor import SpinlanderExtractor
from extractors.slota_extractor import SlotaExtractor
from extractors.spinline_extractor import SpinlineExtractor
from extractors.glitchspin_extractor import GlitchSpinExtractor
from extractors.ritzo_extractor import RitzoExtractor

# Формат: (название проекта, класс, stage_url, prod_url)
PROJECTS = [
    ("Ritzo", RitzoExtractor, "https://stage.ritzo.com", "https://ritzo.com"),
    ("Rolling", RollingExtractor, "https://stage.rollingslots.com", "https://rollingslots.com"),
    ("NeedForSpin", NeedForSpinExtractor, "https://stage.needforspin.com", "https://needforspin.com"),
    ("WildTokyo", WildTokyoExtractor, "https://stage.wildtokyo.com", "https://wildtokyo.com"),
    ("Godofwins", GodofwinsExtractor, "https://stage.godofwins.com", "https://godofwins.com"),
    ("Hugo", HugoExtractor, "https://stage.hugocasino.com", "https://hugocasino.com"),
    ("Winshark", WinsharkExtractor, "https://stage.winshark.com", "https://winshark.com"),
    ("Spinlander", SpinlanderExtractor, "https://stage.spinlander.com", "https://spinlander.com"),
    ("Slota", SlotaExtractor, "https://stage.slota.casino", "https://slota.casino"),
    ("Spinline", SpinlineExtractor, "https://stage.spinline.com", "https://spinline.com"),
    ("GlitchSpin", GlitchSpinExtractor, "https://stage.glitchspin.com", "https://glitchspin.com"),
]

@pytest.mark.parametrize("project_name, extractor_class, stage_url, prod_url", PROJECTS)
@pytest.mark.parametrize("env", ["stage", "prod"])
@pytest.mark.parametrize("geo, login_list", geo_groups.items())
def test_full_extractor(project_name, extractor_class, stage_url, prod_url, env, geo, login_list):
    base_url = stage_url if env == "stage" else prod_url

    for login in login_list:
        extractor = extractor_class(login, password_data, base_url=base_url)

        assert extractor.authenticate(), f"[{project_name}][{env}] Ошибка авторизации: {login}"

        result = extractor.get_payment_and_withdraw_systems(geo)
        assert isinstance(result, tuple) and len(result) == 7, f"[{project_name}][{env}] Неверный формат: {login}"

        deposit, withdraw, dep_names, wd_names, currency, dep_count, recommended = result
        assert isinstance(deposit, list)
        assert isinstance(withdraw, list)
        assert currency is not None
