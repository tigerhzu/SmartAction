# Importing these modules triggers their @register_form decorators.
# PsFormAction does `import ui.forms` to load the registry before lookup.
from ui.forms import join_domain_form, add_local_user_form  # noqa: F401
