# Proposed Desktop PC Software Folder

I propose grouping all desktop/PC Python scripts into `pc_software/desktop/` for clearer organization. This avoids cluttering the repository root and separates firmware, mobile, and PC code.

Suggested files to move (currently at project root):

- advanced_multimeter.py
- app.py
- image_processor.py
- multimeter_app.py
- multimeter_analyzer.py
- multimeter_controller.py
- multimeter_gui.py
- multimeter_gui_new.py
- multimeter_software.py
- multimeter.py
- settings.py
- logger.py
- keithley_2400.py
- specfication_extractor.py
- power_calculator.py
- test_multimeter.py
- main.py
- ini.py

Proposed action (safe, git-aware):

- Use `git mv` to move each file into `pc_software/desktop/` so history is preserved.
- Update any imports that referenced top-level modules to `pc_software.desktop.<module>` if needed.

Do you want me to perform the `git mv` operations and update imports now? Reply `yes` and I'll proceed with the moves and make the necessary import updates and small wrapper modules if needed.