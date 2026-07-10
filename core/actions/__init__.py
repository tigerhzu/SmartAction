# Importing each module triggers its @register_action decorator.
# ActionRunner only needs to `import core.actions` to have all types ready.
from core.actions import (  # noqa: F401
    submenu_action,
    url_action,
    command_action,
    powershell_action,
    powershell_library_action,
    environment_check_action,
    client_workspace_action,
    app_action,
    paste_action,
    form_action,
    ps_form_action,
)
