import sys
from pathlib import Path
from app.application import Application
from core.debug_log import debug_log
from core.single_instance import acquire_single_instance_lock


def main() -> None:
    debug_log(f"app entry path: {Path(__file__).resolve()}")
    debug_log(f"cwd: {Path.cwd()}")
    debug_log(f"frozen/exe mode: {getattr(sys, 'frozen', False)} executable={Path(sys.executable).resolve()}")
    instance_lock = acquire_single_instance_lock()
    if instance_lock is None:
        return
    app = Application(sys.argv)
    app._single_instance_lock = instance_lock
    sys.exit(app.run())


if __name__ == "__main__":
    main()
