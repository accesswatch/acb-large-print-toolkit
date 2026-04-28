from acb_large_print_web.app import create_app
from acb_large_print_web import feature_flags

app = create_app()
with app.app_context():
    print('Active backend:', feature_flags.get_backend())
    try:
        feature_flags.migrate_json_to_sqlite()
        print('Migration completed (if JSON data present).')
    except Exception as e:
        print('Migration failed:', e)
