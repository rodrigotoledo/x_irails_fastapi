import gettext
from pathlib import Path

import irails
import irails._i18n as irails_i18n
from irails import database as irails_database
from fastapi.staticfiles import StaticFiles


for language, translator in irails_i18n.trans_dic.items():
    if translator is None:
        irails_i18n.trans_dic[language] = gettext.NullTranslations()


_original_check_migration = irails_database.check_migration


def _check_migration_with_real_url(engine, uri, alembic_ini, upgrade=None):
    if hasattr(engine, "url"):
        uri = engine.url.render_as_string(hide_password=False)
    return _original_check_migration(engine, uri, alembic_ini, upgrade)


irails_database.check_migration = _check_migration_with_real_url

if __name__=='__main__': 
    
    irails.core.run_server()
    
else:
    #for vercel like deploy
    app = irails.core.generate_mvc_app()
    (Path(__file__).resolve().parent / "uploads").mkdir(exist_ok=True)
    app.mount(
        "/uploads",
        StaticFiles(directory=Path(__file__).resolve().parent / "uploads"),
        name="uploads",
    )
