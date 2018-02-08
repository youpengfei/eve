from eve import ma
from eve.models import Menu, AppVersion


class MenuSchema(ma.ModelSchema):
    class Meta:
        model = Menu
        dateformat = '%Y-%m-%d %H:%M:%S'


menu_schema = MenuSchema()
menu_schemas = MenuSchema(many=True)


class AppVersionSchema(ma.ModelSchema):
    class Meta:
        model = AppVersion
        dateformat = '%Y-%m-%d %H:%M:%S'

app_version_schema = AppVersionSchema()
app_version_schemas = AppVersionSchema(many=True)
